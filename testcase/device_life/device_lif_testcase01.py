from core.base_testcase import BaseTestCase
from core.android_device import AndroidDevice
from assertpy import assert_that
from nightpearl import log

class UnitTest(BaseTestCase):

    def add(self, a, b):
        return a + b
    
    def start_run(self):
        device = AndroidDevice()
        device.connect()
        device.reboot()
        device.shell("uptime")

        return 0

    def teardown(self):
        
        return super().teardown()