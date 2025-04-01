from core.android_device import AndroidDevice  # 导入自定义设备模块
from utils import log
from nightpearl import config
import configparser

class BaseTestCase():
    """所有测试用例的基类，提供统一初始化和资源管理"""

    @classmethod
    def setUpClass(cls):
        """类级别初始化（所有测试方法执行前只运行一次）"""
        log.debug("===== 测试类初始化完成 =====")

    def setup(self):
        """方法级别初始化（每个测试方法执行前运行）"""
        pass

    def start_run(self, test_data):
        """通用测试执行逻辑（可被子类覆盖或复用）"""
        pass

    def teardown(self):
        """方法级别清理（每个测试方法执行后运行）"""
        pass

    @classmethod
    def tearDownClass(cls):
        """类级别清理（所有测试方法执行后只运行一次）"""
        log.info("===== 测试类资源释放完成 =====")

    def __init__(self):
        self.__class__.setUpClass() 

    def __del__(self):
        self.__class__.tearDownClass() 