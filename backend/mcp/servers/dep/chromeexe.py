"""Chromedriver path resolution utility.

Usage:
    from backend.mcp.servers.dep.chromeexe import get_chromedriver_path
    path = get_chromedriver_path()

Resolves in order:
1. CHROMEDRIVER_PATH environment variable if exists and points to a file.
2. Local dep directory file (chromedriver(.exe)).
3. System PATH (shutil.which).
Raises FileNotFoundError if none found.
"""
from pathlib import Path
import platform
import shutil
import os

__all__ = ["get_chromedriver_path"]

def get_chromedriver_path() -> str:
    base_dir = Path(__file__).parent
    driver_filename = "chromedriver.exe" if platform.system().lower().startswith("win") else "chromedriver"
    env_override = os.getenv("CHROMEDRIVER_PATH")
    if env_override:
        p = Path(env_override)
        if p.exists():
            return str(p)
    candidate = base_dir / driver_filename
    if candidate.exists():
        return str(candidate)
    which_path = shutil.which("chromedriver")
    if which_path:
        return which_path
    raise FileNotFoundError(
        f"Chromedriver not found. Checked environment CHROMEDRIVER_PATH, {candidate}, and system PATH."
    )
# Package init for dep utilities

