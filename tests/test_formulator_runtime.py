import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMULATOR = ROOT / "Formulator"
if str(FORMULATOR) not in sys.path:
    sys.path.insert(0, str(FORMULATOR))

from kungfus import SUPPORT_KUNGFU
from utils.analyzer import Analyzer
from utils.parser import Parser


def test_embedded_runtime_registers_only_wufang():
    assert set(SUPPORT_KUNGFU) == {10627}
    assert Parser is not None
    assert Analyzer is not None


def test_retained_kungfu_packages_remain_importable():
    packages = sorted(
        path.name
        for path in (FORMULATOR / "kungfus").iterdir()
        if path.is_dir() and path.name != "__pycache__"
    )
    assert "wu_fang" in packages
    for package in packages:
        importlib.import_module(f"kungfus.{package}")
