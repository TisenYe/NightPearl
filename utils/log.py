import sys
import os
from loguru import logger
from contextlib import contextmanager
from typing import Optional

class LoggerManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger()
        return cls._instance

    def _init_logger(self):
        self._current_case = "."
        self._file_handler_id: Optional[int] = None
        '''
        self._console_handler_id = logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
            level="DEBUG",
            enqueue=True,
            colorize=True
        )
        '''
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self.loglevel = "INFO"
        self.rotation = "100 MB"
        self.retention = "7 day"
        self.log_dir = "./"



    def set_case_name(self, case_name: str):
        if self._file_handler_id is not None:
            logger.remove(self._file_handler_id)
        self._current_case = case_name
        case_log_dir = os.path.join(self.log_dir, case_name)
        os.makedirs(case_log_dir, exist_ok=True)
        self._file_handler_id = logger.add(
            f"{case_log_dir}/runtime.log",
            rotation=self.rotation,
            retention=self.retention,
            level=self.loglevel,
            enqueue=True,
            backtrace=True,
            encoding="utf-8"
        )

        # 重定向标准输出
        sys.stdout = self._create_stream_handler("INFO")
        sys.stderr = self._create_stream_handler("ERROR")

    def _create_stream_handler(self, level: str):
        """创建标准流重定向处理器"""
        class StreamRedirector:
            def __init__(self, level):
                self.level = level
            def write(self, message):
                if message.strip():
                    logger.log(self.level, message.strip())
            def flush(self): pass
        return StreamRedirector(level)

    def restore_std_streams(self):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

    @contextmanager
    def case_context(self, case_name: str):
        prev_case = self._current_case
        self.set_case_name(case_name)
        try:
            yield
        finally:
            self.set_case_name(prev_case)

    @staticmethod
    def debug(*args):
        logger.debug(*args)

    @staticmethod
    def info(*args):
        logger.info(*args)

    @staticmethod 
    def error(*args):
        logger.error(*args)
