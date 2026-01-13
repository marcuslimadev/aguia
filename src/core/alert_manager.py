"""
Gerenciador de alertas e notificações por email
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
import threading

from config.ui_theme import PALETTE, color_for_severity

logger = logging.getLogger(__name__)


class AlertRule:
    """Define uma regra de alerta"""

    def __init__(self, rule_id: int, event_type: str, zone_id: int, enabled: bool = True):
        self.rule_id = rule_id
        self.event_type = event_type
        self.zone_id = zone_id
        self.enabled = enabled
        self.last_alert_time = None
        self.cooldown_seconds = 30

    def can_trigger(self) -> bool:
        """Verifica se a regra pode disparar um alerta"""
        if not self.enabled:
            return False

        if self.last_alert_time is None:
            return True

        elapsed = (datetime.now() - self.last_alert_time).total_seconds()
        return elapsed >= self.cooldown_seconds

    def trigger(self):
        """Marca que a regra foi disparada"""
        self.last_alert_time = datetime.now()


class Alert:
    """Representa um alerta"""

    def __init__(self, alert_id: int, rule_id: int, camera_id: int, event_type: str,
                 severity: str, description: str = "", snapshot_path: str = None):
        self.alert_id = alert_id
        self.rule_id = rule_id
        self.camera_id = camera_id
        self.event_type = event_type
        self.severity = severity
        self.description = description
        self.snapshot_path = snapshot_path
        self.timestamp = datetime.now()
        self.acknowledged = False

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id': self.alert_id,
            'rule_id': self.rule_id,
            'camera_id': self.camera_id,
            'event_type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'snapshot_path': self.snapshot_path,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged
        }


class EmailNotifier:
    """Envia notificações por email"""

    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str,
                 sender_password: str, recipient_emails: List[str]):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_emails = recipient_emails
        self.retry_count = 3

    def send_alert_email(self, alert: Alert, snapshot_path: Optional[Path] = None) -> bool:
        """Envia email de alerta"""
        try:
            msg = MIMEMultipart('related')
            msg['Subject'] = f"[{alert.severity.upper()}] {alert.event_type} - {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_emails)

            # Corpo do email
            body = self._create_email_body(alert)
            msg.attach(MIMEText(body, 'html'))

            # Adicionar snapshot se disponível
            if snapshot_path and Path(snapshot_path).exists():
                self._attach_image(msg, snapshot_path)

            # Enviar email
            self._send_smtp(msg)
            logger.info(f"Email de alerta enviado para {self.recipient_emails}")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar email de alerta: {e}")
            return False

    def _create_email_body(self, alert: Alert) -> str:
        """Cria o corpo do email em HTML"""
        severity_color = color_for_severity(alert.severity)
        content_bg = PALETTE["surface_alt"]
        footer_bg = PALETTE["sidebar"]
        footer_text = PALETTE["accent_text"]

        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .header {{ background-color: {severity_color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: {content_bg}; padding: 20px; }}
                    .footer {{ background-color: {footer_bg}; color: {footer_text}; padding: 10px; text-align: center; font-size: 12px; }}
                    .detail {{ margin: 10px 0; }}
                    .label {{ font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>🚨 Security Alert</h2>
                    </div>
                    <div class="content">
                        <div class="detail">
                            <span class="label">Event Type:</span> {alert.event_type}
                        </div>
                        <div class="detail">
                            <span class="label">Severity:</span> {alert.severity.upper()}
                        </div>
                        <div class="detail">
                            <span class="label">Timestamp:</span> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                        </div>
                        <div class="detail">
                            <span class="label">Description:</span> {alert.description}
                        </div>
                        <div class="detail">
                            <span class="label">Camera ID:</span> {alert.camera_id}
                        </div>
                    </div>
                    <div class="footer">
                        <p>Edge Property Security AI - Automated Alert System</p>
                    </div>
                </div>
            </body>
        </html>
        """
        return html

    def _attach_image(self, msg: MIMEMultipart, image_path: str):
        """Anexa uma imagem ao email"""
        try:
            with open(image_path, 'rb') as attachment:
                image_data = attachment.read()
                image = MIMEImage(image_data)
                image.add_header('Content-ID', '<snapshot>')
                image.add_header('Content-Disposition', 'attachment', filename='snapshot.jpg')
                msg.attach(image)
            logger.info(f"Snapshot anexado ao email: {image_path}")
        except Exception as e:
            logger.warning(f"Erro ao anexar snapshot: {e}")

    def _send_smtp(self, msg: MIMEMultipart):
        """Envia email via SMTP"""
        for attempt in range(self.retry_count):
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
                return
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} de envio falhou: {e}")
                if attempt == self.retry_count - 1:
                    raise


class AlertManager:
    """Gerencia alertas e regras com validação de eventos e fila de email"""

    def __init__(self, db_manager, validator_model=None, email_queue=None):
        self.db = db_manager
        self.validator = validator_model
        self.email_queue = email_queue  # EmailQueue instance
        self.rules: dict = {}
        self.active_alerts: List[Alert] = []
        self.email_notifier: Optional[EmailNotifier] = None
        self.lock = threading.Lock()

    def load_rules(self, camera_id: int):
        """Carrega regras do banco de dados"""
        try:
            camera = self.db.get_camera(camera_id)
            if not camera:
                return

            # Aqui você carregaria as regras do banco de dados
            # Por enquanto, vamos criar regras padrão
            logger.info(f"Regras carregadas para câmera {camera_id}")
        except Exception as e:
            logger.error(f"Erro ao carregar regras: {e}")

    def setup_email_notifier(self, user_id: int) -> bool:
        """Configura o notificador de email"""
        try:
            email_settings = self.db.get_email_settings(user_id)
            if not email_settings:
                logger.debug("Email not configured - alerts will be shown in UI only")
                return False

            recipient_emails = email_settings['recipient_emails'].split(',')
            self.email_notifier = EmailNotifier(
                smtp_server=email_settings['smtp_server'],
                smtp_port=email_settings['smtp_port'],
                sender_email=email_settings['sender_email'],
                sender_password=email_settings['sender_password'],
                recipient_emails=recipient_emails
            )
            logger.info("Notificador de email configurado")
            return True
        except Exception as e:
            logger.error(f"Erro ao configurar notificador de email: {e}")
            return False

    def create_alert(self, rule_id: int, camera_id: int, event_type: str,
                     severity: str, description: str = "", snapshot_path: str = None) -> Optional[Alert]:
        """Cria um novo alerta e envia via fila de email"""
        try:
            alert_id = self.db.add_alert(rule_id, camera_id, event_type, severity, description, snapshot_path)
            alert = Alert(alert_id, rule_id, camera_id, event_type, severity, description, snapshot_path)

            with self.lock:
                self.active_alerts.append(alert)

            # Enviar notificação por email via fila (não bloqueia)
            if self.email_queue and self.email_notifier:
                self._queue_alert_email(alert, snapshot_path)
            elif self.email_notifier:
                # Fallback para envio direto se email_queue não configurado
                threading.Thread(
                    target=self.email_notifier.send_alert_email,
                    args=(alert, snapshot_path),
                    daemon=True
                ).start()

            logger.info(f"Alerta criado: {event_type} - {severity}")
            return alert
        except Exception as e:
            logger.error(f"Erro ao criar alerta: {e}")
            return None

    def _queue_alert_email(self, alert: Alert, snapshot_path: Optional[str] = None):
        """Adiciona email de alerta à fila (não bloqueia)"""
        try:
            if not self.email_notifier:
                logger.warning("Email notifier não configurado")
                return
            
            # Criar corpo do email
            body = self.email_notifier._create_email_body(alert)
            
            # Criar assunto
            subject = f"[{alert.severity.upper()}] {alert.event_type} - {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Adicionar à fila
            for recipient in self.email_notifier.recipient_emails:
                self.email_queue.add_message(
                    to=recipient,
                    subject=subject,
                    body=body,
                    attachment_path=snapshot_path
                )
            
            logger.info(f"Email de alerta adicionado à fila para {len(self.email_notifier.recipient_emails)} destinatários")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar email à fila: {e}")

    def acknowledge_alert(self, alert_id: int):
        """Marca um alerta como reconhecido"""
        try:
            self.db.acknowledge_alert(alert_id)
            with self.lock:
                for alert in self.active_alerts:
                    if alert.alert_id == alert_id:
                        alert.acknowledged = True
                        break
            logger.info(f"Alerta {alert_id} reconhecido")
        except Exception as e:
            logger.error(f"Erro ao reconhecer alerta: {e}")

    def get_active_alerts(self) -> List[Alert]:
        """Retorna alertas ativos"""
        with self.lock:
            return self.active_alerts.copy()

    def clear_old_alerts(self, days: int = 7):
        """Remove alertas antigos"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            with self.lock:
                self.active_alerts = [
                    alert for alert in self.active_alerts
                    if alert.timestamp > cutoff_time
                ]
            logger.info(f"Alertas antigos removidos (> {days} dias)")
        except Exception as e:
            logger.error(f"Erro ao limpar alertas antigos: {e}")

    def process_event_candidate(self, event_candidate, camera_id: int,
                                 snapshot: Optional[Path] = None) -> bool:
        """
        Processa um EventCandidate e cria alerta se validado

        Args:
            event_candidate: EventCandidate do EventEngine
            camera_id: ID da câmera
            snapshot: Path para snapshot (opcional)

        Returns:
            True se alerta foi criado
        """
        try:
            # Validar evento com validator model
            is_valid = True
            validator_score = event_candidate.confidence  # Usar confidence original como padrão
            
            if self.validator:
                is_valid, validator_score = self.validator.validate_event_candidate(
                    event_candidate,
                    snapshot=snapshot
                )
                
                logger.debug(
                    f"Evento {event_candidate.event_type} validado: "
                    f"is_valid={is_valid}, score={validator_score:.2f}"
                )
            
            # Salvar evento no database com validator_score
            import json
            event_id = self.db.add_event(
                camera_id=camera_id,
                zone_id=event_candidate.zone_id,
                event_type=event_candidate.event_type,
                track_id=event_candidate.track_id,
                confidence=event_candidate.confidence,
                severity=event_candidate.severity,
                metadata=json.dumps(event_candidate.metadata),
                evidence_frames=None  # TODO: Serializar frames se necessário
            )
            
            # Atualizar validação no database
            self.db.update_event_validation(event_id, validator_score)
            
            # Criar alerta apenas se validado
            if is_valid:
                description = self._create_event_description(event_candidate)
                
                # Criar alerta (rule_id=0 para eventos temporais)
                alert = self.create_alert(
                    rule_id=0,
                    camera_id=camera_id,
                    event_type=event_candidate.event_type,
                    severity=event_candidate.severity,
                    description=description,
                    snapshot_path=str(snapshot) if snapshot else None
                )
                
                logger.info(
                    f"✓ Alerta criado para evento {event_candidate.event_type} "
                    f"(validator_score={validator_score:.2f})"
                )
                return True
            else:
                logger.info(
                    f"✗ Evento {event_candidate.event_type} rejeitado pelo validador "
                    f"(score={validator_score:.2f})"
                )
                return False
        
        except Exception as e:
            logger.error(f"Erro ao processar evento candidato: {e}", exc_info=True)
            return False

    def _create_event_description(self, event_candidate) -> str:
        """Cria descrição do evento a partir do EventCandidate"""
        description = f"{event_candidate.event_type.title()} detected"
        
        if event_candidate.metadata:
            metadata = event_candidate.metadata
            
            if 'duration' in metadata:
                description += f" (duration: {metadata['duration']:.1f}s)"
            
            if 'dwell_time' in metadata:
                description += f" (dwell time: {metadata['dwell_time']:.1f}s)"
            
            if 'person_count' in metadata:
                description += f" ({metadata['person_count']} people)"
        
        return description
