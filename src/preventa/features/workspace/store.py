import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4


def _database_path() -> Path:
    configured = os.getenv("PREVENTA_DB_PATH")
    if configured:
        return Path(configured)
    if os.getenv("VERCEL"):
        return Path("/tmp/preventa-mvp.db")
    return Path(".data/preventa-mvp.db")


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(path)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    try:
        yield database
        database.commit()
    finally:
        database.close()


def initialize_store() -> None:
    with connection() as database:
        database.executescript(
            """
            CREATE TABLE IF NOT EXISTS mvp_studies (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                client TEXT NOT NULL,
                facility TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS mvp_nodes (
                id TEXT PRIMARY KEY,
                study_id TEXT NOT NULL REFERENCES mvp_studies(id) ON DELETE CASCADE,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                equipment_type TEXT NOT NULL,
                design_intent TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'empty'
            );
            CREATE TABLE IF NOT EXISTS mvp_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT NOT NULL REFERENCES mvp_nodes(id) ON DELETE CASCADE,
                guideword TEXT NOT NULL,
                deviation TEXT NOT NULL DEFAULT '',
                cause TEXT NOT NULL DEFAULT '',
                consequence TEXT NOT NULL DEFAULT '',
                safeguard TEXT NOT NULL DEFAULT '',
                severity INTEGER NOT NULL DEFAULT 1,
                likelihood INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'Eksik',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS mvp_lopa_layers (
                id TEXT PRIMARY KEY,
                row_id INTEGER NOT NULL REFERENCES mvp_rows(id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                pfd REAL NOT NULL,
                is_valid INTEGER NOT NULL DEFAULT 1,
                note TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS mvp_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                action TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # Use INSERT OR IGNORE to be safe in multi-process deployments
        _seed(database)


def _seed(database: sqlite3.Connection) -> None:
    database.execute(
        """
        INSERT OR IGNORE INTO mvp_studies (id, title, client, facility, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("study-reactor-2026", "Ünite 200 HAZOP", "ACWA Power", "Konya", "in_review"),
    )
    nodes = [
        (
            "node-t100",
            "N-01",
            "Hammadde tankı T-100",
            "Atmosferik tank",
            "Hammaddeyi güvenli işletme sınırlarında depolamak.",
            "complete",
        ),
        (
            "node-p101",
            "N-02",
            "Besleme pompası P-101",
            "Santrifüj pompa",
            (
                "T-100 hammadde tankından R-201 reaktörüne kesintisiz ve "
                "kontrollü besleme sağlamak."
            ),
            "active",
        ),
        (
            "node-e102",
            "N-03",
            "Isı eşanjörü E-102",
            "Kabuk-boru eşanjör",
            "Besleme sıcaklığını reaksiyon giriş koşuluna getirmek.",
            "review",
        ),
        (
            "node-r201",
            "N-04",
            "Reaktör R-201",
            "Karıştırıcılı reaktör",
            "Reaksiyonu tanımlı sıcaklık ve basınç aralığında yürütmek.",
            "review",
        ),
        (
            "node-v301",
            "N-05",
            "Ayırıcı V-301",
            "Basınçlı kap",
            "Gaz ve sıvı fazlarını güvenli biçimde ayırmak.",
            "empty",
        ),
    ]
    database.executemany(
        """
        INSERT OR IGNORE INTO mvp_nodes
            (id, study_id, code, name, equipment_type, design_intent, state)
        VALUES (?, 'study-reactor-2026', ?, ?, ?, ?, ?)
        """,
        nodes,
    )
    rows = [
        (
            "Yok",
            "Akış yok",
            "Ortak emiş hattında izolasyon vanasının kapalı kalması",
            "Reaktör beslemesinin kesilmesi ve plansız duruş",
            "Düşük akış alarmı FAL-101; yedek pompa devreye alma prosedürü",
            3,
            2,
            "İncelendi",
        ),
        (
            "Fazla",
            "Yüksek akış",
            "Kontrol vanası FV-101'in tam açık konumda arızalanması",
            "Reaktör sıcaklığının yükselmesi ve spesifikasyon dışı üretim",
            "Yüksek akış alarmı FAH-101; bağımsız TSHH-204 tripi",
            4,
            2,
            "Taslak",
        ),
        (
            "Ters",
            "Ters akış",
            "Pompa duruşunda çekvalfin sızdırması veya açık kalması",
            "Tankta aşırı basınç ve kontaminasyon",
            "Çekvalf bakım programı; motorlu izolasyon vanası",
            4,
            3,
            "Eksik",
        ),
        (
            "Az",
            "Düşük akış",
            "Emiş filtresinin kısmi tıkanması veya tank seviyesinin düşmesi",
            "Pompa kavitasyonu ve yanıcı akışkan kaçağı",
            "Düşük tank seviye alarmı LAL-100; titreşim izleme",
            3,
            3,
            "Taslak",
        ),
    ]
    database.executemany(
        """
        INSERT INTO mvp_rows
            (node_id, guideword, deviation, cause, consequence, safeguard,
             severity, likelihood, status)
        VALUES ('node-p101', ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def risk_label(severity: int, likelihood: int) -> str:
    """Risk boundaries aligned with 5×5 matrix: >=16 Kritik, >=9 Yüksek, >=4 Orta."""
    score = severity * likelihood
    if score >= 16:
        return "Kritik"
    if score >= 9:
        return "Yüksek"
    if score >= 4:
        return "Orta"
    return "Düşük"


def audit(database: sqlite3.Connection, entity_type: str, entity_id: str, action: str) -> None:
    database.execute(
        """
        INSERT INTO mvp_audit (entity_type, entity_id, action, detail)
        VALUES (?, ?, ?, ?)
        """,
        (entity_type, entity_id, action, f"{entity_type} {action}"),
    )


def row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"
