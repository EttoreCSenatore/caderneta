"""Avisos de operação (MO.4): backup atrasado, teste de restauração vencido, disco e memória no limite.

O backup e o teste de restauração rodam fora do app (cron no servidor) e se registram pelo CLI
(`python -m app.cli registrar-backup`). O app só lê esses registros e mede disco e memória na hora do pedido:
não há coleta em segundo plano nem acesso ao Docker.
"""

import shutil
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import RegistroOperacao

MEMINFO = Path("/proc/meminfo")


def backup_monitorado() -> bool:
    s = get_settings()
    return s.env == "prod" if s.backup_monitorado is None else s.backup_monitorado


def ultimo(db: Session, tipo: str) -> RegistroOperacao | None:
    return db.scalars(
        select(RegistroOperacao)
        .where(RegistroOperacao.tipo == tipo)
        .order_by(RegistroOperacao.feito_em.desc())
        .limit(1)
    ).first()


def disco_pct(caminho: str) -> int | None:
    try:
        u = shutil.disk_usage(caminho)
    except OSError:
        return None
    return round(100 * u.used / u.total) if u.total else None


def memoria_pct(meminfo: Path = MEMINFO) -> int | None:
    """Memória em uso (sem cache), pelo /proc/meminfo; None fora do Linux."""
    try:
        campos = dict(linha.split(":", 1) for linha in meminfo.read_text().splitlines() if ":" in linha)
        total = int(campos["MemTotal"].split()[0])
        livre = int(campos["MemAvailable"].split()[0])
    except (OSError, KeyError, ValueError):
        return None
    return round(100 * (total - livre) / total) if total else None


def _horas(desde: datetime, agora: datetime) -> int:
    return int((agora - desde).total_seconds() // 3600)


def situacao(db: Session, agora: datetime | None = None) -> dict:
    s = get_settings()
    agora = agora or datetime.now(UTC)
    avisos: list[dict] = []
    b = ultimo(db, "backup")
    r = ultimo(db, "restauracao")
    if backup_monitorado():
        if b is None:
            avisos.append({"codigo": "backup", "texto": "Nenhum backup registrado nesta instalação."})
        elif _horas(b.feito_em, agora) > s.backup_max_horas:
            avisos.append({"codigo": "backup", "texto": f"O último backup foi há {_horas(b.feito_em, agora)} horas."})
        if r is None:
            avisos.append({"codigo": "restauracao", "texto": "Nenhum teste de restauração do backup registrado."})
        elif (agora - r.feito_em).days > s.restauracao_max_dias:
            avisos.append(
                {
                    "codigo": "restauracao",
                    "texto": f"O último teste de restauração do backup foi há {(agora - r.feito_em).days} dias.",
                }
            )
    disco = disco_pct(s.storage_dir)
    if disco is not None and disco >= s.disco_max_pct:
        avisos.append({"codigo": "disco", "texto": f"Disco do servidor em {disco}% (limite {s.disco_max_pct}%)."})
    mem = memoria_pct()
    if mem is not None and mem >= s.memoria_max_pct:
        avisos.append({"codigo": "memoria", "texto": f"Memória do servidor em {mem}% (limite {s.memoria_max_pct}%)."})
    n_backups = db.scalar(select(func.count()).select_from(RegistroOperacao).where(RegistroOperacao.tipo == "backup"))
    return {
        "avisos": avisos,
        "backup_monitorado": backup_monitorado(),
        "ultimo_backup": b.feito_em.isoformat() if b else None,
        "ultima_restauracao": r.feito_em.isoformat() if r else None,
        "backups_registrados": n_backups,
        "disco_pct": disco,
        "memoria_pct": mem,
    }
