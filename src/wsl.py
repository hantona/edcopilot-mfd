import platform
import subprocess


def running_on_wsl():
    """Returns true if running in the WSL Linux subsystem on Windows"""
    wsl = False
    if platform.system() == "Linux":
        wsl_info = subprocess.run(["wslinfo", "--version"])
        wsl = wsl_info.returncode == 0

    return wsl