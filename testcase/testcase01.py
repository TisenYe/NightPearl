from core.base_testcase import BaseTestCase
from assertpy import assert_that
from nightpearl import log

class UnitTest(BaseTestCase):

    def add(self, a, b):
        return a + b

    def start_run(self):
        device = self.client
        device.connect()
        device.shell("uptime")

        assert_that((self.add(1, 30))).is_equal_to(31)
        return 0

    def teardown(self):
        return super().teardown()