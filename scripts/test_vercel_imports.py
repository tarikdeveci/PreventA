"""Simulate Vercel environment: block sqlalchemy, pgvector, asyncpg imports."""
import builtins
import os
import sys

os.environ["VERCEL"] = "1"

BLOCKED = {"sqlalchemy", "pgvector", "asyncpg"}

_real_import = builtins.__import__


def _mock_import(name, *args, **kwargs):
    top = name.split(".")[0]
    if top in BLOCKED:
        raise ImportError(f"Simulated: No module named '{name}'")
    return _real_import(name, *args, **kwargs)


builtins.__import__ = _mock_import

sys.path.insert(0, "src")

try:
    from preventa.main import app  # noqa: E402

    routes = [r.path for r in app.routes]
    print("[OK] SUCCESS - app loaded without sqlalchemy/pgvector/asyncpg")
    print(f"   Routes ({len(routes)}):")
    for r in routes:
        print(f"     {r}")
except Exception as exc:
    print(f"[FAIL] {type(exc).__name__}: {exc}")
    import traceback

    traceback.print_exc()
finally:
    builtins.__import__ = _real_import
