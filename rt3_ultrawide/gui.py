"""A compact Windows installer/launcher; all user-facing text is English."""
import ctypes
import json
from pathlib import Path
import queue
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .install import install, uninstall
from .runtime import launch


def find_game():
    for parent in Path(sys.executable).parents:
        if (parent / "RT3.exe").is_file():
            return str(parent)
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            steam = Path(winreg.QueryValueEx(key, "SteamPath")[0])
        libraries = [steam]
        index = steam / "steamapps/libraryfolders.vdf"
        if index.exists():
            libraries.extend(Path(p.replace("\\\\", "\\")) for p in
                             re.findall(r'"path"\s+"([^"]+)"', index.read_text(encoding="utf-8")))
        for library in libraries:
            game = library / "steamapps/common/Railroad Tycoon 3"
            if (game / "RT3.exe").is_file():
                return str(game)
    except (OSError, ImportError):
        pass
    return ""


def show():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (OSError, AttributeError):
        pass
    root = tk.Tk()
    root.title("Railroad Tycoon 3 • Ultrawide")
    root.geometry("740x530")
    root.minsize(660, 500)
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    ttk.Label(frame, text="Railroad Tycoon 3 Ultrawide", font=("Segoe UI", 19, "bold")).grid(sticky="w")
    ttk.Label(frame, text=f"v{__version__} · Experimental · Supported Steam build only").grid(sticky="w", pady=(4, 18))
    ttk.Label(frame, text="Borderless display  ·  Split HUD  ·  WASD camera  ·  Space to pause").grid(sticky="w", pady=(0, 18))
    ttk.Label(frame, text="Game folder (contains RT3.exe)").grid(sticky="w")
    location = ttk.Frame(frame)
    location.grid(sticky="ew", pady=(5, 14))
    location.columnconfigure(0, weight=1)
    game = tk.StringVar(value=find_game())
    ttk.Entry(location, textvariable=game).grid(row=0, column=0, sticky="ew", padx=(0, 8))

    def browse():
        selected = filedialog.askdirectory(title="Choose the Railroad Tycoon 3 folder")
        if selected:
            game.set(selected)

    ttk.Button(location, text="Browse…", command=browse).grid(row=0, column=1)
    dimensions = ttk.Frame(frame)
    dimensions.grid(sticky="w", pady=(0, 14))
    width = tk.StringVar(value=str(root.winfo_screenwidth()))
    height = tk.StringVar(value=str(root.winfo_screenheight()))
    ttk.Label(dimensions, text="Resolution").pack(side="left", padx=(0, 12))
    ttk.Entry(dimensions, textvariable=width, width=7).pack(side="left")
    ttk.Label(dimensions, text=" × ").pack(side="left")
    ttk.Entry(dimensions, textvariable=height, width=7).pack(side="left")
    ttk.Label(dimensions, text="  Use your monitor's native resolution").pack(side="left")
    ttk.Label(frame, text="Save and exit the game before installing or restoring.\n"
              "dgVoodoo 2.87.5 is included. Original settings are backed up locally.",
              wraplength=660).grid(sticky="w", pady=(0, 16))
    buttons = ttk.Frame(frame)
    buttons.grid(sticky="w", pady=(0, 12))
    status = tk.StringVar(value="Choose your game folder, then install. After installation, use Launch.")
    ttk.Label(frame, textvariable=status, wraplength=650, justify="left").grid(sticky="nw")
    frame.rowconfigure(8, weight=1)
    ttk.Label(frame, text="Backups and logs: <game folder> / RT3Ultrawide\n"
              "Help: github.com/proteusbr1/TR3-ultrawide", foreground="#555555").grid(row=9, sticky="sw", pady=(18, 0))
    results = queue.Queue()
    active = False
    controls = []

    def work(action):
        nonlocal active
        if active:
            return
        try:
            folder = Path(game.get())
            if not game.get() or not (folder / "RT3.exe").is_file():
                raise ValueError("Select the folder containing RT3.exe.")
            w, h = int(width.get()), int(height.get())
        except ValueError as error:
            messagebox.showerror("Check your settings", str(error))
            return
        if action == "restore" and not messagebox.askyesno("Restore original files",
                "Restore the settings and files saved before installation?\n\n"
                "Your current files will also be copied to a separate backup first.\n"
                "The game must be closed. Saves are not modified."):
            return
        active = True
        for button in controls:
            button.state(["disabled"])
        status.set("Working… Please keep this window open.")

        def background():
            try:
                if action == "install":
                    result = install(folder, w, h)
                elif action == "restore":
                    result = uninstall(folder, preserve_changed=True)
                elif action == "doctor":
                    from .__main__ import doctor
                    report = doctor(folder)
                    result = "\n".join([
                        "Supported game build: " + ("Yes" if report["supported_executable"] else "No"),
                        "Supported graphics wrapper: " + ("Yes" if report["supported_wrapper"] else "No — install the included version"),
                        "Game configuration present: " + ("Yes" if report["engine_config_exists"] and report["hotkeys_exist"] else "No — run the original game once"),
                        f"Helper {report['version']} · Frida {report['frida']}",
                    ])
                else:
                    result = launch(folder)
                results.put((True, result))
            except Exception as error:
                results.put((False, str(error)))
        threading.Thread(target=background, daemon=True).start()

    for text, action in [("Install / Update", "install"), ("Launch", "launch"),
                         ("Check installation", "doctor"), ("Restore original", "restore")]:
        button = ttk.Button(buttons, text=text, command=lambda a=action: work(a))
        button.pack(side="left", padx=(0, 8))
        controls.append(button)

    def poll():
        nonlocal active
        try:
            success, result = results.get_nowait()
            active = False
            for button in controls:
                button.state(["!disabled"])
            status.set(result)
            if not success:
                messagebox.showerror("Operation could not finish", result)
        except queue.Empty:
            pass
        root.after(150, poll)

    def close():
        if active:
            messagebox.showinfo("Operation in progress", "Please wait for the current operation to finish.")
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    poll()
    root.mainloop()
