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

    def run_once(self, env: dict | None = None, timeout: int = 30) -> tuple[str, str, int]:
        """Run the script and return (stdout, stderr, returncode).

        env: an optional dict of environment variables to set for the child process.
        """
        try:
            child_env = os.environ.copy()
            if env:
                # only string values
                for k, v in env.items():
                    child_env[str(k)] = str(v)

            proc = subprocess.Popen(["/usr/bin/env", "python3", str(self.script_path)],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    env=child_env)
            # keep the subprocess timeout modest so the GUI doesn't hang
            out, err = proc.communicate(timeout=timeout)
            return out, err, proc.returncode
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
            return "", "Timed out", 124
        except Exception as e:
            return "", str(e), 2


class TriangleWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application, runner: TryRunner, refresh_seconds: int = 0):
        super().__init__(application=app, title="Triangle — Moon & Sun Report")
        self.set_default_size(900, 650)
        self.runner = runner
        self.refresh_seconds = refresh_seconds

        hb = Gtk.HeaderBar(title="Triangle")
        hb.set_show_close_button(True)
        self.set_titlebar(hb)

        refresh_btn = Gtk.Button(label="Run")
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

        # --- Settings UI ---
        settings_grid = Gtk.Grid(column_spacing=10, row_spacing=5, margin=10)
        vbox.pack_start(settings_grid, False, False, 0)

        # Mode
        settings_grid.attach(Gtk.Label(label="Mode:", xalign=1), 0, 0, 1, 1)
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append_text("AUTO")
        self.mode_combo.append_text("COORDS")
        self.mode_combo.append_text("ADDRESS")
        self.mode_combo.set_active(0)
        settings_grid.attach(self.mode_combo, 1, 0, 1, 1)

        # Lat/Lon
        settings_grid.attach(Gtk.Label(label="Latitude:", xalign=1), 2, 0, 1, 1)
        self.lat_entry = Gtk.Entry(text="46.7313")
        settings_grid.attach(self.lat_entry, 3, 0, 1, 1)
        settings_grid.attach(Gtk.Label(label="Longitude:", xalign=1), 4, 0, 1, 1)
        self.lon_entry = Gtk.Entry(text="-117.1796")
        settings_grid.attach(self.lon_entry, 5, 0, 1, 1)

        # City/State/Country
        settings_grid.attach(Gtk.Label(label="City:", xalign=1), 0, 1, 1, 1)
        self.city_entry = Gtk.Entry(text="Moscow")
        settings_grid.attach(self.city_entry, 1, 1, 1, 1)
        settings_grid.attach(Gtk.Label(label="State:", xalign=1), 2, 1, 1, 1)
        self.state_entry = Gtk.Entry(text="Idaho")
        settings_grid.attach(self.state_entry, 3, 1, 1, 1)
        settings_grid.attach(Gtk.Label(label="Country:", xalign=1), 4, 1, 1, 1)
        self.country_entry = Gtk.Entry(text="USA")
        settings_grid.attach(self.country_entry, 5, 1, 1, 1)

        # Separator
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, margin=5), False, False, 0)

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

        # Guard to prevent overlapping runs
        self._running_lock = threading.Lock()

        # No automatic run at startup to avoid heavy background activity.
        # Periodic refresh (only if interval > 0)
        if self.refresh_seconds and self.refresh_seconds > 0:
            GLib.timeout_add_seconds(self.refresh_seconds, self._scheduled_refresh)

    def _scheduled_refresh(self) -> bool:
        # Called by GLib timeout - only start if not already running
        if self._running_lock.locked():
            # update summary to show we skipped a run
            self.summary_label.set_text("Skipped refresh: previous run still active")
            return True
        return self.refresh()

    def _set_tab_text(self, tab_name: str, text: str):
        tv = self.tabs.get(tab_name)
        if not tv:
            return
        buf = tv.get_buffer()
        buf.set_text(text)

    def _scroll_tab_to_top(self, tab_name: str):
        tv = self.tabs.get(tab_name)
        if not tv:
            return
        buf = tv.get_buffer()
        start = buf.get_start_iter()
        tv.scroll_to_iter(start, 0.0, False, 0.0, 0.0)

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
        # Collect settings from the UI
        env = {
            'LOCATION_MODE': self.mode_combo.get_active_text(),
            'LATITUDE': self.lat_entry.get_text(),
            'LONGITUDE': self.lon_entry.get_text(),
            'CITY': self.city_entry.get_text(),
            'STATE': self.state_entry.get_text(),
            'COUNTRY': self.country_entry.get_text(),
        }

        def worker():
            # prevent overlapping runs
            acquired = self._running_lock.acquire(False)
            if not acquired:
                GLib.idle_add(self.summary_label.set_text, "Skipped: another run is active")
                return
            try:
                start = time.time()
                GLib.idle_add(self.summary_label.set_text, "Running...")
                # give immediate visual feedback
                GLib.idle_add(self._set_tab_text, "All", "Running...\n")
                GLib.idle_add(self._set_tab_text, "Sun", "")
                GLib.idle_add(self._set_tab_text, "Moon", "")
                GLib.idle_add(self._set_tab_text, "Phases", "")
                GLib.idle_add(self._set_tab_text, "Subpoint", "")
                out, err, rc = self.runner.run_once(env=env)
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
                GLib.idle_add(self._scroll_tab_to_top, "All")
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
            finally:
                try:
                    self._running_lock.release()
                except RuntimeError:
                    pass

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
