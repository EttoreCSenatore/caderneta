"""Tarefas administrativas da plataforma (rodam com o papel dono do banco).

python -m app.cli criar-escola "Escola Exemplo" admin@escola.com "Nome do Admin"
python -m app.cli notificar     # worker: avisos agendados, e-mails devidos e retenção (rodar a cada minuto)
python -m app.cli rotacionar-chave [--simular]   # regrava os dados cifrados com a chave atual (rotação de chave)
python -m app.cli revogar-sessoes [escola_id]   # incidente: encerra todas as sessões (ou só as de uma escola)
python -m app.cli registrar-backup caderneta-X.tar.gpg --tamanho N   # chamado pelo backup.sh (MO.4)
python -m app.cli registrar-backup --restauracao "ok"                 # chamado pelo restore-test.sh
"""

import argparse
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Escola, Papel, RegistroOperacao
from app.routers.convites import cria_convite


def criar_escola(nome: str, email: str, nome_admin: str) -> tuple[uuid.UUID, str]:
    engine = create_engine(get_settings().owner_database_url)
    escola_id = uuid.uuid4()  # fora da sessão: depois do commit o objeto fica desanexado
    with Session(engine) as db, db.begin():
        db.add(Escola(id=escola_id, nome=nome))
        db.flush()
        link = cria_convite(db, escola_id=escola_id, email=email, nome=nome_admin, papel=Papel.admin, criado_por=None)
    print(
        f"Escola criada: {escola_id}\nConvite do administrador criado para {email} (o e-mail só sai se o SMTP estiver "
        f"configurado).\nLink do convite: {link}"
    )
    return escola_id, link


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


def revogar_sessoes(escola_id: str | None = None) -> int:
    """Resposta a incidente: encerra sessões abertas (todas, ou só de quem tem perfil na escola indicada)."""
    from sqlalchemy import delete, select

    from app.models import Sessao, UsuarioPerfil

    engine = create_engine(get_settings().owner_database_url)
    with Session(engine) as db, db.begin():
        q = delete(Sessao)
        if escola_id:
            q = q.where(
                Sessao.usuario_id.in_(
                    select(UsuarioPerfil.usuario_id).where(UsuarioPerfil.escola_id == uuid.UUID(escola_id))
                )
            )
        n = db.execute(q).rowcount or 0
    print(f"sessões encerradas: {n}")
    return n


def rotacionar_chave(simular: bool, exigir_arquivos: bool = False) -> dict[str, int]:
    from app.chaves import rotaciona

    engine = create_engine(get_settings().owner_database_url)
    with Session(engine) as db, db.begin():
        r = rotaciona(db, simular)
    print(("[simulação, nada foi gravado] " if simular else "") + " · ".join(f"{k}: {v}" for k, v in r.items()))
    if exigir_arquivos and r["ausentes"]:
        raise SystemExit(f"FALHA: {r['ausentes']} arquivo(s) do banco não estão no armazenamento restaurado")
    return r


def gerar_vapid() -> None:
    from app.push import gerar_chaves

    privada, publica = gerar_chaves()
    print("Coloque no ambiente da API (a chave privada é segredo e não vai para o Git):")
    print(f"CADERNETA_VAPID_PRIVATE_KEY={privada}")
    print(f"CADERNETA_VAPID_PUBLIC_KEY={publica}")
    print("CADERNETA_VAPID_SUBJECT=mailto:contato-de-privacidade@sua-escola.com.br")


def registrar_backup(detalhe: str, tamanho: int | None, restauracao: bool = False) -> None:
    """Registra um backup (ou um teste de restauração) para os avisos de operação da direção."""
    engine = create_engine(get_settings().owner_database_url)
    tipo = "restauracao" if restauracao else "backup"
    with Session(engine) as db, db.begin():
        db.add(RegistroOperacao(tipo=tipo, detalhe=detalhe[:200], tamanho_bytes=tamanho))
    print(f"{tipo} registrado")


def main() -> None:
    p = argparse.ArgumentParser(prog="caderneta")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("criar-escola", help="cria uma escola e convida o primeiro administrador")
    c.add_argument("nome")
    c.add_argument("email")
    c.add_argument("nome_admin")
    r = sub.add_parser("revogar-sessoes", help="encerra todas as sessões (resposta a incidente)")
    r.add_argument("escola_id", nargs="?", default=None)
    k = sub.add_parser("rotacionar-chave", help="regrava os dados cifrados com a chave atual")
    k.add_argument("--simular", action="store_true", help="só conta o que seria regravado")
    k.add_argument(
        "--exigir-arquivos", action="store_true", help="falha se faltar arquivo no armazenamento (teste de restauração)"
    )
    sub.add_parser("gerar-vapid", help="gera as chaves do push (VAPID)")
    rb = sub.add_parser("registrar-backup", help="registra um backup feito (ou um teste de restauração)")
    rb.add_argument("detalhe", nargs="?", default="", help="nome do arquivo ou resultado")
    rb.add_argument("--tamanho", type=int, default=None, help="tamanho do arquivo em bytes")
    rb.add_argument("--restauracao", action="store_true", help="registra um teste de restauração bem-sucedido")
    sub.add_parser("notificar", help="worker de notificações (agendados, e-mails, retenção)")
    a = p.parse_args()
    if a.cmd == "criar-escola":
        criar_escola(a.nome, a.email, a.nome_admin)
    elif a.cmd == "notificar":
        notificar()
    elif a.cmd == "revogar-sessoes":
        revogar_sessoes(a.escola_id)
    elif a.cmd == "rotacionar-chave":
        rotacionar_chave(a.simular, a.exigir_arquivos)
    elif a.cmd == "gerar-vapid":
        gerar_vapid()
    elif a.cmd == "registrar-backup":
        registrar_backup(a.detalhe, a.tamanho, a.restauracao)


if __name__ == "__main__":
    main()
