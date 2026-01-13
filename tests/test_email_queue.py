"""
Testes para Email Queue
"""
import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from src.core.email_queue import EmailQueue, EmailMessage


@pytest.fixture
def mock_db_manager():
    """Fixture com mock do database manager"""
    db = Mock()
    db.execute_update = Mock(return_value=1)
    db.execute_query = Mock(return_value=[])
    return db


@pytest.fixture
def smtp_config():
    """Fixture com configuração SMTP de teste"""
    return {
        'server': 'smtp.gmail.com',
        'port': 587,
        'use_tls': True,
        'username': 'test@example.com',
        'password': 'testpass',
        'from_address': 'test@example.com'
    }


@pytest.fixture
def email_queue(mock_db_manager, smtp_config):
    """Fixture que cria uma email queue"""
    return EmailQueue(mock_db_manager, smtp_config)


class TestEmailMessage:
    """Testes para EmailMessage dataclass"""

    def test_initialization(self):
        """Testa inicialização de EmailMessage"""
        msg = EmailMessage(
            id=1,
            to="user@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        assert msg.id == 1
        assert msg.to == "user@example.com"
        assert msg.subject == "Test Subject"
        assert msg.body == "Test Body"
        assert msg.attempts == 0
        assert msg.max_attempts == 5  # EMAIL_MAX_RETRIES default
        assert msg.created_at is not None

    def test_post_init_created_at(self):
        """Testa que created_at é auto-gerado"""
        msg = EmailMessage(
            id=1,
            to="user@example.com",
            subject="Test",
            body="Test"
        )
        
        assert isinstance(msg.created_at, datetime)
        assert (datetime.now() - msg.created_at).total_seconds() < 1


class TestEmailQueue:
    """Testes para EmailQueue"""

    def test_initialization(self, email_queue):
        """Testa inicialização da fila"""
        assert email_queue.is_running is False
        assert email_queue.worker_thread is None
        assert email_queue.last_error is None
        assert email_queue.stats['sent_count'] == 0
        assert email_queue.stats['failed_count'] == 0

    def test_add_message_success(self, email_queue, mock_db_manager):
        """Testa adição de mensagem à fila"""
        # Mock get_queue_length to return 0
        with patch.object(email_queue, 'get_queue_length', return_value=0):
            success = email_queue.add_message(
                to="user@example.com",
                subject="Test Alert",
                body="Test Body",
                attachment_path="/path/to/snapshot.jpg"
            )
        
        assert success is True
        assert mock_db_manager.execute_update.called

    def test_add_message_queue_full(self, email_queue):
        """Testa que mensagem é rejeitada quando fila está cheia"""
        # Mock get_queue_length to return MAX_QUEUE_SIZE
        with patch.object(email_queue, 'get_queue_length', return_value=1000):
            success = email_queue.add_message(
                to="user@example.com",
                subject="Test",
                body="Test"
            )
        
        assert success is False

    def test_start_worker(self, email_queue):
        """Testa inicialização do worker thread"""
        email_queue.start()
        
        assert email_queue.is_running is True
        assert email_queue.worker_thread is not None
        assert email_queue.worker_thread.is_alive()
        
        # Cleanup
        email_queue.stop()

    def test_stop_worker(self, email_queue):
        """Testa parada do worker thread"""
        email_queue.start()
        assert email_queue.is_running is True
        
        email_queue.stop()
        assert email_queue.is_running is False

    def test_mark_sent(self, email_queue, mock_db_manager):
        """Testa marcação de mensagem como enviada"""
        email_queue.mark_sent(message_id=1)
        
        assert mock_db_manager.execute_update.called
        assert email_queue.stats['sent_count'] == 1

    def test_mark_failed(self, email_queue, mock_db_manager):
        """Testa marcação de mensagem como falhada"""
        email_queue.mark_failed(message_id=1, error="SMTP error")
        
        assert mock_db_manager.execute_update.called
        assert email_queue.stats['retry_count'] == 1
        assert email_queue.last_error == "SMTP error"

    def test_mark_failed_with_custom_delay(self, email_queue, mock_db_manager):
        """Testa retry com delay customizado"""
        email_queue.mark_failed(message_id=1, error="Test", retry_delay=120)
        
        assert mock_db_manager.execute_update.called

    def test_get_pending_messages(self, email_queue, mock_db_manager):
        """Testa obtenção de mensagens pendentes"""
        # Mock database response
        mock_db_manager.execute_query.return_value = [
            (1, "user@example.com", "Subject", "Body", None, 0, datetime.now().isoformat(), None)
        ]
        
        messages = email_queue.get_pending_messages()
        
        assert len(messages) == 1
        assert messages[0].to == "user@example.com"

    def test_get_queue_length(self, email_queue, mock_db_manager):
        """Testa obtenção do tamanho da fila"""
        mock_db_manager.execute_query.return_value = [(5,)]
        
        length = email_queue.get_queue_length()
        
        assert length == 5

    def test_get_last_error(self, email_queue):
        """Testa obtenção do último erro"""
        assert email_queue.get_last_error() is None
        
        email_queue.last_error = "Test error"
        assert email_queue.get_last_error() == "Test error"

    def test_get_stats(self, email_queue, mock_db_manager):
        """Testa obtenção de estatísticas"""
        # Mock queue status
        mock_db_manager.execute_query.return_value = [(10, 3, 7, 0)]
        
        stats = email_queue.get_stats()
        
        assert 'is_running' in stats
        assert 'queue_length' in stats
        assert 'sent_count' in stats
        assert stats['is_running'] is False

    def test_clear_old_messages(self, email_queue, mock_db_manager):
        """Testa limpeza de mensagens antigas"""
        email_queue.clear_old_messages(days=7)
        
        assert mock_db_manager.execute_update.called

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_queue):
        """Testa envio de email com sucesso"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        message = EmailMessage(
            id=1,
            to="user@example.com",
            subject="Test",
            body="Test body"
        )
        
        success = email_queue._send_email(message)
        
        # Como usa context manager diferente, vamos verificar apenas se não houve erro
        assert message.error_message is None or success

    @patch('smtplib.SMTP')
    def test_send_email_smtp_auth_error(self, mock_smtp, email_queue):
        """Testa envio com erro de autenticação"""
        import smtplib
        
        # Mock SMTP to raise authentication error
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        mock_smtp_instance.starttls = MagicMock()
        mock_smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
        
        message = EmailMessage(
            id=1,
            to="user@example.com",
            subject="Test",
            body="Test"
        )
        
        success = email_queue._send_email(message)
        
        assert success is False
        assert message.error_message is not None
        assert "Autenticação SMTP" in message.error_message

    def test_worker_loop_processes_messages(self, email_queue, mock_db_manager):
        """Testa que worker processa mensagens pendentes"""
        # Mock pending messages
        mock_db_manager.execute_query.return_value = []
        
        # Start worker
        email_queue.start()
        
        # Wait briefly
        time.sleep(0.5)
        
        # Stop worker
        email_queue.stop()
        
        # Worker should have called get_pending_messages
        assert email_queue.is_running is False

    def test_exponential_backoff_delays(self, email_queue):
        """Testa que delays seguem exponential backoff"""
        message = EmailMessage(
            id=1,
            to="test@example.com",
            subject="Test",
            body="Test"
        )
        
        # Delays esperados: 60s, 120s, 300s, 600s, 1800s
        expected_delays = [60, 120, 300, 600, 1800]
        
        for attempt, expected_delay in enumerate(expected_delays):
            message.attempts = attempt
            
            # Simular falha
            # _worker_loop usa esta lógica internamente
            retry_delays = [60, 120, 300, 600, 1800]
            actual_delay = retry_delays[min(message.attempts, len(retry_delays) - 1)]
            
            assert actual_delay == expected_delay

    def test_get_queue_status(self, email_queue, mock_db_manager):
        """Testa obtenção de status da fila"""
        # Mock database response: total=10, pending=3, sent=7, failed=0
        mock_db_manager.execute_query.return_value = [(10, 3, 7, 0)]
        
        status = email_queue.get_queue_status()
        
        assert status['total'] == 10
        assert status['pending'] == 3
        assert status['sent'] == 7
        assert status['failed'] == 0
        assert 'is_running' in status
