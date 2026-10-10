import sys
from pathlib import Path
from db import LOGS_DIR
from db.logger import DBLogger, log_streams_to


def _emit():
    print("hello from emit")
    print("bad thing", file=sys.stderr)


def _cleanup(name):
    for f in LOGS_DIR.glob(f"{name}.*.log"):
        f.unlink()
    (LOGS_DIR / f"{name}.index").unlink(missing_ok=True)


def test_log_streams_funcname():
    name = "pytest_funcname"
    logger = DBLogger.get_logger(name, keep=5)
    with log_streams_to(logger):
        _emit()
    for h in logger.handlers:
        h.flush()
    text = Path(logger.handlers[0].baseFilename).read_text()
    assert "[_emit]" in text
    assert "hello from emit" in text
    assert "bad thing" in text
    _cleanup(name)


def test_rotation_keeps_five():
    name = "pytest_rot"
    for _ in range(6):
        DBLogger.get_logger(name, keep=5)
    assert len(list(LOGS_DIR.glob(f"{name}.*.log"))) == 5
    assert 0 <= int((LOGS_DIR / f"{name}.index").read_text()) < 5
    _cleanup(name)
