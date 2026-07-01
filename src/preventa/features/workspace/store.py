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
            CREATE TABLE IF NOT EXISTS mvp_library (
                id TEXT PRIMARY KEY,
                equipment_type TEXT NOT NULL,
                guideword TEXT NOT NULL,
                deviation TEXT NOT NULL,
                cause TEXT NOT NULL,
                consequence TEXT NOT NULL,
                safeguard TEXT NOT NULL DEFAULT '',
                severity INTEGER NOT NULL DEFAULT 3,
                likelihood INTEGER NOT NULL DEFAULT 2,
                source_ref TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS mvp_sources (
                id TEXT PRIMARY KEY,
                study_id TEXT NOT NULL REFERENCES mvp_studies(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                reference TEXT NOT NULL DEFAULT '',
                section_count INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS mvp_risk_matrix (
                study_id TEXT PRIMARY KEY REFERENCES mvp_studies(id) ON DELETE CASCADE,
                low_max INTEGER NOT NULL DEFAULT 3,
                medium_max INTEGER NOT NULL DEFAULT 7,
                high_max INTEGER NOT NULL DEFAULT 11,
                revision INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS mvp_reports (
                id TEXT PRIMARY KEY,
                study_id TEXT NOT NULL REFERENCES mvp_studies(id) ON DELETE CASCADE,
                node_id TEXT NOT NULL REFERENCES mvp_nodes(id) ON DELETE CASCADE,
                filename TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS app_users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'facilitator', 'viewer')),
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS app_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS app_revoked_sessions (
                token_hash TEXT PRIMARY KEY,
                revoked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS mvp_imports (
                content_hash TEXT PRIMARY KEY,
                study_id TEXT NOT NULL REFERENCES mvp_studies(id) ON DELETE CASCADE,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # Use INSERT OR IGNORE to be safe in multi-process deployments
        _seed(database)
        _seed_reference_data(database)


def _seed_reference_data(database: sqlite3.Connection) -> None:
    database.executemany(
        """
        INSERT OR IGNORE INTO mvp_library
            (id, equipment_type, guideword, deviation, cause, consequence,
             safeguard, severity, likelihood, source_ref)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "lib-pump-no-flow",
                "Centrifugal pump",
                "Yok",
                "No flow",
                "Suction isolation closed, low vessel level or blocked strainer",
                "Loss of downstream feed, pump overheating and potential seal failure",
                "Low-flow alarm; standby pump auto-start; operator response procedure",
                3,
                2,
                "IEC 61882 / pump study pattern",
            ),
            (
                "lib-vessel-high-pressure",
                "Pressure vessel",
                "Fazla",
                "High pressure",
                "Blocked outlet, external fire or pressure-control failure",
                "Loss of containment and personnel exposure",
                "PSV; high-pressure alarm; independent shutdown",
                5,
                2,
                "IEC 61882 / pressure protection pattern",
            ),
            (
                "lib-heat-exchanger-cross-leak",
                "Shell-and-tube heat exchanger",
                "Başka",
                "Cross contamination",
                "Tube rupture caused by corrosion, vibration or differential pressure",
                "Higher-pressure fluid enters the low-pressure side",
                "Leak detection; material inspection; pressure relief",
                4,
                2,
                "Historical heat-exchanger studies",
            ),
        ],
    )
    studies = database.execute("SELECT id FROM mvp_studies").fetchall()
    for study in studies:
        database.execute(
            """
            INSERT OR IGNORE INTO mvp_risk_matrix
                (study_id, low_max, medium_max, high_max)
            VALUES (?, 3, 7, 11)
            """,
            (study["id"],),
        )
    for study in studies:
        database.executemany(
            """
                INSERT OR IGNORE INTO mvp_sources
                    (id, study_id, title, source_type, reference, section_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
            [
                (
                    f"source-iec-61882-{study['id']}",
                    study["id"],
                    "IEC 61882:2016",
                    "Standard",
                    "Hazard and operability studies application guide",
                    42,
                ),
                (
                    f"source-iec-61511-{study['id']}",
                    study["id"],
                    "IEC 61511-1:2016",
                    "Standard",
                    "Functional safety for the process industry sector",
                    67,
                ),
            ],
        )


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
            ("study-reactor-2026", "Unit 200 HAZOP", "ACWA Power", "Konya", "in_review"),
            (
                "study-utility-2026",
                "Unit 400 Utilities HAZOP",
                "ACWA Power",
                "Konya",
                "draft",
            ),
            ("study-tank-2026", "Tank Farm LOPA Review", "SOCAR", "Aliaga", "in_review"),
        ],
    )

    nodes = [
        # study-reactor-2026
        (
            "node-t100",
            "study-reactor-2026",
            "N-01",
            "Feedstock Tank T-100",
            "Atmospheric tank",
            "Store feedstock within safe operating limits.",
            "complete",
        ),
        (
            "node-p101",
            "study-reactor-2026",
            "N-02",
            "Feed Pump P-101",
            "Centrifugal pump",
            "Provide continuous, controlled feed from feedstock tank T-100 to reactor R-201.",
            "active",
        ),
        (
            "node-e102",
            "study-reactor-2026",
            "N-03",
            "Heat Exchanger E-102",
            "Shell-and-tube heat exchanger",
            "Bring the feed temperature to reactor inlet conditions.",
            "review",
        ),
        (
            "node-r201",
            "study-reactor-2026",
            "N-04",
            "Reactor R-201",
            "Agitated reactor",
            "Maintain the reaction within its defined temperature and pressure envelope.",
            "review",
        ),
        (
            "node-v301",
            "study-reactor-2026",
            "N-05",
            "Separator V-301",
            "Pressure vessel",
            "Safely separate the gas and liquid phases.",
            "active",
        ),
        # study-utility-2026
        (
            "node-bfw",
            "study-utility-2026",
            "N-01",
            "Boiler Feedwater Pump P-401",
            "Centrifugal pump",
            "Provide continuous feedwater to the steam boiler.",
            "empty",
        ),
        (
            "node-deaer",
            "study-utility-2026",
            "N-02",
            "Deaerator D-401",
            "Pressure vessel",
            "Remove dissolved oxygen from the feedwater.",
            "empty",
        ),
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
        (
            "node-t100",
            "Fazla",
            "High level",
            "Level control valve LV-100 fails fully open and operator response is delayed",
            "Tank overflow, flammable liquid spill and environmental contamination",
            "High-level alarm LAH-100; independent LSHH-100 filling shutdown trip",
            4,
            2,
            "İncelendi",
        ),
        (
            "node-t100",
            "Diğer",
            "Vacuum (sub-atmospheric pressure)",
            "Vacuum breaker remains blocked during rapid draining",
            "Tank shell buckling and mechanical damage",
            "Vacuum breaker PVRV-100; periodic vacuum valve test",
            3,
            2,
            "İncelendi",
        ),
        (
            "node-t100",
            "Daha fazla",
            "High temperature",
            "Solar radiation and insufficient ventilation during summer conditions",
            "Evaporation loss and increased emissions through the breather valve",
            "White reflective coating; breather valve PVRV-100",
            2,
            3,
            "Taslak",
        ),
        # P-101 — Besleme pompası
        (
            "node-p101",
            "Yok",
            "No flow",
            "Isolation valve remains closed on the common suction header",
            "Loss of reactor feed and unplanned shutdown",
            "Low-flow alarm FAL-101; standby pump startup procedure",
            3,
            2,
            "İncelendi",
        ),
        (
            "node-p101",
            "Fazla",
            "High flow",
            "Control valve FV-101 fails fully open",
            "Reactor temperature rise and off-specification production",
            "High-flow alarm FAH-101; independent TSHH-204 trip",
            4,
            2,
            "Taslak",
        ),
        (
            "node-p101",
            "Ters",
            "Reverse flow",
            "Check valve leaks or remains open while the pump is stopped",
            "Tank overpressure and contamination",
            "Check valve maintenance program; motorized isolation valve",
            4,
            3,
            "Eksik",
        ),
        (
            "node-p101",
            "Az",
            "Low flow",
            "Partial suction strainer blockage or low tank level",
            "Pump cavitation and flammable fluid release",
            "Low tank level alarm LAL-100; vibration monitoring",
            3,
            3,
            "Taslak",
        ),
        # E-102 — Isı eşanjörü
        (
            "node-e102",
            "Daha fazla",
            "High temperature",
            "Steam control valve TV-102 fails fully open",
            "Excessive reactor inlet temperature triggers a runaway reaction",
            "High-temperature alarm TAH-102; independent TSHH-102 steam shutdown trip",
            4,
            3,
            "Eksik",
        ),
        (
            "node-e102",
            "Az",
            "Low temperature",
            "Loss of steam supply or blocked condensate drainage",
            "Reduced reaction yield and off-specification product",
            "Low-temperature alarm TAL-102",
            2,
            3,
            "Taslak",
        ),
        (
            "node-e102",
            "Parçası",
            "Tube leak / cross-contamination",
            "Corrosion perforation in the tube bundle",
            "Mixing of process fluid and heating medium",
            "Periodic tube thickness measurement; condensate conductivity monitoring",
            3,
            2,
            "İncelendi",
        ),
        # R-201 — Reaktör
        (
            "node-r201",
            "Daha fazla",
            "High pressure",
            "Uncontrolled reaction rate increase following cooling water loss",
            "Overpressure, vessel rupture and flammable cloud formation",
            "Relief valve PSV-201; emergency cooling and SIS pressure trip",
            5,
            3,
            "Eksik",
        ),
        (
            "node-r201",
            "Daha fazla",
            "High temperature (runaway)",
            "Reaction heat accumulates after agitator motor failure",
            "Uncontrolled exothermic reaction and thermal explosion",
            "Agitator stopped alarm; TSHH-201 SIS trip; emergency quench system",
            5,
            2,
            "Taslak",
        ),
        (
            "node-r201",
            "Yok",
            "No agitation",
            "Agitator coupling failure or drive motor power loss",
            "Localized hot spot and reaction instability",
            "Agitator speed monitoring; low-speed alarm",
            4,
            2,
            "Taslak",
        ),
        # V-301 — Ayırıcı
        (
            "node-v301",
            "Daha fazla",
            "High liquid level",
            "Level control valve LV-301 fails closed",
            "Liquid carryover to the gas outlet and downstream equipment damage",
            "High-level alarm LAH-301; LSHH-301 trip",
            3,
            3,
            "Taslak",
        ),
        (
            "node-v301",
            "Az",
            "Low liquid level",
            "Liquid drain valve fails open",
            "Gas blow-by and high-pressure gas flow downstream",
            "Low-level alarm LAL-301; drain line check valve",
            4,
            2,
            "İncelendi",
        ),
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
        lopa.append(
            (
                f"ipl-seed-{row_id}-a",
                row_id,
                "Independent high-high trip (SIS, SIL-2)",
                1.0e-2,
                1,
                "Annual proof test",
            )
        )
        if index % 2 == 0:
            lopa.append(
                (
                    f"ipl-seed-{row_id}-b",
                    row_id,
                    "Pressure relief valve (PSV) protection layer",
                    1.0e-2,
                    1,
                    "Removal and calibration every five years",
                )
            )
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
