"""System control utilities for Windows."""
import subprocess


# Cache the pycaw volume interface so we don't re-create it on every call
_volume_interface = None


def _get_volume_interface():
    """Get or create the cached IAudioEndpointVolume interface."""
    global _volume_interface
    if _volume_interface is None:
        from pycaw.pycaw import AudioUtilities
        speakers = AudioUtilities.GetSpeakers()
        _volume_interface = speakers.EndpointVolume
    return _volume_interface


class SystemControl:
    """Provides static methods to control Windows system settings."""

    @staticmethod
    def get_volume() -> int:
        """Get current system volume (0-100)."""
        try:
            volume = _get_volume_interface()
            return int(volume.GetMasterVolumeLevelScalar() * 100)
        except Exception:
            return 50

    @staticmethod
    def set_volume(value: int) -> None:
        """Set system volume (0-100)."""
        try:
            volume = _get_volume_interface()
            volume.SetMasterVolumeLevelScalar(max(0, min(100, value)) / 100.0, None)
        except Exception as e:
            print(f"Failed to set volume: {e}")

    @staticmethod
    def get_brightness() -> int:
        """Get current screen brightness (0-100)."""
        try:
            import screen_brightness_control as sbc
            brightness = sbc.get_brightness()
            if isinstance(brightness, list):
                return brightness[0] if brightness else 50
            return brightness
        except Exception:
            return 50

    @staticmethod
    def set_brightness(value: int) -> None:
        """Set screen brightness (0-100)."""
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(max(0, min(100, value)))
        except Exception as e:
            print(f"Failed to set brightness: {e}")

    @staticmethod
    def get_wifi_status() -> dict:
        """Get current Wi-Fi connection status.

        Returns:
            dict with keys: "connected" (bool), "network" (str), "signal" (str)
        """
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout
            connected = False
            network = ""
            signal = ""
            for line in output.split("\n"):
                line = line.strip()
                if "State" in line and "connected" in line.lower():
                    connected = "disconnected" not in line.lower()
                elif "SSID" in line and "BSSID" not in line:
                    network = line.split(":", 1)[1].strip() if ":" in line else ""
                elif "Signal" in line:
                    signal = line.split(":", 1)[1].strip() if ":" in line else ""
            return {"connected": connected, "network": network, "signal": signal}
        except Exception:
            return {"connected": False, "network": "", "signal": ""}

    @staticmethod
    def get_available_networks() -> list:
        """Get list of available Wi-Fi networks.

        Returns:
            list of dicts with keys: "name" (str), "signal" (str), "security" (str)
        """
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks"],
                capture_output=True, text=True, timeout=10
            )
            networks = []
            current = {}
            for line in result.stdout.split("\n"):
                line = line.strip()
                if "SSID" in line and "BSSID" not in line:
                    if current.get("name"):
                        networks.append(current)
                    name = line.split(":", 1)[1].strip() if ":" in line else ""
                    current = {"name": name, "signal": "", "security": ""}
                elif "Signal" in line:
                    current["signal"] = line.split(":", 1)[1].strip() if ":" in line else ""
                elif "Authentication" in line:
                    current["security"] = line.split(":", 1)[1].strip() if ":" in line else ""
            if current.get("name"):
                networks.append(current)
            return networks
        except Exception:
            return []

    @staticmethod
    def connect_wifi(network_name: str) -> bool:
        """Connect to a saved Wi-Fi network."""
        try:
            result = subprocess.run(
                ["netsh", "wlan", "connect", f"name={network_name}"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def is_wifi_enabled() -> bool:
        """Check if the Wi-Fi adapter is enabled."""
        try:
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split("\n"):
                if "Wi-Fi" in line or "Wireless" in line or "WLAN" in line:
                    return "Connected" in line or "Disconnected" in line
            return False
        except Exception:
            return False

    @staticmethod
    def set_wifi_enabled(enabled: bool) -> tuple[bool, str]:
        """Enable or disable the Wi-Fi adapter.
        
        Returns: (success: bool, message: str)
        Note: May require admin privileges.
        """
        action = "enable" if enabled else "disable"
        # Try common adapter names
        adapter_names = ["Wi-Fi", "Wireless Network Connection", "WLAN"]
        
        for name in adapter_names:
            try:
                result = subprocess.run(
                    ["netsh", "interface", "set", "interface", name, f"admin={action}"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return True, f"Wi-Fi {action}d successfully"
            except Exception:
                continue
        
        # Fallback: try PowerShell
        try:
            ps_action = "Enable" if enabled else "Disable"
            result = subprocess.run(
                ["powershell", "-Command",
                 f"Get-NetAdapter -Name '*Wi*','*Wireless*','*WLAN*' | "
                 f"{ps_action}-NetAdapter -Confirm:$false"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True, f"Wi-Fi {action}d successfully"
            else:
                return False, f"Failed: may need admin rights. {result.stderr.strip()}"
        except Exception as e:
            return False, f"Could not {action} Wi-Fi: {e}"

    # ------------------------------------------------------------------
    # Bluetooth
    # ------------------------------------------------------------------

    @staticmethod
    def is_bluetooth_enabled() -> bool:
        """Check if Bluetooth is enabled."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-PnpDevice -Class Bluetooth | "
                 "Where-Object {$_.FriendlyName -like '*Bluetooth*Radio*' -or "
                 "$_.FriendlyName -like '*Bluetooth*Adapter*' -or "
                 "$_.FriendlyName -eq 'Bluetooth'} | "
                 "Select-Object -First 1 -ExpandProperty Status"],
                capture_output=True, text=True, timeout=10
            )
            status = result.stdout.strip()
            return status.lower() == "ok"
        except Exception:
            return False

    @staticmethod
    def set_bluetooth_enabled(enabled: bool) -> tuple[bool, str]:
        """Enable or disable Bluetooth.
        
        Returns: (success: bool, message: str)
        Note: May require admin privileges.
        """
        action = "Enable" if enabled else "Disable"
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 f"Get-PnpDevice -Class Bluetooth | "
                 f"Where-Object {{$_.FriendlyName -like '*Bluetooth*Radio*' -or "
                 f"$_.FriendlyName -like '*Bluetooth*Adapter*' -or "
                 f"$_.FriendlyName -eq 'Bluetooth'}} | "
                 f"{action}-PnpDevice -Confirm:$false"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                return True, f"Bluetooth {action.lower()}d"
            else:
                return False, f"Failed: may need admin rights. {result.stderr.strip()}"
        except Exception as e:
            return False, f"Could not toggle Bluetooth: {e}"

    @staticmethod
    def get_bluetooth_devices() -> list[dict]:
        """Get list of paired/connected Bluetooth devices.
        
        Returns: list of {"name": str, "status": str, "type": str}
        """
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-PnpDevice -Class Bluetooth | "
                 "Where-Object {$_.FriendlyName -notlike '*Radio*' -and "
                 "$_.FriendlyName -notlike '*Adapter*' -and "
                 "$_.FriendlyName -ne 'Bluetooth' -and "
                 "$_.FriendlyName -notlike '*Enumerator*' -and "
                 "$_.FriendlyName -notlike '*Microsoft*'} | "
                 "Select-Object FriendlyName, Status | "
                 "ConvertTo-Json"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0 or not result.stdout.strip():
                return []

            import json
            data = json.loads(result.stdout)
            # PowerShell returns a single object (not array) if only 1 result
            if isinstance(data, dict):
                data = [data]
            
            devices = []
            for item in data:
                name = item.get("FriendlyName", "Unknown")
                status = item.get("Status", "Unknown")
                devices.append({
                    "name": name,
                    "status": "Connected" if status.lower() == "ok" else "Paired",
                    "type": "bluetooth",
                })
            return devices
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Power
    # ------------------------------------------------------------------

    @staticmethod
    def shutdown() -> None:
        """Shutdown the computer."""
        subprocess.run(["shutdown", "/s", "/t", "0"])

    @staticmethod
    def restart() -> None:
        """Restart the computer."""
        subprocess.run(["shutdown", "/r", "/t", "0"])

    @staticmethod
    def sleep() -> None:
        """Put the computer to sleep."""
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])

    @staticmethod
    def lock_screen() -> None:
        """Lock the screen."""
        import ctypes
        ctypes.windll.user32.LockWorkStation()

