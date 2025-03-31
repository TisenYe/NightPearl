import time
import util.log as log
from ppadb.client import Client as AdbClient

class AndroidDevice:
    def __init__(self, device_name=None, device_type=None):
        self.device_type = device_type
        self.device_name = device_name
        self.status = "offline"
        self.connected = False
        self.device = None

    def connect(self, device_name=None, host="127.0.0.1", port=5037):
        client = AdbClient(host, port)
        retry = 6
        wait_time = 10

        if device_name != None:
            log.info("start connect {}", device_name)
            while retry > 0:
                try:
                    self.device = client.device(device_name)
                    if self.device == None:
                        raise Exception("Device not found")
                except Exception as e:
                    time.sleep(wait_time)
                    retry -= 1
                else:
                    break

        else:
            log.error("Need device name or device id to conect")
            return -1

        log.info("Connected to device {}", device_name)
        self.connect = True
        return self.device