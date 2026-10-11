"""Build a Windows x64 folder distribution, notices, ZIP, and SHA-256 file."""
from importlib import metadata
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rt3_ultrawide import __version__
from rt3_ultrawide.install import digest, wrapper_files
from rt3_ultrawide.menu import archive_bytes


def main():
    if sys.platform != "win32":
        raise SystemExit("Build the Windows release on Windows with Python 3.12 x64.")
    wrapper_files()  # Verify the bundled dependency before packaging.
    archive_bytes()
    output = ROOT / "dist" / uuid.uuid4().hex
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
                    "--name", "RT3Ultrawide", "--collect-all", "frida", "--collect-all", "rt3_ultrawide",
                    "--distpath", str(output), "--specpath", "build", "launcher.py"], cwd=ROOT, check=True)
    destination = output / "RT3Ultrawide"
    for name in ["README.md", "LICENSE", "THIRD_PARTY.md", "CHANGELOG.md"]:
        shutil.copy2(ROOT / name, destination / name)
    shutil.copytree(ROOT / "docs", destination / "docs", dirs_exist_ok=True)
    licenses = destination / "licenses"
    licenses.mkdir(exist_ok=True)
    for name in ["frida", "pyinstaller"]:
        package = metadata.distribution(name)
        for entry in package.files:
            if "/licenses/" in str(entry).replace("\\", "/"):
                source = Path(package.locate_file(entry))
                if source.is_file():
                    target = licenses / name / source.name
                    target.parent.mkdir(exist_ok=True)
                    shutil.copy2(source, target)
    base = Path(sys.base_prefix)
    for candidate in [base / "LICENSE.txt", base / "tcl/tcl8.6/license.terms", base / "tcl/tk8.6/license.terms"]:
        if candidate.exists():
            shutil.copy2(candidate, licenses / (candidate.parent.name + "-" + candidate.name))
    # CPython's Windows LICENSE.txt includes Tcl/Tk and other bundled-library notices.
    if not (licenses / (base.name + "-LICENSE.txt")).exists():
        raise RuntimeError("Python license not found; do not distribute an incomplete package.")
    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    archive = Path(shutil.make_archive(str(release / f"RT3-Ultrawide-v{__version__}-windows-x64"),
                                      "zip", destination.parent, destination.name))
    (release / "SHA256SUMS.txt").write_text(f"{digest(archive.read_bytes())}  {archive.name}\n", encoding="ascii")
    (ROOT / "build/latest-package.txt").write_text(str(destination), encoding="utf-8")
    print("Created:", archive)


if __name__ == "__main__":
    main()
