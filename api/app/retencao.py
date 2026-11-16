"""Eliminação de arquivos e pedidos vencidos (LGPD art. 15 e 16: dado sem finalidade é eliminado).

Roda no worker (`python -m app.cli notificar`), com o papel dono do banco. Prazos em `config.py`:
- pedidos de impressão: `retencao_pedidos_dias` depois da data de aplicação (apaga também comentários e arquivos);
- rascunhos parados: `retencao_rascunho_dias` depois de criados;
- anexos de mensagens: `retencao_anexos_dias` (a mensagem de texto continua);
- arquivos órfãos no disco (sobras de um envio que não chegou a ser gravado no banco), com mais de 1 hora.
"""

import uuid
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import arquivos
from app.audit import registrar
from app.config import get_settings
from app.models import Anotacao, Arquivo, MensagemAnexo, PedidoImpressao, PedidoTitular, StatusPedido

DIAS_ANOTACAO_REMOVIDA = 30


def _apaga_arquivos(db: Session, ids: set[uuid.UUID]) -> None:
    for aid in ids:
        a = db.get(Arquivo, aid)
        if not a:
            continue
        usado = db.scalar(
            select(PedidoImpressao.id)
            .where((PedidoImpressao.arquivo_id == aid) | (PedidoImpressao.arquivo_adaptado_id == aid))
            .limit(1)
        ) or db.scalar(select(MensagemAnexo.id).where(MensagemAnexo.arquivo_id == aid).limit(1))
        if not usado:
            arquivos.apaga(a)
            db.delete(a)


def elimina_vencidos(db: Session, agora: datetime | None = None) -> dict[str, int]:
    s = get_settings()
    agora = agora or datetime.now(UTC)
    hoje: date = agora.date()
    por_escola: Counter[tuple[uuid.UUID, str]] = Counter()
    candidatos: set[uuid.UUID] = set()

    vencidos = db.scalars(
        select(PedidoImpressao).where(
            (PedidoImpressao.data_aplicacao < hoje - timedelta(days=s.retencao_pedidos_dias))
            | (
                (PedidoImpressao.status == StatusPedido.rascunho)
                & (PedidoImpressao.criado_em < agora - timedelta(days=s.retencao_rascunho_dias))
            )
        )
    ).unique()
    for p in list(vencidos):
        candidatos |= {p.arquivo_id} | ({p.arquivo_adaptado_id} if p.arquivo_adaptado_id else set())
        por_escola[(p.escola_id, "pedidos")] += 1
        db.delete(p)
    db.flush()

    antigos = db.scalars(
        select(MensagemAnexo).where(MensagemAnexo.criado_em < agora - timedelta(days=s.retencao_anexos_dias))
    ).unique()
    for x in list(antigos):
        candidatos.add(x.arquivo_id)
        por_escola[(x.escola_id, "anexos")] += 1
        db.delete(x)
    db.flush()

    # anotações removidas: eliminadas de vez (com as versões) depois do prazo de carência
    for an in list(
        db.scalars(
            select(Anotacao).where(
                Anotacao.removida_em.is_not(None),
                Anotacao.removida_em < agora - timedelta(days=DIAS_ANOTACAO_REMOVIDA),
            )
        ).unique()
    ):
        por_escola[(an.escola_id, "anotacoes")] += 1
        db.delete(an)
    db.flush()

    # pedidos de titulares já respondidos: a prova de atendimento vale pelo mesmo prazo dos demais registros
    for pt in list(
        db.scalars(
            select(PedidoTitular).where(
                PedidoTitular.respondido_em.is_not(None),
                PedidoTitular.respondido_em < agora - timedelta(days=s.retencao_pedidos_titular_dias),
            )
        ).unique()
    ):
        por_escola[(pt.escola_id, "pedidos_titular")] += 1
        db.delete(pt)
    db.flush()

    _apaga_arquivos(db, candidatos)
    for (escola_id, tipo), n in por_escola.items():
        registrar(db, "retencao.eliminar", escola_id=escola_id, usuario_id=None, detalhes={"tipo": tipo, "itens": n})
    orfaos = varre_orfaos(db, agora)
    return {
        "pedidos": sum(n for (_, t), n in por_escola.items() if t == "pedidos"),
        "anexos": sum(n for (_, t), n in por_escola.items() if t == "anexos"),
        "anotacoes": sum(n for (_, t), n in por_escola.items() if t == "anotacoes"),
        "pedidos_titular": sum(n for (_, t), n in por_escola.items() if t == "pedidos_titular"),
        "orfaos": orfaos,
    }


def varre_orfaos(db: Session, agora: datetime | None = None) -> int:
    """Apaga do disco arquivos sem registro no banco (e com mais de 1 hora, para não pegar um envio em andamento)."""
    raiz = Path(get_settings().storage_dir)
    if not raiz.is_dir():
        return 0
    corte = (agora or datetime.now(UTC)).timestamp() - 3600
    apagados = 0
    for f in raiz.glob("*/*"):
        if f.suffix not in {".bin", ".tmp"} or f.stat().st_mtime > corte:
            continue
        try:
            aid = uuid.UUID(f.stem)
        except ValueError:
            continue
        if f.suffix == ".tmp" or not db.get(Arquivo, aid):
            f.unlink(missing_ok=True)
            apagados += 1
    return apagados
