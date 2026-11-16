"""Tarefas administrativas da plataforma (rodam com o papel dono do banco).

python -m app.cli criar-escola "Escola Exemplo" admin@escola.com "Nome do Admin"
python -m app.cli notificar     # worker: avisos agendados, e-mails devidos e retenção (rodar a cada minuto)
"""

import argparse
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Escola, Papel
from app.routers.convites import cria_convite


def criar_escola(nome: str, email: str, nome_admin: str) -> None:
    engine = create_engine(get_settings().owner_database_url)
    with Session(engine) as db, db.begin():
        escola = Escola(id=uuid.uuid4(), nome=nome)
        db.add(escola)
        db.flush()
        link = cria_convite(db, escola_id=escola.id, email=email, nome=nome_admin, papel=Papel.admin, criado_por=None)
    print(f"Escola criada: {escola.id}\nConvite do administrador enviado para {email}.\nLink: {link}")


def notificar() -> None:
    from app.notificacoes import processar

    engine = create_engine(get_settings().owner_database_url)
    with Session(engine) as db, db.begin():
        r = processar(db)
    print(
        f"avisos liberados: {r['avisos']} · e-mails enviados: {r['emails']} · notificações apagadas: {r['apagadas']}"
        f" · pedidos eliminados: {r['eliminados_pedidos']} · anexos: {r['eliminados_anexos']}"
        f" · arquivos órfãos: {r['eliminados_orfaos']} · pushes: {r['pushes']}"
    )


def gerar_vapid() -> None:
    from app.push import gerar_chaves

    privada, publica = gerar_chaves()
    print("Coloque no ambiente da API (a chave privada é segredo e não vai para o Git):")
    print(f"CADERNETA_VAPID_PRIVATE_KEY={privada}")
    print(f"CADERNETA_VAPID_PUBLIC_KEY={publica}")
    print("CADERNETA_VAPID_SUBJECT=mailto:contato-de-privacidade@sua-escola.com.br")


def main() -> None:
    p = argparse.ArgumentParser(prog="caderneta")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("criar-escola", help="cria uma escola e convida o primeiro administrador")
    c.add_argument("nome")
    c.add_argument("email")
    c.add_argument("nome_admin")
    sub.add_parser("gerar-vapid", help="gera as chaves do push (VAPID)")
    sub.add_parser("notificar", help="worker de notificações (agendados, e-mails, retenção)")
    a = p.parse_args()
    if a.cmd == "criar-escola":
        criar_escola(a.nome, a.email, a.nome_admin)
    elif a.cmd == "notificar":
        notificar()
    elif a.cmd == "gerar-vapid":
        gerar_vapid()


if __name__ == "__main__":
    main()
