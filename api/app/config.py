"""Configuração por variáveis de ambiente (prefixo CADERNETA_)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CADERNETA_", env_file=".env", extra="ignore")

    # Papel da API: não é dono das tabelas, então o RLS vale.
    database_url: str = "postgresql+psycopg://caderneta_app:dev-app@127.0.0.1:5433/caderneta"
    # Papel dono: só para migrações e para o seed de demonstração.
    owner_database_url: str = "postgresql+psycopg://caderneta_owner:dev-owner@127.0.0.1:5433/caderneta"

    # Chave AES-256 (base64 urlsafe, 32 bytes) para dados sensíveis. Em produção é obrigatória.
    data_key: str = ""
    env: str = "dev"  # dev | test | prod

    public_url: str = "http://localhost:5173"
    cookie_secure: bool = False
    session_idle_hours: int = 12
    session_max_days: int = 30
    require_staff_2fa: bool = True
    totp_anti_reuso: bool = (
        True  # o mesmo código de 6 dígitos não vale duas vezes (desligado só nos testes que logam várias vezes)
    )
    rate_limit: bool = True  # limite de tentativas por IP e por e-mail (desligado só nos testes que não o exercitam)

    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = False
    mail_from: str = "Caderneta <nao-responda@caderneta.local>"
    mail_backend: str = "smtp"  # smtp | memory

    invite_days: int = 7
    max_upload_bytes: int = 2_000_000
    # Arquivos de provas e trabalhos: cifrados em repouso (AES-GCM) num diretório fora do código.
    storage_dir: str = "./storage"
    max_arquivo_bytes: int = 15_000_000
    link_validade_s: int = 300
    max_anexo_bytes: int = 10_000_000  # anexos de mensagens (PDF e imagens)
    # Antivírus (ClamAV via clamd). Falha fechada: se ligado e fora do ar, o upload é recusado. Obrigatório em produção.
    antivirus: str = "off"  # off | clamav
    clamav_host: str = "127.0.0.1"
    clamav_port: int = 3310
    clamav_timeout_s: int = 20
    # Conversão de DOCX para PDF (LibreOffice sem interface, isolado por upload).
    conversor: str = "off"  # off | libreoffice
    soffice_path: str = "soffice"
    conversor_timeout_s: int = 60
    # Push (Web Push com VAPID, sem conteúdo na mensagem). Gere as chaves com `python -m app.cli gerar-vapid`.
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_subject: str = "mailto:privacidade@caderneta.local"
    push_hosts_extra: str = ""  # hosts extras permitidos (separados por vírgula), só para testes e ambientes internos
    retencao_push_dias: int = 90  # inscrição de aparelho sem uso é apagada
    # Retenção (dias). Aplicada pelo worker `app.cli notificar`.
    retencao_pedidos_dias: int = 365  # depois da data de aplicação
    retencao_rascunho_dias: int = 90  # rascunho parado
    retencao_anexos_dias: int = 365  # anexos de mensagens
    retencao_pedidos_titular_dias: int = (
        1825  # pedidos de titulares respondidos: 5 anos da resposta (prova de atendimento)
    )


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.env == "prod":
        if not s.data_key:
            raise RuntimeError("CADERNETA_DATA_KEY é obrigatória em produção")
        if s.antivirus != "clamav":
            raise RuntimeError("CADERNETA_ANTIVIRUS=clamav é obrigatório em produção")
        if not s.storage_dir.startswith("/"):
            raise RuntimeError("CADERNETA_STORAGE_DIR deve ser um caminho absoluto em produção")
        if not s.cookie_secure:
            raise RuntimeError("CADERNETA_COOKIE_SECURE deve ser true em produção")
    return s
