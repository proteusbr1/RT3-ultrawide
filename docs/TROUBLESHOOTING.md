# Troubleshooting

## The game opens, but the HUD is stretched or centered

Use `Launch RT3 Ultrawide.cmd`, not Steam's regular Play button. Check
`RT3Ultrawide/runtime-latest.log` for a `ready` message. If the helper is absent,
dgVoodoo can still display the game at high resolution, but the HUD corrections
will not be applied.

Since 0.2.0, the replacement menu texture also requires the helper's drawing
correction. Steam's regular Play button can show misplaced texture fragments.
Close the game and launch through the installed ultrawide shortcut. To return
to regular Steam launching, restore the original files with the installer.

## Unsupported RT3.exe

Only the SHA-256 listed in the README has known addresses and signatures. Steam,
CD, localized, and community-patched executables may differ. Do not disable the
check or substitute addresses. Run **Check installation** and report the hash
with your game edition and installed game patches.

## Unsupported D3D8.dll / another graphics wrapper is installed

This version uses the included dgVoodoo 2.87.5 x86 DLL. Preserve your existing
wrapper before removing it. Do not put the x64 version into this 32-bit game.
No wrapper DLL should be copied into the Windows system folders.

## The watermark is still visible

The installer sets `[DirectX] dgVoodooWatermark = false` in `dgVoodoo.conf`.
Restart the game after changing that setting. A watermark in an already-running
session does not mean the saved setting failed.

To disable it without restarting, open `dgVoodooCpl.exe` in the game folder,
select **[Running] Railroad Tycoon 3**, open **DirectX**, uncheck
**dgVoodoo Watermark**, and click **Apply**. The running-instance setting and the
saved game-folder configuration are separate; the installer handles the latter.

## Missing city names or icons near the old bottom HUD strip

Revision 9 updates the logical camera rectangle as well as the rendering
viewport. Earlier experimental revisions expanded only the viewport, leaving
labels and visibility calculations at the old 70% height. Update and relaunch.
If the problem persists, report the scenario, active overview mode, camera zoom,
resolution, and whether the label disappears at a consistent screen boundary.

## World Overview, briefing, or minimap clicks are offset

Make sure only one helper is attached and that the resolution has not changed.
The World Overview uses a dedicated right/bottom anchor. Briefings have their
own input scope; the minimap also has a separate raw-mouse polling path.
If one window still fails, include its name and an annotated screenshot.

## WASD does nothing

Give the game focus and close text-entry dialogs. Look for
`cameraKeysRefreshed` in the log: the expected values are `[87, 83, 65, 68]`.
If you changed hotkeys while playing, save and relaunch through the helper.

## Permission denied

Use a game library where your Windows account can write the game files. Run the
game and helper at the same privilege level. The installer does not silently
elevate or change folder permissions.

## The helper reports another instance

Leave the existing helper running if it works. To detach this release cleanly,
use the source CLI `stop` command or create an empty file named `STOP` inside
`RT3Ultrawide`. Do not attach multiple Frida tools to RT3 at the same time.
Save and restart the game before changing between instrumentation tools.

## Restoring settings

Use **Restore original** with the game closed. If a backup checksum fails, keep
all backups and investigate the damaged file before retrying. Backups are local
to the installation and are not uploaded anywhere.

## Reporting a problem

Open an issue with the game edition/hash, Windows version, GPU, resolution, exact
window or action, and the relevant log excerpt. Logs and diagnostic layout files
stay on your computer. Review them for local paths before posting. Do not upload
the game executable, full memory dumps, proprietary assets, or private saves.
