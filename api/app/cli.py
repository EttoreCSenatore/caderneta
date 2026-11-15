"""Tarefas administrativas da plataforma (rodam com o papel dono do banco).

python -m app.cli criar-escola "Escola Exemplo" admin@escola.com "Nome do Admin"
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


def main() -> None:
    p = argparse.ArgumentParser(prog="caderneta")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("criar-escola", help="cria uma escola e convida o primeiro administrador")
    c.add_argument("nome")
    c.add_argument("email")
    c.add_argument("nome_admin")
    a = p.parse_args()
    if a.cmd == "criar-escola":
        criar_escola(a.nome, a.email, a.nome_admin)


if __name__ == "__main__":
    main()
