"""Thread-safe facade over the interrogators, used by the UI."""

import logging
import threading

from PIL import Image

from booruvision.tagging.interrogator import Interrogator
from booruvision.tagging.models import DEFAULT_MODEL, interrogators
from booruvision.tagging.prediction import Prediction

log = logging.getLogger(__name__)


class TaggerService:
    def __init__(self, model: str = DEFAULT_MODEL, unload_after: bool = False):
        self.model = model
        self.unload_after = unload_after
        self._lock = threading.Lock()

    @staticmethod
    def available_models() -> list[str]:
        return list(interrogators)

    @staticmethod
    def info(model: str) -> Interrogator:
        """The interrogator for `model`, for its categories and default thresholds only."""
        return interrogators[model]

    def is_loaded(self) -> bool:
        return interrogators[self.model].model is not None

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

    def predict(self, image: Image.Image) -> Prediction:
        """Run the current model on `image`. Blocking; call from a worker thread."""
        with self._lock:
            interrogator = interrogators[self.model]
            log.info("Using model: %s", self.model)
            try:
                return interrogator.interrogate(image)
            finally:
                if self.unload_after:
                    interrogator.unload()
