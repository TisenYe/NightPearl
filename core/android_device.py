import time
import threading
import os
import sys
import re
from datetime import datetime
from adbutils import AdbClient
from nightpearl import global_config
from nightpearl import log

class AndroidDevice:
    def __init__(self, device_name=None, log_dir=None):
        self.global_config = global_config
        self.host = self.global_config.device.host
        self.port = self.global_config.device.port
        self.log_dir = self.global_config.log.log_dir
        self.device_name =  self.global_config.device.device_name
        self.connected = False
        self.device = None
        self.heartbeat_interval = 3  # 心跳间隔秒数
        self.heartbeat_thread = None
        self.heartbeat_living = threading.Event()

    def _heartbeat_checker(self):
        retry = 3
        while not self.heartbeat_living.is_set():
            try:
                if self.device and self.device.get_state() == "device":
                    time.sleep(self.heartbeat_interval)
                    break
                else:
                    retry -= 1
                    continue
            except Exception as e:
                retry -= 1
                log.warn(f"{self.device_name} device heartbeat lost ({retry}): {str(e)}")
            if retry == 0:
                self.heartbeat_living.set()
                self.connected = False
                log.error(f"{self.device_name} device not living")
                break

    def shell(self, cmd, display=True):
        ret = -1
        if self.device != None and self.connected:
            ret = self.device.shell(cmd)
            if display:
                log.info(ret)
        else:
            log.error("Device not connected, cant run shell command")
        return ret

    def connect(self, device_name=None, host=None, port=None):
        client = AdbClient(host, port)
        retry = 6
        wait_time = 10
        device_name = device_name or self.device_name
        if device_name == None:
                log.warn("Need device name to conect")
                return -1

        log.info("Start connect to device {}", device_name)
        while retry > 0:
            try:
                self.device = client.device(device_name)
                self.device.root()
                if self.device.get_state() == "device":
                    break
                else:
                    raise Exception("Device not found")
            except Exception as e:
                time.sleep(wait_time)
                retry -= 1
        if (retry <= 0):
            log.error("Connected to device failed")
            return None

        log.info("Connected to device {}", device_name)
        self.start_collect_log()
        self.connected = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_checker,
            name="DeviceHeartbeat",
            daemon=True
        )
        self.heartbeat_thread.start()
        return self.device

    # 注意:重启之后是新的连接对象
    def reboot(self, mode=None): # mode = "bootloader" or "recovery"
        if self.device != None and self.connected:
            log.info("Rebooting device")
            self.device.shell("reboot {mode}")
            time.sleep(10)
            self.connect()
            return self.device
        else:
            log.error("Need device to reboot")
            return None

    def health_check(self,):
        if not self.connected:
            log.error("No device connected, cant check health")
            return False
        ret = True
        boot_completed = self.device.shell("dmesg | grep 'Boot com'")
        if boot_completed == "":
            ret = False
        if ret == True:
            log.info("Health check is OK")
        else:
            log.error("Health check failed")
        return ret

    def _record_log_worker(self, save_log_file, log_from):
        try:
            with open(save_log_file, 'a', buffering=100) as f:
                stream = self.device.shell(log_from, stream=True)
                output = stream.conn.makefile()
                while not self.heartbeat_living.is_set():
                    line = output.readline().strip()
                    if line:
                        f.write(line + "\n")
        except Exception as e:
            log.error(f"{log_from} recordlog thread error: {e}")
            self.heartbeat_living.set()

    def _record_dmesg_history(self, save_log_file):
        try:
            dmesg_output = self.device.shell("dmesg").strip()
            if dmesg_output:
                with open(save_log_file, 'a') as f:
                    f.write(dmesg_output + "\n")
        except Exception as e:
            log.error(f"dmesg recordlog thread error: {e}")
            self.heartbeat_living.set()

    def _generate_log_filename(self, log_dir):
        safe_device_name = re.sub(r'[^\w\-_.]', '_', self.device_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join(log_dir, self.global_config.get_exec_case_name())
        os.makedirs(log_dir, exist_ok=True)

        logcat_file = f"{safe_device_name}_logcat_{timestamp}.log"
        dmesg_file = f"{safe_device_name}_dmesg_{timestamp}.log"
        dmesg_history_file = f"{safe_device_name}_dmesg_history_{timestamp}.log"

        self.logcat_file = os.path.join(log_dir, logcat_file)
        self.dmesg_file = os.path.join(log_dir, dmesg_file)
        self.dmesg_history_file = os.path.join(log_dir, dmesg_history_file)

    # TODO 串口日志也需要添加.
    def start_collect_log(self):
        self._generate_log_filename(self.log_dir)
        dmesg_thread = threading.Thread(
            target=self._record_log_worker,
            args=(self.dmesg_file, "cat /proc/kmsg")
        )
        logcat_thread = threading.Thread(
            target=self._record_log_worker,
            args=(self.logcat_file, "logcat")
        )
        logcat_thread.start()
        dmesg_thread.start()
        self._record_dmesg_history(self.dmesg_history_file)

    def __del__(self):
         if not self.heartbeat_living.is_set():
            self.heartbeat_living.set()
