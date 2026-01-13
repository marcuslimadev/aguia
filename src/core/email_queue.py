"""
Fila de email com retry automático e persistência
"""
import logging
import threading
import time
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config.config import (
    EMAIL_RETRY_DELAY,
    EMAIL_MAX_RETRIES,
    EMAIL_WORKER_INTERVAL,
    EMAIL_CLEANUP_DAYS,
    MAX_QUEUE_SIZE
)

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Mensagem de email na fila"""
    id: int
    to: str
    subject: str
    body: str
    attachment_path: Optional[str] = None
    attempts: int = 0
    max_attempts: int = EMAIL_MAX_RETRIES
    next_retry_at: Optional[datetime] = None
    created_at: datetime = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class EmailQueue:
    """Fila de email com persistência em banco de dados e retry automático"""

    def __init__(self, db_manager, smtp_config: dict):
        """
        Inicializa fila de email

        Args:
            db_manager: Gerenciador de banco de dados
            smtp_config: Configuração SMTP
        """
        self.db = db_manager
        self.smtp_config = smtp_config
        self.queue: List[EmailMessage] = []
        self.lock = threading.Lock()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.last_error: Optional[str] = None
        self.stats = {
            'sent_count': 0,
            'failed_count': 0,
            'retry_count': 0
        }

    def start(self):
        """Inicia worker de fila"""
        if self.is_running:
            logger.warning("Worker de fila já está rodando")
            return

        self.is_running = True
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="EmailQueueWorker"
        )
        self.worker_thread.start()

        logger.info("Worker de fila de email iniciado")

    def stop(self):
        """Para worker de fila"""
        self.is_running = False

        if self.worker_thread:
            self.worker_thread.join(timeout=5)

        logger.info("Worker de fila de email parado")

    def add_message(
        self,
        to: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None
    ) -> bool:
        """
        Adiciona mensagem à fila

        Args:
            to: Email destinatário
            subject: Assunto
            body: Corpo da mensagem
            attachment_path: Caminho do anexo (opcional)

        Returns:
            True se adicionado com sucesso
        """
        try:
            # Verificar tamanho da fila
            queue_size = self.get_queue_length()
            if queue_size >= MAX_QUEUE_SIZE:
                logger.warning(f"Fila de email cheia ({queue_size}/{MAX_QUEUE_SIZE}), descartando mensagem")
                return False
            
            with self.lock:
                message = EmailMessage(
                    id=None,
                    to=to,
                    subject=subject,
                    body=body,
                    attachment_path=attachment_path
                )

                # Salvar no banco de dados
                query = """
                    INSERT INTO email_queue 
                    (to, subject, body, attachment_path, attempts, next_retry_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """

                self.db.execute_update(
                    query,
                    (
                        to, subject, body, attachment_path,
                        0, datetime.now().isoformat(), datetime.now().isoformat()
                    )
                )

                logger.info(f"Email adicionado à fila: {to} - {subject}")
                return True

        except Exception as e:
            logger.error(f"Erro ao adicionar email à fila: {e}")
            self.last_error = str(e)
            return False

    def get_pending_messages(self) -> List[EmailMessage]:
        """Obtém mensagens pendentes para envio"""
        try:
            query = """
                SELECT id, to, subject, body, attachment_path, attempts, 
                       created_at, error_message
                FROM email_queue
                WHERE sent_at IS NULL
                AND (next_retry_at IS NULL OR next_retry_at <= ?)
                AND attempts < ?
                ORDER BY created_at ASC
                LIMIT 10
            """

            results = self.db.execute_query(
                query,
                (datetime.now().isoformat(), EMAIL_MAX_RETRIES)
            )

            messages = []
            for row in results:
                message = EmailMessage(
                    id=row[0],
                    to=row[1],
                    subject=row[2],
                    body=row[3],
                    attachment_path=row[4],
                    attempts=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                    error_message=row[7]
                )
                messages.append(message)

            return messages

        except Exception as e:
            logger.error(f"Erro ao obter mensagens pendentes: {e}")
            self.last_error = str(e)
            return []

    def mark_sent(self, message_id: int):
        """Marca mensagem como enviada"""
        try:
            query = "UPDATE email_queue SET sent_at = ? WHERE id = ?"
            self.db.execute_update(query, (datetime.now().isoformat(), message_id))

            with self.lock:
                self.stats['sent_count'] += 1

            logger.info(f"Email {message_id} marcado como enviado")

        except Exception as e:
            logger.error(f"Erro ao marcar email como enviado: {e}")
            self.last_error = str(e)

    def mark_failed(self, message_id: int, error: str, retry_delay: int = None):
        """Marca mensagem como falhada e agenda retry"""
        try:
            if retry_delay is None:
                retry_delay = EMAIL_RETRY_DELAY
            
            next_retry = datetime.now() + timedelta(seconds=retry_delay)

            query = """
                UPDATE email_queue 
                SET attempts = attempts + 1, 
                    next_retry_at = ?,
                    error_message = ?
                WHERE id = ?
            """

            self.db.execute_update(
                query,
                (next_retry.isoformat(), error, message_id)
            )

            with self.lock:
                self.stats['retry_count'] += 1
                self.last_error = error

            logger.warning(f"Email {message_id} falhou: {error}. Retry em {retry_delay}s")

        except Exception as e:
            logger.error(f"Erro ao marcar email como falhado: {e}")
            self.last_error = str(e)

    def _worker_loop(self):
        """Loop principal do worker"""
        while self.is_running:
            try:
                messages = self.get_pending_messages()

                for message in messages:
                    if not self.is_running:
                        break

                    success = self._send_email(message)

                    if success:
                        self.mark_sent(message.id)
                    else:
                        # Exponential backoff: 60s, 120s, 300s, 600s, 1800s
                        retry_delays = [60, 120, 300, 600, 1800]
                        delay = retry_delays[min(message.attempts, len(retry_delays) - 1)]
                        self.mark_failed(message.id, message.error_message or "Unknown error", delay)
                        
                        with self.lock:
                            self.stats['failed_count'] += 1

                # Aguardar antes de próxima verificação
                time.sleep(EMAIL_WORKER_INTERVAL)

            except Exception as e:
                logger.error(f"Erro no worker de fila: {e}")
                self.last_error = str(e)
                time.sleep(EMAIL_WORKER_INTERVAL)

    def _send_email(self, message: EmailMessage) -> bool:
        """Envia email"""
        try:
            # Conectar ao servidor SMTP
            if self.smtp_config.get('use_tls'):
                server = smtplib.SMTP(
                    self.smtp_config['server'],
                    self.smtp_config.get('port', 587)
                )
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(
                    self.smtp_config['server'],
                    self.smtp_config.get('port', 465)
                )

            # Autenticar
            server.login(
                self.smtp_config['username'],
                self.smtp_config['password']
            )

            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_address']
            msg['To'] = message.to
            msg['Subject'] = message.subject

            msg.attach(MIMEText(message.body, 'html'))

            # Adicionar anexo se existir
            if message.attachment_path:
                attachment_path = Path(message.attachment_path)
                if attachment_path.exists():
                    with open(attachment_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())

                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment_path.name}'
                    )
                    msg.attach(part)

            # Enviar
            server.send_message(msg)
            server.quit()

            logger.info(f"Email enviado para {message.to}: {message.subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            message.error_message = f"Autenticação SMTP falhou: {str(e)}"
            logger.error(message.error_message)
            return False

        except smtplib.SMTPException as e:
            message.error_message = f"Erro SMTP: {str(e)}"
            logger.error(message.error_message)
            return False

        except Exception as e:
            message.error_message = f"Erro ao enviar email: {str(e)}"
            logger.error(message.error_message)
            return False

    def get_queue_status(self) -> dict:
        """Retorna status da fila"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN sent_at IS NULL THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN sent_at IS NOT NULL THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN attempts >= ? THEN 1 ELSE 0 END) as failed
                FROM email_queue
            """

            result = self.db.execute_query(query, (5,))

            if result:
                row = result[0]
                return {
                    'total': row[0] or 0,
                    'pending': row[1] or 0,
                    'sent': row[2] or 0,
                    'failed': row[3] or 0,
                    'is_running': self.is_running
                }

            return {
                'total': 0,
                'pending': 0,
                'sent': 0,
                'failed': 0,
                'is_running': self.is_running
            }

        except Exception as e:
            logger.error(f"Erro ao obter status da fila: {e}")
            return {'error': str(e)}

    def clear_old_messages(self, days: int = None):
        """Remove mensagens antigas"""
        try:
            if days is None:
                days = EMAIL_CLEANUP_DAYS
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = "DELETE FROM email_queue WHERE created_at < ?"
            self.db.execute_update(query, (cutoff_date,))

            logger.info(f"Mensagens antigas removidas (> {days} dias)")

        except Exception as e:
            logger.error(f"Erro ao limpar mensagens antigas: {e}")
            self.last_error = str(e)

    def get_queue_length(self) -> int:
        """Retorna tamanho atual da fila (mensagens pendentes)"""
        try:
            query = "SELECT COUNT(*) FROM email_queue WHERE sent_at IS NULL"
            result = self.db.execute_query(query)
            return result[0][0] if result else 0
        except Exception as e:
            logger.error(f"Erro ao obter tamanho da fila: {e}")
            return 0

    def get_last_error(self) -> Optional[str]:
        """Retorna último erro ocorrido"""
        return self.last_error

    def get_stats(self) -> Dict:
        """Retorna estatísticas detalhadas da fila"""
        try:
            status = self.get_queue_status()
            
            return {
                'is_running': self.is_running,
                'queue_length': status.get('pending', 0),
                'total_messages': status.get('total', 0),
                'sent_messages': status.get('sent', 0),
                'failed_messages': status.get('failed', 0),
                'sent_count': self.stats['sent_count'],
                'retry_count': self.stats['retry_count'],
                'failed_count': self.stats['failed_count'],
                'last_error': self.last_error
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}
