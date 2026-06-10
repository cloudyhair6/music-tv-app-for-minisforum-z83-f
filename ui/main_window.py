"""Main application window — fullscreen, frameless, with sidebar navigation."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame,
    QGraphicsOpacityEffect, QMessageBox, QSizePolicy,
)

from styles.theme import Colors, Sizes
from ui.components import FocusCard, NavBar
from ui.home_screen import HomeScreen
from ui.movie_browser import MovieBrowser
from ui.movie_player import MoviePlayer
from ui.settings_screen import SettingsScreen
from backend.system_control import SystemControl
from backend.remote_server import RemoteServer, RemoteCommandDispatcher
from backend.updater import UpdateWorker, get_local_version


# Screen indices
_HOME = 0
_MOVIES = 1
_SETTINGS = 2
_POWER = 3
_PLAYER = 4


class _PowerScreen(QWidget):
    """Simple power options screen with cards for Shutdown, Restart, Sleep, Lock."""

    go_back = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PowerScreen")
        self._cards: list[FocusCard] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(
            Sizes.SPACING_LG, Sizes.SPACING_LG,
            Sizes.SPACING_LG, Sizes.SPACING_LG,
        )
        root.setSpacing(Sizes.SPACING)

        # Header
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

        title = QLabel("Power")
        title.setStyleSheet(
            f"font-size: {Sizes.FONT_H1}px; "
            f"font-weight: 700; "
            f"color: {Colors.TEXT_PRIMARY}; "
            f"background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        # Center content
        root.addStretch(2)

        subtitle = QLabel("Choose a power option")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            f"font-size: {Sizes.FONT_H2}px; "
            f"color: {Colors.TEXT_SECONDARY}; "
            f"background: transparent; "
            f"margin-bottom: {Sizes.SPACING_LG}px;"
        )
        root.addWidget(subtitle)

        # Cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(Sizes.SPACING_LG)
        cards_layout.addStretch(1)

        card_data = [
            ("💤", "Sleep", "Suspend the system", Colors.ACCENT, self._on_sleep),
            ("🔄", "Restart", "Restart the computer", Colors.WARNING, self._on_restart),
            ("⏻", "Shutdown", "Turn off the computer", Colors.DANGER, self._on_shutdown),
            ("🔒", "Lock", "Lock the screen", Colors.ACCENT_SECONDARY, self._on_lock),
        ]

        for icon, label, subtitle_text, color, handler in card_data:
            card = FocusCard(
                icon_char=icon,
                title=label,
                subtitle=subtitle_text,
                color=color,
                parent=self,
            )
            card.setMinimumSize(200, 180)
            card.setMaximumSize(240, 200)
            card.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed,
            )
            card.clicked.connect(handler)
            cards_layout.addWidget(card)
            self._cards.append(card)

        cards_layout.addStretch(1)
        root.addLayout(cards_layout)

        root.addStretch(3)

        # Tab order
        for i in range(len(self._cards) - 1):
            self.setTabOrder(self._cards[i], self._cards[i + 1])

    def _confirm_action(self, title: str, message: str) -> bool:
        """Show a styled confirmation dialog."""
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.setStyleSheet(
            f"QMessageBox {{ "
            f"  background: {Colors.BG_SECONDARY}; "
            f"  color: {Colors.TEXT_PRIMARY}; "
            f"}} "
            f"QMessageBox QLabel {{ "
            f"  color: {Colors.TEXT_PRIMARY}; "
            f"  font-size: {Sizes.FONT_BODY}px; "
            f"}} "
            f"QPushButton {{ "
            f"  background: {Colors.BG_TERTIARY}; "
            f"  color: {Colors.TEXT_PRIMARY}; "
            f"  border: 1px solid {Colors.BORDER}; "
            f"  border-radius: {Sizes.BUTTON_RADIUS}px; "
            f"  padding: 8px 24px; "
            f"  font-size: {Sizes.FONT_BODY}px; "
            f"  min-width: 80px; "
            f"}} "
            f"QPushButton:hover {{ "
            f"  background: {Colors.BG_CARD_HOVER}; "
            f"  border-color: {Colors.ACCENT}; "
            f"}}"
        )
        return box.exec() == QMessageBox.StandardButton.Yes

    def _on_sleep(self) -> None:
        if self._confirm_action("Sleep", "Put the computer to sleep?"):
            SystemControl.sleep()

    def _on_restart(self) -> None:
        if self._confirm_action("Restart", "Are you sure you want to restart?"):
            SystemControl.restart()

    def _on_shutdown(self) -> None:
        if self._confirm_action(
            "Shutdown", "Are you sure you want to shut down?"
        ):
            SystemControl.shutdown()

    def _on_lock(self) -> None:
        SystemControl.lock_screen()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.go_back.emit()
            return

        focused = self.focusWidget()
        if focused in self._cards:
            idx = self._cards.index(focused)
            if key == Qt.Key.Key_Left and idx > 0:
                self._cards[idx - 1].setFocus()
                return
            if key == Qt.Key.Key_Right and idx < len(self._cards) - 1:
                self._cards[idx + 1].setFocus()
                return

        super().keyPressEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._cards:
            self._cards[0].setFocus()


class MainWindow(QMainWindow):
    """Fullscreen frameless main window with sidebar navigation and screen stack."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MiniPC Media Center")
        self.setObjectName("MainWindow")
        self.setStyleSheet(
            f"QMainWindow#MainWindow {{ background-color: {Colors.BG_PRIMARY}; }}"
        )

        self._is_playing = False
        self._setup_ui()
        self._connect_signals()
        self._setup_remote_server()

        # Start fullscreen
        self.showFullScreen()

        # Check for updates on startup
        self._check_for_updates()

    def _setup_ui(self) -> None:
        # Central widget
        central = QWidget()
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar navigation
        self._nav_bar = NavBar(self)
        self._nav_bar.add_item("🏠", "Home")
        self._nav_bar.add_item("🎬", "Movies")
        self._nav_bar.add_item("⚙️", "Settings")
        self._nav_bar.add_item("⚡", "Power")
        main_layout.addWidget(self._nav_bar)

        # --- Screen stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")
        main_layout.addWidget(self._stack, 1)

        # Create screens
        self._home_screen = HomeScreen()
        self._movie_browser = MovieBrowser()
        self._movie_player = MoviePlayer()
        self._settings_screen = SettingsScreen()
        self._power_screen = _PowerScreen()

        # Add to stack in order matching constants
        self._stack.addWidget(self._home_screen)      # 0 = HOME
        self._stack.addWidget(self._movie_browser)     # 1 = MOVIES
        self._stack.addWidget(self._settings_screen)   # 2 = SETTINGS
        self._stack.addWidget(self._power_screen)      # 3 = POWER
        self._stack.addWidget(self._movie_player)      # 4 = PLAYER

        # Start at home
        self._stack.setCurrentIndex(_HOME)

        # --- Update overlay (initially hidden)
        self._update_overlay = QWidget(central)
        self._update_overlay.setStyleSheet(
            f"background: {Colors.OVERLAY};"
        )
        self._update_overlay.setVisible(False)
        update_layout = QVBoxLayout(self._update_overlay)
        update_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._update_label = QLabel("Checking for updates...")
        self._update_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_label.setStyleSheet(
            f"font-size: {Sizes.FONT_H2}px; "
            f"color: {Colors.TEXT_PRIMARY}; "
            f"background: {Colors.BG_CARD_SOLID}; "
            f"padding: {Sizes.SPACING_XL}px; "
            f"border-radius: {Sizes.CARD_RADIUS}px; "
            f"min-width: 400px;"
        )
        update_layout.addWidget(self._update_label)

    def _connect_signals(self) -> None:
        # Nav bar
        self._nav_bar.item_clicked.connect(self._on_nav_clicked)

        # Home screen navigation
        self._home_screen.navigate_to.connect(self._on_home_navigate)

        # Movie browser
        self._movie_browser.play_movie.connect(self._start_playback)
        self._movie_browser.go_back.connect(lambda: self._switch_screen(_HOME))

        # Movie player
        self._movie_player.go_back.connect(self._stop_playback)

        # Settings
        self._settings_screen.go_back.connect(
            lambda: self._switch_screen(_HOME),
        )

        # Power
        self._power_screen.go_back.connect(
            lambda: self._switch_screen(_HOME),
        )

    def _on_nav_clicked(self, index: int) -> None:
        """Handle sidebar navigation clicks."""
        if self._is_playing:
            self._stop_playback()
        self._switch_screen(index)

    def _on_home_navigate(self, target: str) -> None:
        """Handle home screen card clicks."""
        screen_map = {
            "movies": _MOVIES,
            "settings": _SETTINGS,
            "power": _POWER,
        }
        idx = screen_map.get(target, _HOME)
        self._switch_screen(idx)

    def _switch_screen(self, index: int) -> None:
        """Switch to a screen by index with a fade transition."""
        if index == self._stack.currentIndex():
            return

        # Update nav bar active state
        if index < 4:
            self._nav_bar.set_active(index)

        # Fade out current widget
        current = self._stack.currentWidget()
        if current:
            effect = QGraphicsOpacityEffect(current)
            current.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity", self)
            anim.setDuration(Sizes.ANIMATION_FAST)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.Type.InQuad)

            def on_fade_out_done(idx=index):
                self._stack.setCurrentIndex(idx)
                # Fade in new widget
                new_widget = self._stack.currentWidget()
                if new_widget:
                    new_effect = QGraphicsOpacityEffect(new_widget)
                    new_widget.setGraphicsEffect(new_effect)
                    fade_in = QPropertyAnimation(new_effect, b"opacity", self)
                    fade_in.setDuration(Sizes.ANIMATION_FAST)
                    fade_in.setStartValue(0.0)
                    fade_in.setEndValue(1.0)
                    fade_in.setEasingCurve(QEasingCurve.Type.OutQuad)
                    fade_in.finished.connect(
                        lambda: new_widget.setGraphicsEffect(None)
                    )
                    fade_in.start()
                    # Keep reference alive
                    self._current_fade_in = fade_in

            anim.finished.connect(on_fade_out_done)
            anim.finished.connect(
                lambda: current.setGraphicsEffect(None)
            )
            anim.start()
            # Keep reference alive
            self._current_fade_out = anim
        else:
            self._stack.setCurrentIndex(index)

    def _start_playback(self, file_path: str) -> None:
        """Start video playback — hide nav bar, switch to player."""
        self._is_playing = True
        self._nav_bar.setVisible(False)
        self._stack.setCurrentIndex(_PLAYER)
        self._movie_player.play(file_path)
        self._movie_player.setFocus()

    def _stop_playback(self) -> None:
        """Stop video and return to movie browser."""
        self._is_playing = False
        self._movie_player.stop()
        self._nav_bar.setVisible(True)
        self._switch_screen(_MOVIES)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Global key handling."""
        key = event.key()

        # Escape: stop playback or go home
        if key == Qt.Key.Key_Escape:
            if self._is_playing:
                self._stop_playback()
                return
            current = self._stack.currentIndex()
            if current != _HOME:
                self._switch_screen(_HOME)
                return

        # F11 or Alt+Enter: toggle fullscreen
        if key == Qt.Key.Key_F11 or (
            key == Qt.Key.Key_Return
            and event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            return

        # Q or Alt+F4: quit
        if key == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.close()
            return

        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Remote control server
    # ------------------------------------------------------------------

    def _setup_remote_server(self) -> None:
        """Start the HTTP remote control server."""
        self._remote_dispatcher = RemoteCommandDispatcher()
        self._remote_dispatcher.command_received.connect(self._handle_remote_command)
        self._remote_server = RemoteServer(self._remote_dispatcher, port=8080)
        try:
            url = self._remote_server.start()
            self._settings_screen.set_remote_url(url)
        except Exception as e:
            print(f"[MiniPC] Remote server failed to start: {e}")
            self._settings_screen.set_remote_url("Failed to start")

    def _handle_remote_command(self, command: str) -> None:
        """Handle a command received from the remote control."""
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtWidgets import QApplication

        key_map = {
            "up": Qt.Key.Key_Up,
            "down": Qt.Key.Key_Down,
            "left": Qt.Key.Key_Left,
            "right": Qt.Key.Key_Right,
            "select": Qt.Key.Key_Return,
            "back": Qt.Key.Key_Escape,
            "home": None,  # Special handling
            "play_pause": Qt.Key.Key_Space,
        }

        if command == "home":
            if self._is_playing:
                self._stop_playback()
            self._switch_screen(_HOME)
            return

        if command == "volume_up":
            vol = min(100, SystemControl.get_volume() + 5)
            SystemControl.set_volume(vol)
            return

        if command == "volume_down":
            vol = max(0, SystemControl.get_volume() - 5)
            SystemControl.set_volume(vol)
            return

        if command == "mute":
            SystemControl.set_volume(0)
            return

        qt_key = key_map.get(command)
        if qt_key is not None:
            # Simulate a key press to the focused widget
            focused = QApplication.focusWidget() or self
            event = QKeyEvent(QKeyEvent.Type.KeyPress, qt_key, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(focused, event)

    # ------------------------------------------------------------------
    # Auto-update
    # ------------------------------------------------------------------

    def _check_for_updates(self) -> None:
        """Check GitHub for updates on startup."""
        self._update_overlay.setVisible(True)
        self._update_overlay.raise_()
        self._update_label.setText("🔄  Checking for updates...")

        # Resize overlay to fill the window
        self._update_overlay.setGeometry(self.centralWidget().rect())

        self._update_worker = UpdateWorker(auto_apply=True)
        self._update_worker.check_complete.connect(self._on_update_check_complete)
        self._update_worker.download_progress.connect(self._on_update_progress)
        self._update_worker.update_complete.connect(self._on_update_done)
        self._update_worker.error.connect(self._on_update_error)
        self._update_worker.start()

    def _on_update_check_complete(self, available: bool, local: str, remote: str) -> None:
        if available:
            self._update_label.setText(
                f"🔄  Updating: v{local} → v{remote}\nDownloading..."
            )
        else:
            self._update_label.setText(f"✅  Up to date (v{local})")
            # Hide overlay after 1.5 seconds
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1500, self._hide_update_overlay)

    def _on_update_progress(self, current: int, total: int, filename: str) -> None:
        self._update_label.setText(
            f"🔄  Downloading update ({current}/{total})\n{filename}"
        )

    def _on_update_done(self, success: bool, message: str) -> None:
        if success:
            self._update_label.setText(f"✅  {message}\nRestarting...")
            # Restart the app
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, self._restart_app)
        else:
            self._update_label.setText(f"⚠️  Update failed: {message}")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self._hide_update_overlay)

    def _on_update_error(self, message: str) -> None:
        self._update_label.setText(f"⚠️  {message}")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, self._hide_update_overlay)

    def _hide_update_overlay(self) -> None:
        self._update_overlay.setVisible(False)

    def _restart_app(self) -> None:
        """Restart the application after an update."""
        import sys
        import os
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def resizeEvent(self, event) -> None:
        """Keep the update overlay sized to the window."""
        super().resizeEvent(event)
        if hasattr(self, '_update_overlay') and self._update_overlay.isVisible():
            self._update_overlay.setGeometry(self.centralWidget().rect())
