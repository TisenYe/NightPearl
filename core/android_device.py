import time
from utils import log
import threading
import os
import re
from datetime import datetime
from adbutils import AdbClient

class AndroidDevice:
    def __init__(self, device_name=None, device_type=None):
        self.device_type = device_type
        self.device_name = device_name
        self.status = "offline"
        self.connected = False
        self.device = None
        self.save_collect_log_dir = "./"
        self.stop_log_event = threading.Event()

    def shell(self, cmd, display=True):
        ret = -1
        if self.device != None and self.connected:
            ret = self.device.shell(cmd)
            if display:
                log.info(ret)
        else:
            log.error("Device not connected, cant run shell command")
        return ret

    def connect(self, device_name=None, host="127.0.0.1", port=5037):
        client = AdbClient(host, port)
        retry = 6
        wait_time = 10

        if device_name == None:
            if self.device_name != None:
                device_name = self.device_name
            else:
                log.error("Need device name to conect")
                return -1
        if self.device_name == None:
            self.device_name = device_name

        log.info("start connect {}", device_name)
        while retry > 0:
            try:
                self.device = client.device(device_name)
                if self.device == None:
                    raise Exception("Device not found")

                self.start_collect_log()
            except Exception as e:
                log.error(e)
                time.sleep(wait_time)
                retry -= 1
            else:
                break

        log.info("Connected to device {}", device_name)
        self.connected = True
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
                while not self.stop_log_event.is_set():
                    line = output.readline().strip()
                    if line:
                        f.write(line + "\n")
        except Exception as e:
            log.error(f"recordlog thread error: {e}")
            self.stop_log_event.set()

    def _record_dmesg_history(self, save_log_file):
        try:
            dmesg_output = self.device.shell("dmesg").strip()
            if dmesg_output:
                with open(save_log_file, 'a') as f:
                    f.write(dmesg_output + "\n")
        except Exception as e:
            log.error(f"Failed to get dmesg history: {e}")

    def _generate_log_filename(self, dir="./"):
        safe_device_name = re.sub(r'[^\w\-_.]', '_', self.device_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = dir
        os.makedirs(log_dir, exist_ok=True)
        dmesg_file = f"{safe_device_name}_dmesg_{timestamp}.log"
        dmesg_history_file = f"{safe_device_name}_dmesg_history_{timestamp}.log"
        logcat_file = f"{safe_device_name}_logcat_{timestamp}.log"
        self.dmesg_file = os.path.join(log_dir, dmesg_file)
        self.dmesg_history_file = os.path.join(log_dir, dmesg_history_file)
        self.logcat_file = os.path.join(log_dir, logcat_file)
        log.debug(self.dmesg_file)
        log.debug(self.dmesg_history_file)
        log.debug(self.logcat_file)

    # TODO 串口日志也需要添加.
    def start_collect_log(self):
        self._generate_log_filename(self.save_collect_log_dir)
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

        def _event_loop():
            try:
                while not self.stop_log_event.is_set():
                    time.sleep(0.5)
            except KeyboardInterrupt:
                self.stop_log_event.set()
        event_thread = threading.Thread(target=_event_loop, daemon=True)
        event_thread.start()

    def __del__(self):
         if not self.stop_log_event.is_set():
            self.stop_log_event.set()
