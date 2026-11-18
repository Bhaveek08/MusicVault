# Common Qt for Python mobile deployment intent. Machine-local SDK and wheel paths
# are not committed; deployment workflows provide those paths at build time.
[app]
title = MusicVault
project_dir = .
input_file = app/main.py
exec_directory = dist

[qt]
modules = Core, Gui, Widgets

[android]
# Architecture-specific PySide6/Shiboken6 wheel paths are passed by CI.

[buildozer]
mode = debug

[ios]
bundle_id = com.musicvault.mobile
version = 0.1.0
# Set device signing team_id only in a secured release workflow, never here.
