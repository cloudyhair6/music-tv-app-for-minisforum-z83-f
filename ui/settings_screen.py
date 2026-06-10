"""Settings screen with grouped audio, display, network, and system settings."""

from __future__ import annotations

import platform
import socket

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QMessageBox,
)

from styles.theme import Colors, Sizes
from ui.components import SliderSetting, ToggleSetting
from backend.system_control import SystemControl


class _SectionHeader(QLabel):
    """Styled section header for settings groups."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(
            f"font-size: {Sizes.FONT_H3}px; "
            f"font-weight: 600; "
            f"color: {Colors.TEXT_SECONDARY}; "
            f"padding-top: {Sizes.SPACING}px; "
            f"padding-bottom: {Sizes.SPACING_SM}px; "
            f"background: transparent;"
        )


class _InfoRow(QFrame):
    """Read-only label pair for system info."""

    def __init__(
        self, label: str, value: str, parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"background: {Colors.BG_CARD}; "
            f"border-radius: {Sizes.CARD_RADIUS_SM}px; "
            f"padding: {Sizes.SPACING_SM}px {Sizes.SPACING}px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            Sizes.SPACING, Sizes.SPACING_SM,
            Sizes.SPACING, Sizes.SPACING_SM,
        )
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"font-size: {Sizes.FONT_BODY}px; "
            f"color: {Colors.TEXT_SECONDARY}; "
            f"background: transparent;"
        )
        layout.addWidget(lbl)
        layout.addStretch()
        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"font-size: {Sizes.FONT_BODY}px; "
            f"color: {Colors.TEXT_PRIMARY}; "
            f"font-weight: 500; "
            f"background: transparent;"
        )
        layout.addWidget(self._val)

    def set_value(self, text: str) -> None:
        self._val.setText(text)


class _DeviceRow(QFrame):
    """A row showing a Bluetooth device."""

    def __init__(
        self, name: str, status: str, parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"background: {Colors.BG_CARD}; "
            f"border-radius: {Sizes.CARD_RADIUS_SM}px; "
            f"padding: 4px {Sizes.SPACING}px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            Sizes.SPACING, Sizes.SPACING_SM,
            Sizes.SPACING, Sizes.SPACING_SM,
        )

        icon = QLabel("🔵")
        icon.setStyleSheet("font-size: 18px; background: transparent;")
        layout.addWidget(icon)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"font-size: {Sizes.FONT_BODY}px; "
            f"color: {Colors.TEXT_PRIMARY}; "
            f"background: transparent; margin-left: 8px;"
        )
        layout.addWidget(name_lbl)
        layout.addStretch()

        status_color = Colors.SUCCESS if "Connected" in status else Colors.TEXT_SECONDARY
        status_lbl = QLabel(status)
        status_lbl.setStyleSheet(
            f"font-size: {Sizes.FONT_SMALL}px; "
            f"color: {status_color}; "
            f"background: transparent;"
        )
        layout.addWidget(status_lbl)


class SettingsScreen(QWidget):
    """System settings panel with live controls."""

    go_back = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsScreen")
        self._bt_device_rows: list[_DeviceRow] = []
        self._setup_ui()
        self._load_initial_values()

    # ------------------------------------------------------------------ UI
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(
            Sizes.SPACING_LG, Sizes.SPACING_LG,
            Sizes.SPACING_LG, Sizes.SPACING_LG,
        )
        root.setSpacing(Sizes.SPACING)

        # ---- header
        header = QHBoxLayout()
        header.setSpacing(Sizes.SPACING)

        back_btn = QPushButton("←  Back")
        back_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(
            f"QPushButton {{ "
            f"  background: {Colors.BG_TERTIARY}; "
            f"  color: {Colors.TEXT_PRIMARY}; "
            f"  border: none; "
            f"  border-radius: {Sizes.BUTTON_RADIUS}px; "
            f"  padding: 10px 20px; "
            f"  font-size: {Sizes.FONT_BODY}px; "
            f"}} "
            f"QPushButton:hover {{ background: {Colors.BG_CARD_HOVER}; }} "
            f"QPushButton:focus {{ border: 2px solid {Colors.ACCENT}; }}"
        )
        back_btn.clicked.connect(self.go_back.emit)
        header.addWidget(back_btn)

        title = QLabel("Settings")
        title.setStyleSheet(
            f"font-size: {Sizes.FONT_H1}px; "
            f"font-weight: 700; "
            f"color: {Colors.TEXT_PRIMARY}; "
            f"background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        # ---- scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; } "
            "QScrollBar:vertical { width: 6px; background: transparent; } "
            f"QScrollBar::handle:vertical {{ "
            f"  background: {Colors.TEXT_MUTED}; border-radius: 3px; "
            f"}} "
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical "
            "{ height: 0; }"
        )

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(Sizes.SPACING_SM)

        # ---------- Section: Audio & Display
        self._content_layout.addWidget(_SectionHeader("Audio & Display"))

        self._volume_slider = SliderSetting(
            label="Volume",
            icon_char="🔊",
            min_val=0,
            max_val=100,
            value=50,
            parent=content,
        )
        self._volume_slider.value_changed.connect(
            lambda v: SystemControl.set_volume(v),
        )
        self._content_layout.addWidget(self._volume_slider)

        self._brightness_slider = SliderSetting(
            label="Brightness",
            icon_char="🔆",
            min_val=0,
            max_val=100,
            value=50,
            parent=content,
        )
        self._brightness_slider.value_changed.connect(
            lambda v: SystemControl.set_brightness(v),
        )
        self._content_layout.addWidget(self._brightness_slider)

        self._content_layout.addSpacing(Sizes.SPACING_LG)

        # ---------- Section: Network
        self._content_layout.addWidget(_SectionHeader("Network"))

        self._wifi_toggle = ToggleSetting(
            label="Wi-Fi",
            icon_char="📶",
            is_on=False,
            status_text="Checking…",
            parent=content,
        )
        self._wifi_toggle.toggled.connect(self._on_wifi_toggled)
        self._content_layout.addWidget(self._wifi_toggle)

        # Network info label
        self._network_list_label = QLabel()
        self._network_list_label.setWordWrap(True)
        self._network_list_label.setStyleSheet(
            f"font-size: {Sizes.FONT_SMALL}px; "
            f"color: {Colors.TEXT_SECONDARY}; "
            f"padding: {Sizes.SPACING_SM}px {Sizes.SPACING}px; "
            f"background: transparent;"
        )
        self._network_list_label.setVisible(False)
        self._content_layout.addWidget(self._network_list_label)

        self._content_layout.addSpacing(Sizes.SPACING_LG)

        # ---------- Section: Bluetooth
        self._content_layout.addWidget(_SectionHeader("Bluetooth"))

        self._bt_toggle = ToggleSetting(
            label="Bluetooth",
            icon_char="🔵",
            is_on=False,
            status_text="Checking…",
            parent=content,
        )
        self._bt_toggle.toggled.connect(self._on_bluetooth_toggled)
        self._content_layout.addWidget(self._bt_toggle)

        # Bluetooth devices list container
        self._bt_devices_container = QVBoxLayout()
        self._bt_devices_container.setSpacing(Sizes.SPACING_SM)
        self._content_layout.addLayout(self._bt_devices_container)

        self._bt_status_label = QLabel()
        self._bt_status_label.setWordWrap(True)
        self._bt_status_label.setStyleSheet(
            f"font-size: {Sizes.FONT_SMALL}px; "
            f"color: {Colors.TEXT_SECONDARY}; "
            f"padding: {Sizes.SPACING_SM}px {Sizes.SPACING}px; "
            f"background: transparent;"
        )
        self._bt_status_label.setVisible(False)
        self._content_layout.addWidget(self._bt_status_label)

        self._content_layout.addSpacing(Sizes.SPACING_LG)

        # ---------- Section: Remote Control
        self._content_layout.addWidget(_SectionHeader("Remote Control"))

        self._remote_info = _InfoRow("Kindle Remote URL", "Starting…", content)
        self._content_layout.addWidget(self._remote_info)

        self._content_layout.addSpacing(Sizes.SPACING_LG)

        # ---------- Section: System
        self._content_layout.addWidget(_SectionHeader("System"))

        os_version = f"{platform.system()} {platform.release()} ({platform.version()})"
        hostname = socket.gethostname()

        self._content_layout.addWidget(
            _InfoRow("Operating System", os_version, content),
        )
        self._content_layout.addWidget(
            _InfoRow("Hostname", hostname, content),
        )
        self._content_layout.addWidget(
            _InfoRow("Python", platform.python_version(), content),
        )

        # Version info
        try:
            from backend.updater import get_local_version
            ver = get_local_version()
        except Exception:
            ver = "unknown"
        self._content_layout.addWidget(
            _InfoRow("App Version", ver, content),
        )

        self._content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def set_remote_url(self, url: str) -> None:
        """Update the remote control URL display."""
        self._remote_info.set_value(url)

    # ----------------------------------------------------- Initial data
    def _load_initial_values(self) -> None:
        """Fetch live values from SystemControl."""
        try:
            vol = SystemControl.get_volume()
            self._volume_slider.set_value(vol)
        except Exception:
            pass

        try:
            bright = SystemControl.get_brightness()
            self._brightness_slider.set_value(bright)
        except Exception:
            pass

        self._refresh_wifi_status()
        self._refresh_bluetooth_status()

    def _refresh_wifi_status(self) -> None:
        """Query current Wi-Fi state and update the toggle."""
        try:
            enabled = SystemControl.is_wifi_enabled()
            status = SystemControl.get_wifi_status()
            connected = status.get("connected", False)
            network = status.get("network", "")

            self._wifi_toggle.set_state(enabled)

            if connected and network:
                self._wifi_toggle.set_status_text(f"Connected to {network}")
            elif enabled:
                self._wifi_toggle.set_status_text("Enabled — not connected")
            else:
                self._wifi_toggle.set_status_text("Disabled")
        except Exception:
            self._wifi_toggle.set_status_text("Unavailable")

    def _on_wifi_toggled(self, is_on: bool) -> None:
        """Handle Wi-Fi toggle — actually enable/disable the adapter."""
        self._wifi_toggle.set_status_text("Applying…")

        # Actually toggle the Wi-Fi adapter
        success, message = SystemControl.set_wifi_enabled(is_on)

        if not success:
            # Show error message
            self._wifi_toggle.set_status_text(f"Error: {message}")
            self._network_list_label.setText(
                "⚠️ Wi-Fi toggle requires admin privileges.\n"
                "Try running MiniPC as Administrator."
            )
            self._network_list_label.setVisible(True)
            # Revert toggle state
            QTimer.singleShot(500, self._refresh_wifi_status)
            return

        # Wait a moment for the adapter to settle, then refresh
        QTimer.singleShot(2000, self._refresh_wifi_after_toggle)

    def _refresh_wifi_after_toggle(self) -> None:
        """Refresh Wi-Fi status after toggling."""
        self._refresh_wifi_status()

        # Show available networks if enabled
        if SystemControl.is_wifi_enabled():
            try:
                networks = SystemControl.get_available_networks()
                if networks:
                    text = "Available networks:\n" + "\n".join(
                        f"  •  {n['name']}  ({n.get('signal', '')})"
                        if isinstance(n, dict) else f"  •  {n}"
                        for n in networks[:10]
                    )
                    self._network_list_label.setText(text)
                    self._network_list_label.setVisible(True)
                else:
                    self._network_list_label.setText("Scanning for networks…")
                    self._network_list_label.setVisible(True)
            except Exception:
                self._network_list_label.setVisible(False)
        else:
            self._network_list_label.setVisible(False)

    # ----------------------------------------------------- Bluetooth
    def _refresh_bluetooth_status(self) -> None:
        """Query current Bluetooth state."""
        try:
            enabled = SystemControl.is_bluetooth_enabled()
            self._bt_toggle.set_state(enabled)
            if enabled:
                self._bt_toggle.set_status_text("Enabled")
                self._refresh_bluetooth_devices()
            else:
                self._bt_toggle.set_status_text("Disabled")
                self._clear_bt_devices()
        except Exception:
            self._bt_toggle.set_status_text("Unavailable")

    def _on_bluetooth_toggled(self, is_on: bool) -> None:
        """Handle Bluetooth toggle."""
        self._bt_toggle.set_status_text("Applying…")

        success, message = SystemControl.set_bluetooth_enabled(is_on)

        if not success:
            self._bt_toggle.set_status_text(f"Error: {message}")
            self._bt_status_label.setText(
                "⚠️ Bluetooth toggle requires admin privileges.\n"
                "Try running MiniPC as Administrator."
            )
            self._bt_status_label.setVisible(True)
            QTimer.singleShot(500, self._refresh_bluetooth_status)
            return

        # Wait for adapter to settle
        QTimer.singleShot(2000, self._refresh_bluetooth_status)

    def _refresh_bluetooth_devices(self) -> None:
        """Refresh the list of Bluetooth devices."""
        self._clear_bt_devices()
        try:
            devices = SystemControl.get_bluetooth_devices()
            if devices:
                for dev in devices:
                    row = _DeviceRow(dev["name"], dev["status"])
                    self._bt_device_rows.append(row)
                    self._bt_devices_container.addWidget(row)
                self._bt_status_label.setVisible(False)
            else:
                self._bt_status_label.setText("No paired devices found.")
                self._bt_status_label.setVisible(True)
        except Exception:
            self._bt_status_label.setText("Could not scan devices.")
            self._bt_status_label.setVisible(True)

    def _clear_bt_devices(self) -> None:
        """Remove all Bluetooth device rows."""
        for row in self._bt_device_rows:
            row.setParent(None)
            row.deleteLater()
        self._bt_device_rows.clear()

    # --------------------------------------------------------- Keyboard
    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.go_back.emit()
            return
        super().keyPressEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802
        """Refresh live values when the screen becomes visible."""
        super().showEvent(event)
        self._load_initial_values()
