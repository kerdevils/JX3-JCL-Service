"""Build a distributable Windows executable with PyInstaller."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).parent.resolve()
FORMULATOR = ROOT / "Formulator"


def main() -> None:
    if not FORMULATOR.is_dir():
        raise SystemExit(f"Formulator source was not found: {FORMULATOR}")

    try:
        import PyInstaller.__main__
    except ImportError as exc:
        raise SystemExit("Install the build dependency first: pip install -r requirements-build.txt") from exc

    separator = os.pathsep
    PyInstaller.__main__.run([
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name", "JX3-JCL-Converter",
        "--paths", str(FORMULATOR),
        "--add-data", f"{ROOT / 'app'}{separator}app",
        "--add-data", f"{FORMULATOR}{separator}formulator",
        str(ROOT / "local_launcher.py"),
    ])


if __name__ == "__main__":
    main()
