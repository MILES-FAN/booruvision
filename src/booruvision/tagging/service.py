"""Thread-safe facade over the interrogators, used by the UI."""

import logging
import threading

from PIL import Image

from booruvision.tagging.interrogator import Interrogator
from booruvision.tagging.models import DEFAULT_MODEL, interrogators

log = logging.getLogger(__name__)


class TaggerService:
    def __init__(self, model: str = DEFAULT_MODEL, threshold: float = 0.35, unload_after: bool = False):
        self.model = model
        self.threshold = threshold
        self.unload_after = unload_after
        self._lock = threading.Lock()

    @staticmethod
    def available_models() -> list[str]:
        return list(interrogators)

    def set_model(self, model: str) -> None:
        if model not in interrogators:
            raise KeyError(f"Unknown model: {model}")
        with self._lock:
            if model != self.model:
                interrogators[self.model].unload()
            self.model = model

    def unload(self) -> None:
        with self._lock:
            interrogators[self.model].unload()

    def tag(self, image: Image.Image) -> dict[str, float]:
        """Run the current model on `image`. Blocking; call from a worker thread."""
        with self._lock:
            interrogator = interrogators[self.model]
            log.info("Using model: %s, threshold: %s", self.model, self.threshold)
            try:
                _, tags = interrogator.interrogate(image)
            finally:
                if self.unload_after:
                    interrogator.unload()
            return Interrogator.postprocess_tags(tags, self.threshold)
