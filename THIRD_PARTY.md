# Third-party components

## dgVoodoo 2.87.5

Author: **Dege**. Copyright © 2013–2026 Dege.

The original, unmodified `dgVoodoo2_87_5.zip` is included in
`rt3_ultrawide/vendor/`. This game-specific mod installs `MS/x86/D3D8.dll` and `dgVoodooCpl.exe`
and uses the archive's `dgVoodoo.conf` as the starting configuration when no
configuration already exists. The full original archive also contains the
other wrappers and links to the upstream documentation.

- [Official release and original download](https://github.com/dege-diosg/dgVoodoo2/releases/tag/v2.87.5)
- [Author's redistribution terms and documentation](https://dege.freeweb.hu/dgVoodoo2/ReadmeGeneral/#1-redistribution-rights)
- Archive SHA-256: `5ffde6927f7355ca3fdd5d785b581256a8e6539fa13e395a891ade6ba1040850`
- x86 D3D8.dll SHA-256: `d03e2562178db1fcf3493fc0a0b23a465e35c55d73adb3ec095be866cd662704`

The author's terms permit individual files to accompany a game/mod and require
the full ZIP when redistributing dgVoodoo as a standalone component. This project
retains that complete archive. dgVoodoo is a separate component, **not covered by
this project's MIT license**. Its binaries are not modified. The watermark is
disabled using its normal configuration setting.

## Windows release runtime

The release bundles Python, Tcl/Tk, Frida, and the PyInstaller bootloader so players
do not need Python installed. Their license files are copied into the release's
`licenses/` directory by the build script. Frida's Python package uses the
wxWindows Library Licence, version 3.1. PyInstaller's bootloader distribution
exception permits distributing the generated application under its own license.

- [Python](https://www.python.org/)
- [Frida 17.15.5 source](https://github.com/frida/frida/releases/tag/17.15.5)
- [PyInstaller](https://github.com/pyinstaller/pyinstaller)

## Railroad Tycoon 3

The game is required and is not included. This repository contains no game
executable, extracted game assets, save files, or copied game configuration
baseline. The installer reads and backs up the player's own files locally.
Railroad Tycoon 3 and its assets remain the property of their respective owners.
This is an unofficial community modification.
