"""Full-featured movie player with auto-hiding overlay controls."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QStackedLayout, QFrame, QSizePolicy,
)

from styles.theme import Colors, Sizes


def _fmt_time(ms: int) -> str:
    """Format milliseconds as HH:MM:SS."""
    total_s = max(0, ms // 1000)
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class MoviePlayer(QWidget):
    """Video player with overlay transport controls."""

    go_back = Signal()

    _HIDE_DELAY_MS = 3000
    _SEEK_STEP_MS = 10_000
    _VOL_STEP = 5

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MoviePlayer")
        self.setMouseTracking(True)
        self._setup_media()
        self._setup_ui()
        self._setup_hide_timer()

    # --------------------------------------------------------- Media core
    def _setup_media(self) -> None:
        self._audio = QAudioOutput(self)
        self._audio.setVolume(0.75)

        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio)

        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.errorOccurred.connect(self._on_error)

    # ------------------------------------------------------------------ UI
    def _setup_ui(self) -> None:
        # Use a stacked layout so the overlay sits on top of the video
        stack = QStackedLayout(self)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # --- video widget (bottom layer)
        self._video_widget = QVideoWidget()
        self._video_widget.setMouseTracking(True)
        self._player.setVideoOutput(self._video_widget)
        stack.addWidget(self._video_widget)

        # --- overlay container (top layer, transparent except controls bar)
        self._overlay = QWidget()
        self._overlay.setMouseTracking(True)
        self._overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, False,
        )
        self._overlay.setStyleSheet("background: transparent;")
        overlay_layout = QVBoxLayout(self._overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)

        # error label (hidden by default)
        self._error_label = QLabel()
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setStyleSheet(
            f"font-size: {Sizes.FONT_H3}px; "
            f"color: {Colors.DANGER}; "
            f"background: {Colors.OVERLAY}; "
            f"padding: 24px; "
            f"border-radius: {Sizes.CARD_RADIUS}px;"
        )
        self._error_label.setVisible(False)
        overlay_layout.addWidget(
            self._error_label, 0, Qt.AlignmentFlag.AlignCenter,
        )

        overlay_layout.addStretch()

        # --- controls bar
        self._controls_bar = QFrame()
        self._controls_bar.setStyleSheet(
            f"QFrame {{ "
            f"  background: {Colors.OVERLAY}; "
            f"  border-top: 1px solid rgba(255,255,255,0.08); "
            f"}}"
        )
        bar_layout = QHBoxLayout(self._controls_bar)
        bar_layout.setContentsMargins(
            Sizes.SPACING_LG, Sizes.SPACING_SM,
            Sizes.SPACING_LG, Sizes.SPACING_SM,
        )
        bar_layout.setSpacing(Sizes.SPACING)

        # play/pause button
        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(48, 48)
        self._play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._play_btn.setStyleSheet(self._btn_style())
        self._play_btn.clicked.connect(self._toggle_play)
        bar_layout.addWidget(self._play_btn)

        # current time
        self._cur_time = QLabel("00:00:00")
        self._cur_time.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; "
            f"font-size: {Sizes.FONT_SMALL}px; "
            f"background: transparent;"
        )
        bar_layout.addWidget(self._cur_time)

        # seek slider
        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setRange(0, 0)
        self._seek_slider.setStyleSheet(self._slider_style())
        self._seek_slider.sliderMoved.connect(self._player.setPosition)
        bar_layout.addWidget(self._seek_slider, 1)

        # duration label
        self._dur_time = QLabel("00:00:00")
        self._dur_time.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; "
            f"font-size: {Sizes.FONT_SMALL}px; "
            f"background: transparent;"
        )
        bar_layout.addWidget(self._dur_time)

        # volume icon
        vol_icon = QLabel("🔊")
        vol_icon.setStyleSheet(
            "font-size: 18px; background: transparent;"
        )
        bar_layout.addWidget(vol_icon)

        # volume slider
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(75)
        self._vol_slider.setFixedWidth(100)
        self._vol_slider.setStyleSheet(self._slider_style())
        self._vol_slider.valueChanged.connect(
            lambda v: self._audio.setVolume(v / 100.0),
        )
        bar_layout.addWidget(self._vol_slider)

        overlay_layout.addWidget(self._controls_bar)
        stack.addWidget(self._overlay)

    # --------------------------------------------------------- Timer
    def _setup_hide_timer(self) -> None:
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(self._HIDE_DELAY_MS)
        self._hide_timer.timeout.connect(self._hide_controls)

    def _show_controls(self) -> None:
        self._controls_bar.setVisible(True)
        self._hide_timer.start()

    def _hide_controls(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._controls_bar.setVisible(False)

    # --------------------------------------------------------- Styles
    @staticmethod
    def _btn_style() -> str:
        return (
            f"QPushButton {{ "
            f"  background: {Colors.ACCENT}; "
            f"  color: {Colors.BG_PRIMARY}; "
            f"  border: none; "
            f"  border-radius: 24px; "
            f"  font-size: 20px; "
            f"}} "
            f"QPushButton:hover {{ background: {Colors.ACCENT_SECONDARY}; }}"
        )

    @staticmethod
    def _slider_style() -> str:
        return (
            f"QSlider::groove:horizontal {{ "
            f"  height: 6px; "
            f"  background: {Colors.SLIDER_GROOVE}; "
            f"  border-radius: 3px; "
            f"}} "
            f"QSlider::handle:horizontal {{ "
            f"  width: 14px; height: 14px; "
            f"  margin: -4px 0; "
            f"  background: {Colors.ACCENT}; "
            f"  border-radius: 7px; "
            f"}} "
            f"QSlider::sub-page:horizontal {{ "
            f"  background: {Colors.ACCENT}; "
            f"  border-radius: 3px; "
            f"}}"
        )

    # ------------------------------------------------------- Public API
    def play(self, file_path: str) -> None:
        """Start playing a video file."""
        self._error_label.setVisible(False)
        self._player.setSource(QUrl.fromLocalFile(file_path))
        self._player.play()
        self._show_controls()

    def stop(self) -> None:
        """Stop playback and reset."""
        self._player.stop()
        self._player.setSource(QUrl())
        self._controls_bar.setVisible(True)

    # -------------------------------------------------------- Callbacks
    def _toggle_play(self) -> None:
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _on_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_btn.setText("⏸")
        else:
            self._play_btn.setText("▶")
            self._controls_bar.setVisible(True)

    def _on_position_changed(self, pos: int) -> None:
        self._seek_slider.blockSignals(True)
        self._seek_slider.setValue(pos)
        self._seek_slider.blockSignals(False)
        self._cur_time.setText(_fmt_time(pos))

    def _on_duration_changed(self, dur: int) -> None:
        self._seek_slider.setRange(0, dur)
        self._dur_time.setText(_fmt_time(dur))

    def _on_error(self, error, msg: str = "") -> None:
        text = msg or "An error occurred during playback."
        self._error_label.setText(f"⚠️  {text}\n\nPress Escape to go back.")
        self._error_label.setVisible(True)

    # ---------------------------------------------------- Input events
    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._show_controls()
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key == Qt.Key.Key_Space:
            self._toggle_play()
        elif key == Qt.Key.Key_Escape:
            self.stop()
            self.go_back.emit()
        elif key == Qt.Key.Key_Left:
            pos = max(0, self._player.position() - self._SEEK_STEP_MS)
            self._player.setPosition(pos)
            self._show_controls()
        elif key == Qt.Key.Key_Right:
            pos = min(
                self._player.duration(),
                self._player.position() + self._SEEK_STEP_MS,
            )
            self._player.setPosition(pos)
            self._show_controls()
        elif key == Qt.Key.Key_Up:
            vol = min(100, self._vol_slider.value() + self._VOL_STEP)
            self._vol_slider.setValue(vol)
            self._show_controls()
        elif key == Qt.Key.Key_Down:
            vol = max(0, self._vol_slider.value() - self._VOL_STEP)
            self._vol_slider.setValue(vol)
            self._show_controls()
        else:
            super().keyPressEvent(event)
