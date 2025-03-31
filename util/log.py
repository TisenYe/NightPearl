import sys
from loguru import logger

# "DEBUG" "INFO" "ERROR"
level="DEBUG"

# 重定向标准输出到日志,即printk内容在日志中也显示
class StreamToLogger:
    def __init__(self, level=level):
        self.level = level

    def write(self, message):
        if message.strip():
            logger.log(self.level, message.strip())

    def flush(self):
        pass

sys.stdout = StreamToLogger(level="INFO")
sys.stderr = StreamToLogger(level="ERROR")

logger.add(
    "runtime_{time}.log", 
    rotation="100 MB",  # 按大小轮转
    retention="20 days",  # 保留7天
    level=level,
    enqueue=True,        # 多进程安全
    backtrace=True       # 异常堆栈追踪
)
def debug(*str):
    logger.debug(*str)

def info(*str):
    logger.info(*str)

def error(*str):
    logger.error(*str)
