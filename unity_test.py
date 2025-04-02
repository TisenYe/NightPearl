import sys
import time
import os
import glob
from utils import log
from assertpy import assert_that
from utils.config_parser import SingletonConfig

from core.android_device import AndroidDevice


def clean_log_file():
    log_files = glob.glob('*.log')

    for file_path in log_files:
        try:
            os.remove(file_path)
            log.debug(f"已删除文件: {file_path}")
        except Exception as e:
            print(f"删除 {file_path} 失败: {e}")

def test_connect():
    clean_log_file()
    client = AndroidDevice()
    client.connect("181E1E2510000080")
    print(client.shell("uptime"))
    client.health_check()

    client.__del__()

clean_log_file()
assert_that(30).is_equal_to(32)

config = SingletonConfig('config.cfg')
print(config.log.loglevel)