"""Download de arquivos por link assinado (provas, trabalhos e anexos de mensagens).

O link vale poucos minutos, é preso ao usuário e à escola e não é um endereço permanente. Na hora do download a API
exige a sessão e confere o acesso de novo (o professor pode ter despublicado, o vínculo pode ter acabado).
"""

import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response

from app import arquivos
from app.audit import registrar
from app.deps import Contexto, com_perfil
from app.models import Arquivo, Mensagem, MensagemAnexo, Papel
from app.routers.impressao import _auditar, _pedido
from app.routers.mensagens import _conversa
from app.security import verifica_link

router = APIRouter(tags=["arquivos"])
LEITORES = {Papel.responsavel, Papel.aluno}


def _do_pedido(ctx: Contexto, carga: dict) -> Arquivo:
    p = _pedido(ctx, uuid.UUID(carga["p"]))  # confere o acesso de novo, na hora do download
    a = p.arquivo_adaptado if carga["v"] == "adaptado" else p.arquivo
    if not a or (carga["v"] == "adaptado" and ctx.papel in LEITORES):
        raise HTTPException(404, "Arquivo não encontrado.")
    _auditar(ctx, "pedido.baixar", p, versao=carga["v"], arquivo=str(a.id))
    return a


def _do_anexo(ctx: Contexto, carga: dict) -> Arquivo:
    x = ctx.db.get(MensagemAnexo, uuid.UUID(carga["a"]))
    m = ctx.db.get(Mensagem, x.mensagem_id) if x else None
    if not x or not m:
        raise HTTPException(404, "Arquivo não encontrado.")
    c = _conversa(ctx, m.conversa_id)
    registrar(
        ctx.db,
        "mensagem.baixar",
        escola_id=ctx.escola_id,
        usuario_id=ctx.usuario.id,
        entidade="conversa",
        entidade_id=c.id,
        detalhes={"anexo": str(x.id)},
    )
    return x.arquivo


@router.get("/arquivos/{token}")
def baixar(token: str, ctx: Contexto = Depends(com_perfil)):
    carga = verifica_link(token)
    if not carga or carga.get("u") != str(ctx.usuario.id) or carga.get("s") != str(ctx.escola_id):
        raise HTTPException(404, "Link inválido ou expirado.")
    a = _do_anexo(ctx, carga) if carga.get("k") == "m" else _do_pedido(ctx, carga)
    return Response(
        arquivos.le(a),
        media_type=a.mime,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(a.nome)}", "Cache-Control": "no-store"},
    )
