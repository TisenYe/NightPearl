import sys
from pathlib import Path
root_dir = Path(__file__).absolute()
sys.path.append(str(root_dir))

from core.android_device import AndroidDevice


client = AndroidDevice()
device = client.connect("181E1E2510000086")
print(device.shell("ls"))
