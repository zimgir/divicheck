import sys
import json
import logging
import contextlib
from datetime import datetime
from pathlib import Path
from db import LOGS_DIR


class _OriginFilter(logging.Filter):
    """Rewrite record.funcName to the first non-logging/non-logger frame."""

    def filter(self, record):
        frame = sys._getframe(1)
        while frame is not None:
            name = frame.f_globals.get("__name__", "")
            if name != "logging" and not name.startswith("logging.") and frame.f_code.co_filename != __file__:
                record.funcName = frame.f_code.co_name
                break
            frame = frame.f_back
        return True


class DBLogger:
    progress_path = None

    @staticmethod
    def get_logger(name: str = "db_cli", keep: int = 5):
        idx_file = LOGS_DIR / f"{name}.index"
        try:
            idx = int(idx_file.read_text().strip())
        except (OSError, ValueError):
            idx = 0
        n = idx % keep
        for old in LOGS_DIR.glob(f"{name}.{n}.*.log"):
            try:
                old.unlink()
            except OSError:
                pass
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = LOGS_DIR / f"{name}.{n}.{stamp}.log"
        idx_file.write_text(str((n + 1) % keep))

        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if logger.hasHandlers():
            logger.handlers.clear()

        handler = logging.FileHandler(log_file, mode="w")
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(funcName)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        handler.addFilter(_OriginFilter())
        logger.addHandler(handler)
        return logger


    @staticmethod
    def print_progress(current: int, total: int, msg: str = ""):
        print(f"Progress: {current}/{total} ({current / total:.2%}) {msg}".rstrip())
        if DBLogger.progress_path is None:
            return
        percent = round(current / total * 100, 1) if total else 0
        path = Path(DBLogger.progress_path)
        tmp = path.with_suffix(path.suffix + ".tmp")
        payload = {"percent": percent, "cur": current, "total": total, "msg": msg}
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(payload))
            tmp.replace(path)
        except OSError:
            pass


class LoggerStream:
    def __init__(self, logger, original_stream, is_error=False):
        self.logger = logger
        self.orig = original_stream
        self.is_error = is_error

    def write(self, msg):
        self.orig.write(msg)
        for line in msg.splitlines():
            clean = line.strip()
            if clean:
                if self.is_error:
                    self.logger.error(clean)
                else:
                    self.logger.info(clean)

    def flush(self):
        self.orig.flush()



@contextlib.contextmanager
def log_streams_to(logger):
    with contextlib.redirect_stdout(LoggerStream(logger, sys.stdout, is_error=False)), \
         contextlib.redirect_stderr(LoggerStream(logger, sys.stderr, is_error=True)):
        yield
