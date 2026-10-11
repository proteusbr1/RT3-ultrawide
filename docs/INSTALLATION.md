# Installation and operation

## Before installing

Run the original game at least once so that `Data/Configuration/engine.cfg` and
`HotKeys/hotkeys.txt` exist. Save your game and exit it. Select the installation
folder, not a save folder or the Steam application folder.

The installer checks the exact executable hash, configuration format, hotkey
identifiers, and graphics-wrapper checksum. It will not install while any RT3
process is running. If a different `D3D8.dll` is present, retain your own backup
and remove that wrapper before installing this one. Do not mix wrapper versions.

The tested layout is 3440×1440. Use the resolution of the display where you intend
to play. The GUI starts with the primary monitor's resolution; on a multi-monitor
system, verify it before installing.

## What gets installed

| Path under the game folder | Purpose |
| --- | --- |
| `Data/Configuration/engine.cfg` | Native width/height and startup display flag |
| `HotKeys/hotkeys.txt` | WASD, Space, and relocated conflicting shortcuts |
| `D3D8.dll` | Unmodified x86 dgVoodoo 2.87.5 |
| `dgVoodooCpl.exe` | Matching official control panel |
| `dgVoodoo.conf` | Borderless output, native resolution, watermark off |
| `Launch RT3 Ultrawide.cmd` | Persistent entry point |
| `RT3Ultrawide/launch.ps1` | Launcher command |
| `RT3Ultrawide/app/` | Self-contained helper (prebuilt release only) |
| `RT3Ultrawide/installation.json` | Version, resolution, backup manifest and hashes |
| `RT3Ultrawide/backups/` | Original files and restoration snapshots |

The wrapper archive is included in the package. Its SHA-256 and the extracted DLL
hash are checked before use. A checksum-verified upstream download is a fallback
only if someone builds a source distribution without the bundled archive.

Unrelated configuration entries are preserved during installation. Custom hotkey
conflicts are reported instead of silently assigning two actions to one key.

## Launching

Use `Launch RT3 Ultrawide.cmd` or **Launch** in the GUI. The launcher refreshes
the startup display settings, asks Steam to open App ID 7610, waits for RT3,
then attaches the helper. If RT3 is already running, it attempts attachment to
that installation without rewriting configuration. Its current resolution must
be suitable; exit and relaunch if you opened it at a different resolution.

The helper verifies code signatures, runs native coordinate tests, applies the
patch in memory, and remains attached until the game exits. A lock prevents
duplicate copies of this helper, including the older development launcher.

Do not use F9/F11/F12 to change display mode while the patch is attached.
For a resolution change: save, exit, install with the new resolution, then launch.

## Command line

These examples use the source environment. The release EXE accepts the same
arguments, although its windowless build does not display terminal output.

```powershell
$game = 'D:\SteamLibrary\steamapps\common\Railroad Tycoon 3'
.\.venv\Scripts\python.exe -m rt3_ultrawide install --game $game --width 3440 --height 1440
.\.venv\Scripts\python.exe -m rt3_ultrawide launch --game $game
.\.venv\Scripts\python.exe -m rt3_ultrawide doctor --game $game --output diagnostic.json
.\.venv\Scripts\python.exe -m rt3_ultrawide uninstall --game $game
```

CLI restoration refuses to overwrite settings changed since installation.
Add `--preserve-changed` to first retain those settings in a separate backup and
restore the original baseline. The GUI explicitly offers this behavior in its
restore confirmation.

## Updates and removal

Install a new release with the game closed. The original baseline is retained
across updates. Close the installed helper GUI before replacing its application
files; run updates from the newly extracted release folder.

Restoration removes files created by the installer and restores files that
existed beforehand. Backup history, logs, and the inactive application directory
remain for recovery. After a successful restoration, you may manually delete
`RT3Ultrawide` when you no longer need those backups.

The baseline means **the files present before the first installation**. If other
mods or the earlier experimental patch were already installed, restoration
returns to that state, not necessarily to a clean Steam installation.

The installer can upgrade the exact official dgVoodoo 2.87.3 DLL and control panel
to 2.87.5. It preserves the existing configuration and backs up replaced files.
Unknown wrapper builds are rejected to avoid overwriting an unrelated mod.
