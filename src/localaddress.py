import subprocess

from wsl import running_on_wsl


def get_local_ip_address():
    """Returns the local IP address"""
    local_address = "127.0.0.1"
    if running_on_wsl():
        # WSL is in a VM, so it has a different local network interface
        # The host and the WSL VM share the same hostname, so connecting by hostname also connects to the VM
        # Use the first active physical interface that has an IPv4 address
        active_interfaces = subprocess.check_output(['powershell.exe', '-Command',
                                                     'Get-NetAdapter -Name * -Physical | Where-Object { $_.Status -eq "Up" } | Select-Object -ExpandProperty Name']).decode().splitlines()

        for active_interface in active_interfaces:
            ip_addresses = subprocess.check_output(['powershell.exe', '-Command',
                                                    'Get-NetIPAddress -InterfaceAlias "' + active_interface + '" -AddressFamily IPv4 | Select-Object -ExpandProperty IPAddress'
                                                    ]).decode().splitlines()
            if ip_addresses:
                local_address = ip_addresses[0]
                break

    return local_address