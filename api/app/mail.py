"""Envio de e-mail. Em testes usa uma caixa em memória."""

import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

log = logging.getLogger("caderneta.mail")
outbox: list[EmailMessage] = []


def enviar(para: str, assunto: str, texto: str) -> None:
    s = get_settings()
    msg = EmailMessage()
    msg["From"] = s.mail_from
    msg["To"] = para
    msg["Subject"] = assunto
    msg.set_content(texto)
    if s.mail_backend == "memory":
        outbox.append(msg)
        return
    try:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=10) as smtp:
            if s.smtp_starttls:
                smtp.starttls()
            if s.smtp_user:
                smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(msg)
    except OSError:
        # Não derruba a requisição; o convite pode ser reenviado. Sem dados pessoais no log.
        log.exception("falha ao enviar e-mail")
