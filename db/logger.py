import sys
import logging
import contextlib
from db import LOGS_DIR


class DBLogger:
    @staticmethod
    def get_logger(name: str, reset: bool = True):
        log_file = LOGS_DIR / f"{name}.log"
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if logger.hasHandlers():
            logger.handlers.clear()

        handler = logging.FileHandler(log_file, mode="w" if reset else "a")
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


    @staticmethod
    def print_progress(current: int, total: int):
        print(f"Progress: {current}/{total} ({current / total:.2%})")


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
