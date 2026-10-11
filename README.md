# Railroad Tycoon 3 Ultrawide

An experimental Windows mod for the **Steam edition of Railroad Tycoon 3**.
Play in a borderless window at your monitor's resolution, with the original HUD
split between the bottom corners and correctly aligned mouse input.

**[Download the Windows package](https://github.com/proteusbr1/RT3-ultrawide/releases)**
· [Installation](docs/INSTALLATION.md)
· [Controls](docs/CONTROLS.md)
· [Troubleshooting](docs/TROUBLESHOOTING.md)
· [Technical notes](docs/ARCHITECTURE.md)

## What changes

- Native-resolution, borderless display with no title bar. Alt+Tab leaves the game visible.
- Map rendering, camera bounds, and world labels extend to the bottom of the screen.
- Minimap and action buttons stay at the bottom left; information panels stay at the bottom right.
- The right green background disappears when there is no information panel open.
- Removed unused footer, excess HUD background, and lower collapse widgets. **Tab** still hides the HUD.
- Proportional menus and cursor, with corrected minimap, briefing, and World Overview input.
- **WASD** pans the camera; **Space** pauses/resumes.
- dgVoodoo **2.87.5 is included**, with its watermark disabled in the installed configuration.
- Local backups and a restore command. The game executable and saves are not modified.

This keeps the game's original artwork and fonts. It is a layout/input patch,
not a replacement texture pack.

## Quick start

1. Download the Windows ZIP from **Releases** and extract the entire folder.
2. Save and close the game. Run `RT3Ultrawide.exe`.
3. Select the folder containing `RT3.exe` and enter your monitor's native resolution.
4. Click **Install / Update**, then **Launch**.
5. For future sessions, use **`Launch RT3 Ultrawide.cmd` in the game folder**.
   You can create a desktop shortcut to that file.

The release includes Python and the graphics wrapper, so neither needs a separate
installation or download. Keep the `_internal` folder beside the downloaded EXE
when running the installer. Installation copies the runtime into the game folder;
the downloaded folder can then be removed.

**Steam's regular Play button does not start the HUD helper.** Use the new launcher
each time. The helper exits when the game closes.

## Compatibility

| Component | Supported / tested |
| --- | --- |
| Operating system | Windows 10/11, x64; tested on Windows 11 |
| Game | One specific 32-bit Steam executable; validated by SHA-256 |
| Graphics wrapper | Included dgVoodoo 2.87.5, x86 D3D8.dll |
| Tested display | 3440 × 1440 |
| Configurable display range | Landscape 16:9 through 32:9, 1280×720 or larger; other resolutions need validation |

Supported `RT3.exe` SHA-256:

```text
c6e178bfc694b5fc5e059a584fc84045627cb3613604c83e19ba1906ccc0d252
```

Other game builds, executable mods, GOG/CD editions, multiplayer, and every
scenario/editor window have **not** been validated. Unsupported executables are
rejected rather than patched at unknown addresses. Read the
[validation record and limitations](docs/VALIDATION.md) before reporting a bug.

## Restore

Save and close the game, open `RT3Ultrawide.exe`, select the same game folder,
and choose **Restore original**. The installer preserves a copy of the current
files before restoring the baseline saved during the first installation.
Backups remain in `<game>/RT3Ultrawide/backups/`.

## Source and development

With Python 3.12 x64 installed, run in PowerShell from this repository:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m rt3_ultrawide
```

Source installations use that Python environment; keep the checkout and `.venv`
in place. The prebuilt release installs a self-contained runtime instead.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install pyinstaller==6.22.0
.\.venv\Scripts\python.exe tools\build_release.py
```

The Windows ZIP and checksum file are produced in `release/`.

## Project layout

```text
rt3_ultrawide/
  assets/ultrawide.js   Native runtime hooks and coordinate self-tests
  vendor/              Original dgVoodoo archive and provenance
  config.py            Resolution, wrapper, and hotkey transformations
  install.py           Compatibility checks, backups, install, restore
  runtime.py           Single-session attachment and clean detachment
  gui.py               Graphical installer and launcher
docs/                  User guide, validation record, reverse-engineering notes
tests/                 Configuration and installation safety tests
tools/                 Reproducible Windows packaging script
```

## Credits and licensing

Original patch code and documentation: [MIT](LICENSE).
dgVoodoo by **Dege** and bundled runtime dependencies retain their own licenses:
see [third-party notices](THIRD_PARTY.md). Railroad Tycoon 3 is required and is not
included. This is an unofficial community project.
