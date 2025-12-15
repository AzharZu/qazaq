# Alias package so that importing ``app`` resolves to the real backend/app
# even if Python picks up this nested backend/backend/app package first.
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]  # .../backend
REAL_APP = ROOT / "app"

# Ensure the real backend root is on sys.path
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Point this package's search path to the real app package directory.
__path__ = [str(REAL_APP)]  # type: ignore
