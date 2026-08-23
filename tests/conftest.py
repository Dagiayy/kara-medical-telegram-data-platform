import os
import sys
from types import ModuleType

# Settings requires Telegram credentials; supply harmless test values so
# `app.config` can be imported without a real .env file in CI/dev.
os.environ.setdefault("TELEGRAM_API_ID", "12345")
os.environ.setdefault("TELEGRAM_API_HASH", "test_hash")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")


def _install_fake_ultralytics() -> None:
    """kara_detection.detect_images imports `from ultralytics import YOLO` at
    module scope. ultralytics pulls in torch, which is unnecessary weight
    for unit-testing pure detection logic, so we stub it out."""
    if "ultralytics" in sys.modules:
        return
    fake_module = ModuleType("ultralytics")

    class _FakeYOLO:
        def __init__(self, *_args, **_kwargs):
            self.names = {}

        def __call__(self, *_args, **_kwargs):
            return []

    fake_module.YOLO = _FakeYOLO
    sys.modules["ultralytics"] = fake_module


_install_fake_ultralytics()
