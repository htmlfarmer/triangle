#!/usr/bin/env python3
"""
Simple GTK desktop wrapper for the existing try.py script.

Features:
- Runs the repository's try.py and shows the textual output
- Manual refresh button and auto-refresh interval
- Optional AppIndicator tray (if libayatana-appindicator is available)

This is intended as a minimal cross-distribution desktop app. For
packaging across distros prefer creating a Flatpak or a distro package.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, GLib
except Exception as exc:
    raise SystemExit("PyGObject (python3-gi) and GTK3 are required to run the GUI: %s" % exc)

# Optional AppIndicator (tray) support
USE_APPINDICATOR = True
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
except Exception:
    USE_APPINDICATOR = False


REPO_ROOT = Path(__file__).resolve().parent
TRY_PY = REPO_ROOT / "try.py"


class TryRunner:
    def __init__(self, script_path: Path):
        self.script_path = script_path

    def run_once(self) -> tuple[str, str, int]:
        """Run the script and return (stdout, stderr, returncode)."""
        try:
            proc = subprocess.Popen(["/usr/bin/env", "python3", str(self.script_path)],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            out, err = proc.communicate(timeout=120)
            return out, err, proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            return "", "Timed out", 124
        except Exception as e:
            return "", str(e), 2


class TriangleWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application, runner: TryRunner, refresh_seconds: int = 300):
        super().__init__(application=app, title="Triangle — Moon & Sun Report")
        self.set_default_size(900, 650)
        self.runner = runner
        self.refresh_seconds = refresh_seconds

        hb = Gtk.HeaderBar(title="Triangle")
        hb.set_show_close_button(True)
        self.set_titlebar(hb)

        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", lambda *_: self.refresh())
        hb.pack_end(refresh_btn)

        self.summary_label = Gtk.Label(label="Idle")
        self.summary_label.set_xalign(0)
        hb.pack_start(self.summary_label)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Notebook with dedicated tabs
        self.notebook = Gtk.Notebook()
        vbox.pack_start(self.notebook, True, True, 0)

        # Prepare textviews for tabs
        self.tabs = {}
        for name in ("Sun", "Moon", "Phases", "Subpoint", "All"):
            tv = Gtk.TextView()
            tv.set_editable(False)
            tv.set_wrap_mode(Gtk.WrapMode.NONE)
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.add(tv)
            label = Gtk.Label(label=name)
            self.notebook.append_page(scrolled, label)
            self.tabs[name] = tv

        self.show_all()

        # AppIndicator/tray (best-effort)
        self.indicator = None
        if USE_APPINDICATOR:
            try:
                self.indicator = AppIndicator3.Indicator.new(
                    "triangle-indicator", "utilities-terminal", AppIndicator3.IndicatorCategory.APPLICATION_STATUS
                )
                self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
                menu = Gtk.Menu()
                item_show = Gtk.MenuItem(label="Show")
                item_quit = Gtk.MenuItem(label="Quit")
                item_show.connect("activate", lambda *_: self.present())
                item_quit.connect("activate", lambda *_: Gtk.main_quit())
                menu.append(item_show)
                menu.append(item_quit)
                menu.show_all()
                self.indicator.set_menu(menu)
            except Exception:
                self.indicator = None

        # First run in background
        GLib.idle_add(self.refresh)

        # Periodic refresh
        GLib.timeout_add_seconds(self.refresh_seconds, self.refresh)

    def _set_tab_text(self, tab_name: str, text: str):
        tv = self.tabs.get(tab_name)
        if not tv:
            return
        buf = tv.get_buffer()
        buf.set_text(text)

    def _parse_and_distribute(self, full_text: str) -> dict:
        # Simple heuristics to split the output into the requested tabs.
        sun_lines = []
        moon_lines = []
        phases_lines = []
        subpoint_lines = []
        other_lines = []

        for ln in full_text.splitlines():
            l = ln.strip()
            if not l:
                continue
            low = l.lower()
            if "sun" in low or "solar" in low or "sunrise" in low or "sunset" in low or "dhuhr" in low:
                sun_lines.append(ln)
            elif "moon" in low or "moonrise" in low or "moonset" in low or "zenith" in low or "ascent" in low:
                moon_lines.append(ln)
            elif "phase" in low or "lunation" in low or "full" in low or "new" in low or "quarter" in low:
                phases_lines.append(ln)
            elif "sub" in low or "nearest city" in low or "sublunar" in low or "subsolar" in low:
                subpoint_lines.append(ln)
            else:
                other_lines.append(ln)

        # Compose tab text
        all_text = full_text
        sun_text = "\n".join(sun_lines) or "(no sun lines found)"
        moon_text = "\n".join(moon_lines) or "(no moon lines found)"
        phases_text = "\n".join(phases_lines) or "(no phases lines found)"
        subpoint_text = "\n".join(subpoint_lines) or "(no subpoint lines found)"
        other_text = "\n".join(other_lines)

        return {
            "Sun": sun_text,
            "Moon": moon_text,
            "Phases": phases_text,
            "Subpoint": subpoint_text,
            "All": all_text,
            "Other": other_text,
        }

    def _update_indicator(self, text: str):
        # Best-effort: set a short label on the AppIndicator if supported.
        if not self.indicator:
            return
        try:
            # set_label may not exist on all implementations; ignore failures
            self.indicator.set_label(text[:64], "")
        except Exception:
            pass

    def refresh(self) -> bool:
        """Trigger a background refresh. Returns True to keep timeout active."""
        def worker():
            start = time.time()
            GLib.idle_add(self.summary_label.set_text, "Running...")
            out, err, rc = self.runner.run_once()
            elapsed = time.time() - start
            summary = f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')} (rc={rc}, {elapsed:.1f}s)"
            if rc != 0 and not out:
                out = "(no stdout)"
            full = out
            if err:
                full += "\n--- STDERR ---\n" + err

            parsed = self._parse_and_distribute(full)
            # Update UI on main thread
            GLib.idle_add(self._set_tab_text, "Sun", parsed["Sun"])
            GLib.idle_add(self._set_tab_text, "Moon", parsed["Moon"])
            GLib.idle_add(self._set_tab_text, "Phases", parsed["Phases"])
            GLib.idle_add(self._set_tab_text, "Subpoint", parsed["Subpoint"])
            GLib.idle_add(self._set_tab_text, "All", parsed["All"])
            GLib.idle_add(self.summary_label.set_text, summary)

            # Update indicator label with a compact summary (prefer moon then sun)
            compact = None
            if parsed["Moon"] and parsed["Moon"] != "(no moon lines found)":
                compact = parsed["Moon"].splitlines()[0]
            elif parsed["Sun"] and parsed["Sun"] != "(no sun lines found)":
                compact = parsed["Sun"].splitlines()[0]
            else:
                compact = summary
            GLib.idle_add(self._update_indicator, compact)

        threading.Thread(target=worker, daemon=True).start()
        return True


class TriangleApp(Gtk.Application):
    def __init__(self, runner: TryRunner, *args, **kwargs):
        super().__init__(*args, application_id="org.htmlfarmer.triangle")
        self.runner = runner
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = TriangleWindow(self, self.runner)
        self.window.present()


def main():
    runner = TryRunner(TRY_PY)
    app = TriangleApp(runner)
    app.run(None)


if __name__ == "__main__":
    main()
