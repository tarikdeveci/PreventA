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
    already = database.execute(
        "SELECT 1 FROM mvp_studies WHERE id = 'study-reactor-2026'"
    ).fetchone()
    if already:
        return  # Idempotent: only seed a fresh database.

    database.executemany(
        """
        INSERT INTO mvp_studies (id, title, client, facility, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("study-reactor-2026", "Ünite 200 HAZOP", "ACWA Power", "Konya", "in_review"),
            (
                "study-utility-2026",
                "Ünite 400 Yardımcı Tesisler HAZOP",
                "ACWA Power",
                "Konya",
                "draft",
            ),
            ("study-tank-2026", "Tank Sahası LOPA Revizyonu", "SOCAR", "Aliağa", "in_review"),
        ],
    )

    nodes = [
        # study-reactor-2026
        ("node-t100", "study-reactor-2026", "N-01", "Hammadde tankı T-100",
         "Atmosferik tank", "Hammaddeyi güvenli işletme sınırlarında depolamak.", "complete"),
        ("node-p101", "study-reactor-2026", "N-02", "Besleme pompası P-101",
         "Santrifüj pompa",
         "T-100 hammadde tankından R-201 reaktörüne kesintisiz ve kontrollü besleme sağlamak.",
         "active"),
        ("node-e102", "study-reactor-2026", "N-03", "Isı eşanjörü E-102",
         "Kabuk-boru eşanjör", "Besleme sıcaklığını reaksiyon giriş koşuluna getirmek.", "review"),
        ("node-r201", "study-reactor-2026", "N-04", "Reaktör R-201",
         "Karıştırıcılı reaktör", "Reaksiyonu tanımlı sıcaklık ve basınç aralığında yürütmek.",
         "review"),
        ("node-v301", "study-reactor-2026", "N-05", "Ayırıcı V-301",
         "Basınçlı kap", "Gaz ve sıvı fazlarını güvenli biçimde ayırmak.", "active"),
        # study-utility-2026
        ("node-bfw", "study-utility-2026", "N-01", "Kazan besleme suyu pompası P-401",
         "Santrifüj pompa", "Buhar kazanına kesintisiz besleme suyu sağlamak.", "empty"),
        ("node-deaer", "study-utility-2026", "N-02", "Degazör D-401",
         "Basınçlı kap", "Besleme suyundan çözünmüş oksijeni uzaklaştırmak.", "empty"),
    ]
    database.executemany(
        """
        INSERT INTO mvp_nodes
            (id, study_id, code, name, equipment_type, design_intent, state)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        nodes,
    )

    # (node_id, guideword, deviation, cause, consequence, safeguard, severity, likelihood, status)
    rows = [
        # T-100 — Hammadde tankı
        ("node-t100", "Fazla", "Yüksek seviye",
         "Seviye kontrol vanası LV-100 tam açık arızası ve operatör müdahalesinin gecikmesi",
         "Tank taşması, yanıcı sıvı dökülmesi ve çevresel kirlilik",
         "Yüksek seviye alarmı LAH-100; bağımsız LSHH-100 dolum kesme tripi", 4, 2, "İncelendi"),
        ("node-t100", "Diğer", "Vakum (atmosfer altı basınç)",
         "Hızlı boşaltma sırasında vakum kırıcının tıkalı kalması",
         "Tank cidarının içe doğru çökmesi ve mekanik hasar",
         "Vakum kırıcı PVRV-100; periyodik vakum vanası testi", 3, 2, "İncelendi"),
        ("node-t100", "Daha fazla", "Yüksek sıcaklık",
         "Yaz koşullarında güneş ışınımı ve havalandırma yetersizliği",
         "Buharlaşma kaybı ve solunum vanasından emisyon artışı",
         "Beyaz reflektif boya; solunum vanası PVRV-100", 2, 3, "Taslak"),

        # P-101 — Besleme pompası
        ("node-p101", "Yok", "Akış yok",
         "Ortak emiş hattında izolasyon vanasının kapalı kalması",
         "Reaktör beslemesinin kesilmesi ve plansız duruş",
         "Düşük akış alarmı FAL-101; yedek pompa devreye alma prosedürü", 3, 2, "İncelendi"),
        ("node-p101", "Fazla", "Yüksek akış",
         "Kontrol vanası FV-101'in tam açık konumda arızalanması",
         "Reaktör sıcaklığının yükselmesi ve spesifikasyon dışı üretim",
         "Yüksek akış alarmı FAH-101; bağımsız TSHH-204 tripi", 4, 2, "Taslak"),
        ("node-p101", "Ters", "Ters akış",
         "Pompa duruşunda çekvalfin sızdırması veya açık kalması",
         "Tankta aşırı basınç ve kontaminasyon",
         "Çekvalf bakım programı; motorlu izolasyon vanası", 4, 3, "Eksik"),
        ("node-p101", "Az", "Düşük akış",
         "Emiş filtresinin kısmi tıkanması veya tank seviyesinin düşmesi",
         "Pompa kavitasyonu ve yanıcı akışkan kaçağı",
         "Düşük tank seviye alarmı LAL-100; titreşim izleme", 3, 3, "Taslak"),

        # E-102 — Isı eşanjörü
        ("node-e102", "Daha fazla", "Yüksek sıcaklık",
         "Buhar kontrol vanası TV-102'nin tam açık konumda arızalanması",
         "Reaktör giriş sıcaklığının aşırı yükselmesi ve runaway reaksiyon tetiklenmesi",
         "Yüksek sıcaklık alarmı TAH-102; bağımsız TSHH-102 buhar kesme tripi", 4, 3, "Eksik"),
        ("node-e102", "Az", "Düşük sıcaklık",
         "Buhar beslemesinin kesilmesi veya kondens tahliyesinin tıkanması",
         "Reaksiyon veriminin düşmesi ve spesifikasyon dışı ürün",
         "Düşük sıcaklık alarmı TAL-102", 2, 3, "Taslak"),
        ("node-e102", "Parçası", "Tüp sızıntısı / çapraz kontaminasyon",
         "Tüp demetinde korozyon kaynaklı delinme",
         "Proses akışkanı ile ısıtıcı ortamın karışması",
         "Periyodik tüp kalınlık ölçümü; kondens iletkenlik izleme", 3, 2, "İncelendi"),

        # R-201 — Reaktör
        ("node-r201", "Daha fazla", "Yüksek basınç",
         "Soğutma suyu kaybı ile birlikte reaksiyon hızının kontrolsüz artması",
         "Aşırı basınç, kabuk yırtılması ve yanıcı bulut oluşumu",
         "Emniyet ventili PSV-201; acil soğutma ve SIS basınç tripi", 5, 3, "Eksik"),
        ("node-r201", "Daha fazla", "Yüksek sıcaklık (runaway)",
         "Karıştırıcı motorunun durması ile reaksiyon ısısının birikmesi",
         "Kontrolsüz ekzotermik reaksiyon ve termal patlama",
         "Karıştırıcı durdu alarmı; TSHH-201 SIS tripi; acil quench sistemi", 5, 2, "Taslak"),
        ("node-r201", "Yok", "Karıştırma yok",
         "Karıştırıcı kaplin arızası veya tahrik motoru elektrik kesintisi",
         "Lokal sıcak nokta ve reaksiyon kararsızlığı",
         "Karıştırıcı dönüş hızı izleme; düşük devir alarmı", 4, 2, "Taslak"),

        # V-301 — Ayırıcı
        ("node-v301", "Daha fazla", "Yüksek sıvı seviyesi",
         "Seviye kontrol vanası LV-301'in kapalı arızası",
         "Gaz çıkış hattına sıvı taşınması ve aşağı akış ekipmanı hasarı",
         "Yüksek seviye alarmı LAH-301; LSHH-301 tripi", 3, 3, "Taslak"),
        ("node-v301", "Az", "Düşük sıvı seviyesi",
         "Sıvı tahliye vanasının açık arızası",
         "Gaz blow-by ve aşağı akışa yüksek basınçlı gaz geçişi",
         "Düşük seviye alarmı LAL-301; tahliye hattı çekvalfi", 4, 2, "İncelendi"),
    ]
    database.executemany(
        """
        INSERT INTO mvp_rows
            (node_id, guideword, deviation, cause, consequence, safeguard,
             severity, likelihood, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )

    # Attach LOPA / IPL layers to the highest-risk scenarios (severity*likelihood >= 12).
    critical = database.execute(
        "SELECT id FROM mvp_rows WHERE severity * likelihood >= 12 ORDER BY id"
    ).fetchall()
    lopa: list[tuple[str, int, str, float, int, str]] = []
    for index, row in enumerate(critical):
        row_id = int(row["id"])
        lopa.append((
            f"ipl-seed-{row_id}-a", row_id,
            "Bağımsız yüksek-yüksek trip (SIS, SIL-2)", 1.0e-2, 1, "Yıllık kanıt testi",
        ))
        if index % 2 == 0:
            lopa.append((
                f"ipl-seed-{row_id}-b", row_id,
                "Basınç tahliye ventili (PSV) — koruyucu katman", 1.0e-2, 1,
                "5 yılda bir sökme-kalibrasyon",
            ))
    database.executemany(
        """
        INSERT INTO mvp_lopa_layers (id, row_id, description, pfd, is_valid, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        lopa,
    )


def risk_label(severity: int, likelihood: int) -> str:
    """Risk boundaries aligned with the ACWA 5×5 matrix: >=12 Kritik, >=8 Yüksek, >=4 Orta.

    Must stay in sync with the frontend matrix zoning in frontend/src/App.tsx.
    """
    score = severity * likelihood
    if score >= 12:
        return "Kritik"
    if score >= 8:
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
