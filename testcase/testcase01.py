from core.base_testcase import BaseTestCase
from assertpy import assert_that
from utils import log

class UnitTest(BaseTestCase):
    """登录功能测试用例"""

    def add(self, a, b):
        return a + b
    
    def start_run(self):
        # 直接调用核心模块方法
        print(self.add(1, 30))
        pass

    def test_failed_login(self):
        # 测试异常场景
        pass