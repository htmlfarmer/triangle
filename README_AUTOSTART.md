Run Qibla-Numa at login or when opening a terminal

Options provided here:

1) Run manually in a terminal
   - cd /path/to/triangle
   - ./run_try.sh

2) Add to your shell profile (prints every new terminal)
   - Edit ~/.bashrc (or ~/.profile) and add one of the lines below:

# print Qibla-Numa once per interactive shell
if [[ $- == *i* ]]; then
  /path/to/triangle/run_try.sh
fi

3) Create a systemd --user service (runs at login)
   - Create the file ~/.config/systemd/user/qibla-numa.service with the contents below.

[Unit]
Description=Run Qibla-Numa report at user login

[Service]
Type=oneshot
ExecStart=/path/to/triangle/run_try.sh

[Install]
WantedBy=default.target

Then enable and start:

systemctl --user daemon-reload
systemctl --user enable qibla-numa.service
systemctl --user start qibla-numa.service

4) GNOME / Desktop autostart (.desktop)
   - Create ~/.config/autostart/qibla-numa.desktop with:

[Desktop Entry]
Type=Application
Name=Qibla-Numa
Exec=/path/to/triangle/run_try.sh
Terminal=true
X-GNOME-Autostart-enabled=true

Notes:
- Replace /path/to/triangle with the absolute path to your cloned repo (e.g., /home/you/github/triangle)
- If your script depends on a virtualenv, modify Exec line to source the venv first.
- For the Weather app modification request, see next section in this README.
