# MiniPC — Fullscreen TV Media Center App

A fullscreen Python application with a TV-like interface for browsing/playing movies and managing computer settings, inspired by LibreELEC/Kodi.

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **GUI Framework** | PySide6 + QtWidgets | GPU-friendly, rich styling via Qt stylesheets, mature ecosystem |
| **Media Playback** | `python-vlc` | Widest codec support, easiest embedding into Qt, no extra DLL management |
| **Volume** | `pycaw` | Direct Windows audio API |
| **Brightness** | `screen-brightness-control` | Cross-monitor support |
| **Wi-Fi** | `netsh` via subprocess | Native Windows networking |
| **Power** | `subprocess` (shutdown/restart/sleep) | Standard Windows commands |
| **File Scanning** | `pathlib.rglob()` | Built-in, fast recursive search |

> [!NOTE]
> I'm using **QtWidgets with heavy CSS styling** instead of QML to keep the project in pure Python (no separate QML files). This simplifies development while still delivering a polished, animated TV-style interface using Qt's animation framework (`QPropertyAnimation`, `QGraphicsOpacityEffect`).

## User Review Required

> [!IMPORTANT]
> **Media Player Dependency**: This plan uses `python-vlc`, which requires **VLC media player** to be installed on the system. If you'd prefer a self-contained solution, I can use Qt's built-in `QMediaPlayer` instead (fewer codecs but zero external dependencies).

> [!IMPORTANT]  
> **Admin Privileges**: Some settings (Wi-Fi toggle, display resolution) may require running the app as Administrator. The app will gracefully handle permission errors with user-friendly messages.

## Open Questions

1. **Movie directories**: Which folders should be scanned for movies? Default plan is `~/Videos`, `~/Downloads`, and any connected external drives. Would you like to add custom paths?
2. **Gamepad support**: Should I include gamepad/controller navigation (adds `pygame` dependency), or is keyboard + mouse sufficient?
3. **App launcher**: Would you like the ability to launch other apps (e.g., a web browser, Steam) from the home screen?

## Proposed Changes

### Project Structure

```
minipc/
├── main.py                    # Entry point, fullscreen window
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Root fullscreen window + navigation
│   ├── home_screen.py         # Home screen with category tiles
│   ├── movie_browser.py       # Movie grid with poster/thumbnail view
│   ├── movie_player.py        # VLC-embedded video player with controls
│   ├── settings_screen.py     # System settings panel
│   └── components/
│       ├── __init__.py
│       ├── focus_card.py      # Animated focusable card widget
│       ├── nav_bar.py         # Sidebar navigation
│       ├── slider_setting.py  # Reusable slider for volume/brightness
│       └── toggle_setting.py  # Reusable toggle for Wi-Fi/Bluetooth
├── backend/
│   ├── __init__.py
│   ├── media_scanner.py       # Scan directories for video files
│   ├── system_control.py      # Volume, brightness, Wi-Fi, power controls
│   └── thumbnail_cache.py     # Generate & cache video thumbnails
├── assets/
│   ├── fonts/                 # Inter font files
│   └── icons/                 # SVG icons for UI
├── styles/
│   └── theme.py               # Color palette, fonts, global stylesheet
├── requirements.txt
└── README.md
```

---

### Core Application

#### [NEW] [main.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/main.py)
- Application entry point
- Initialize `QApplication` with dark palette
- Create fullscreen `MainWindow`
- Apply global stylesheet from theme
- Handle graceful shutdown

#### [NEW] [requirements.txt](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/requirements.txt)
```
PySide6>=6.6
python-vlc>=3.0
pycaw>=20240210
comtypes>=1.4
screen-brightness-control>=0.23
pywin32>=306
Pillow>=10.0
```

---

### Theme & Styling

#### [NEW] [styles/theme.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/styles/theme.py)
- Dark color palette inspired by modern streaming UIs:
  - Background: deep navy/charcoal (`#0a0e1a`)
  - Cards: semi-transparent dark (`rgba(20, 25, 45, 0.85)`)
  - Accent: vibrant cyan-blue gradient (`#00d4ff → #7b61ff`)
  - Text: crisp white with muted secondary (`#8892b0`)
  - Focus glow: animated accent border
- Typography: Inter font family (bundled)
- Global Qt stylesheet generator
- Animation timing constants

---

### UI Layer

#### [NEW] [ui/main_window.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/ui/main_window.py)
- `MainWindow(QMainWindow)` — fullscreen, frameless
- `QStackedWidget` for screen transitions with fade animations
- Sidebar navigation (`NavBar`) with icons for Home, Movies, Settings, Power
- Keyboard navigation handler (arrow keys, Enter, Escape)
- Screen transition animations (slide + fade)

#### [NEW] [ui/home_screen.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/ui/home_screen.py)
- Large hero area with time/date display
- Grid of category tiles: 🎬 Movies, ⚙️ Settings, 🔌 Power
- Each tile is a `FocusCard` with icon, label, and hover/focus animation
- Keyboard grid navigation (arrow keys move focus between tiles)

#### [NEW] [ui/movie_browser.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/ui/movie_browser.py)
- Scrollable grid of movie cards showing filename + file size
- Search/filter bar at top
- Focus-based navigation through the grid
- Click/Enter to launch player
- Background scanning with progress indicator

#### [NEW] [ui/movie_player.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/ui/movie_player.py)
- Embedded VLC player in a `QFrame`
- Auto-hiding overlay controls (play/pause, seek bar, volume, fullscreen)
- Controls appear on mouse move, fade after 3 seconds
- Keyboard shortcuts: Space (play/pause), Left/Right (seek), Escape (exit)

#### [NEW] [ui/settings_screen.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/ui/settings_screen.py)
- Categorized settings with smooth focus navigation:
  - **🔊 Volume**: Slider 0–100% with live preview
  - **🔆 Brightness**: Slider 0–100%
  - **📶 Wi-Fi**: Show connected network, list available networks, connect/disconnect
  - **⚡ Power**: Shutdown, Restart, Sleep buttons with confirmation dialog
- Each setting uses reusable `SliderSetting` or `ToggleSetting` components

---

### Reusable Components

#### [NEW] [ui/components/focus_card.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/ui/components/focus_card.py)
- `FocusCard(QFrame)` — animated card widget
- On focus: scale up slightly, glow border, brightness increase
- On hover: similar but lighter effect
- Smooth `QPropertyAnimation` for all transitions
- Customizable icon, title, subtitle

#### [NEW] [ui/components/nav_bar.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/ui/components/nav_bar.py)
- Vertical sidebar with icon buttons
- Active indicator (glowing accent line)
- Collapse/expand animation
- Keyboard navigable (Up/Down to move, Enter to select)

#### [NEW] [ui/components/slider_setting.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/ui/components/slider_setting.py)
- Label + styled `QSlider` + value display
- Real-time value change callback
- Custom styled slider track and handle (accent colored)

#### [NEW] [ui/components/toggle_setting.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/ui/components/toggle_setting.py)
- Label + animated toggle switch
- Smooth on/off animation
- Status text display

---

### Backend Layer

#### [NEW] [backend/media_scanner.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/backend/media_scanner.py)
- `MediaScanner` class that runs in a `QThread`
- Scans configured directories for video files (`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.m4v`, `.webm`, etc.)
- Returns list of `MovieInfo` dataclass objects (path, name, size, modified date)
- Emits progress signals for UI updates
- Caches results for fast re-display

#### [NEW] [backend/system_control.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/backend/system_control.py)
- **Volume**: `pycaw` — get/set master volume (0.0–1.0), mute/unmute
- **Brightness**: `screen-brightness-control` — get/set brightness (0–100)
- **Wi-Fi**: `netsh` via subprocess — list networks, connect to saved profiles, show current connection
- **Power**: subprocess calls — shutdown (`/s /t 0`), restart (`/r /t 0`), sleep (`rundll32 powrprof.dll,SetSuspendState`)
- All methods include error handling with descriptive messages

#### [NEW] [backend/thumbnail_cache.py](file:///c:/Users/Will/OneDrive/github/copilot%20cli/minipc/backend/thumbnail_cache.py)
- Generate thumbnails from video files using VLC's snapshot feature
- Cache thumbnails to `~/.minipc/thumbnails/`
- Lazy loading — generate on first view, serve from cache subsequently

---

### Assets

#### [NEW] assets/icons/
- SVG icons for: home, movies, settings, power, volume, brightness, wifi, play, pause, back, forward
- Will use simple, clean line icons (embedded as Qt resources or loaded from file)

---

## Visual Design

The UI will follow a **modern streaming/smart TV aesthetic**:

```
┌──────────────────────────────────────────────────────────────┐
│  ◀ NAV │                                                     │
│        │         🕐 Tuesday, June 10 — 8:44 AM               │
│  🏠    │                                                     │
│  Home  │    ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│        │    │             │  │             │  │           │ │
│  🎬    │    │  🎬 Movies  │  │  ⚙️ Settings │  │  ⚡ Power  │ │
│  Movies│    │             │  │             │  │           │ │
│        │    └─────────────┘  └─────────────┘  └───────────┘ │
│  ⚙️    │                                                     │
│  Settings   ┌─────────────┐  ┌─────────────┐               │
│        │    │  Recently   │  │  Continue   │               │
│  ⚡    │    │  Added      │  │  Watching   │               │
│  Power │    └─────────────┘  └─────────────┘               │
│        │                                                     │
└──────────────────────────────────────────────────────────────┘
```

- Deep dark background with subtle gradient
- Glassmorphism cards with blur and transparency
- Cyan-to-purple accent gradient for focus states
- Smooth 300ms animations on all transitions
- Large, readable text (minimum 18px for body, 32px+ for headings)

## Verification Plan

### Manual Verification
1. Launch app → verify it starts fullscreen with the home screen
2. Navigate with keyboard (arrow keys + Enter + Escape) through all screens
3. Open movie browser → verify it finds video files from ~/Videos
4. Play a movie → verify VLC playback with overlay controls
5. Open settings → adjust volume slider → verify system volume changes
6. Open settings → adjust brightness → verify screen brightness changes
7. Verify Wi-Fi status displays correctly
8. Test power menu (sleep only — won't test shutdown/restart for obvious reasons!)
9. Test Escape key returns to previous screen from any location

### Automated Tests
- None initially — this is a UI-heavy app best verified manually
- Future: unit tests for `backend/system_control.py` and `backend/media_scanner.py`
