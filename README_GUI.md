Triangle GUI
=================

This repository includes a minimal GTK3 desktop wrapper around the
existing `try.py` script. The GUI is intentionally small: it runs the
script and displays text output, with a refresh button and auto-refresh.

Files added:
- `gui.py` — GTK3 application that runs `try.py` and shows output.
- `triangle.desktop` — example desktop entry to install under `~/.local/share/applications`.
- `requirements.txt` — Python requirements for the GUI (and for `try.py`).

Quick start (Ubuntu / Debian / Fedora):

1. Install system packages (examples):

Ubuntu / Debian:
```
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    python3-pip
```

Fedora:
```
sudo dnf install -y python3-gobject python3-pip gtk3
```

2. Install Python packages:
```
python3 -m pip install --user -r requirements.txt
```

3. Run the GUI:
```
python3 gui.py
```

To install the desktop entry for your user:
```
mkdir -p ~/.local/share/applications
cp triangle.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications || true
```

Packaging and distribution notes:
- For cross-distro distribution prefer Flatpak (recommended) or Snap.
- For Debian/Ubuntu, create a simple .deb using fpm or a packaging tool.

Tray support: If AppIndicator/ayatana is available `gui.py` will try to
use it (best-effort). On many modern GNOME desktops the tray is
deprecated; keep the window running.

If you'd like a smaller binary, consider using PyInstaller to build a
single executable (`pyinstaller --onefile gui.py`) but test the GLib/Gtk
integration first — packaging GUI apps can be tricky.
