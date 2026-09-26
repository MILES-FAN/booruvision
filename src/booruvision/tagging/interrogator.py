"""ONNX interrogators for WD tagger, PixAI tagger and ML-Danbooru models."""

import csv
import json
import logging
from pathlib import Path

import numpy as np
from huggingface_hub import hf_hub_download
from PIL import Image

from booruvision.tagging import preprocess
from booruvision.tagging.categories import Category
from booruvision.tagging.prediction import Prediction

log = logging.getLogger(__name__)

use_cpu = True


def _providers() -> list[str]:
    # https://onnxruntime.ai/docs/execution-providers/
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    if use_cpu:
        providers.pop(0)
    return providers


class Interrogator:
    # Categories the model predicts, in display order
    categories: tuple[Category, ...] = (Category.GENERAL,)
    # Recommended per-category thresholds; None means the model uses the single global threshold
    default_thresholds: dict[Category, float] | None = None

    def __init__(self, name: str) -> None:
        self.name = name
        self.model = None
        self.tags: list[str] | None = None
        self.tag_categories: list[Category] | None = None

    def load(self) -> None:
        raise NotImplementedError()

    def unload(self) -> bool:
        if self.model is None:
            return False
        self.model = None
        self.tags = None
        self.tag_categories = None
        log.info("Unloaded %s", self.name)
        return True

    def interrogate(self, image: Image.Image) -> Prediction:
        """Score every tag the model knows for `image`."""
        raise NotImplementedError()


# Danbooru category ids used in selected_tags.csv
_DANBOORU_CATEGORY_IDS = {
    0: Category.GENERAL,
    1: Category.STYLE,
    3: Category.COPYRIGHT,
    4: Category.CHARACTER,
    5: Category.META,
    9: Category.RATING,
}


def _danbooru_category(value: str) -> Category:
    return _DANBOORU_CATEGORY_IDS.get(int(value), Category.GENERAL)


class WaifuDiffusionInterrogator(Interrogator):
    categories = (Category.GENERAL, Category.CHARACTER, Category.RATING)

    def __init__(
        self,
        name: str,
        model_path="model.onnx",
        tags_path="selected_tags.csv",
        **kwargs,
    ) -> None:
        super().__init__(name)
        self.model_path = model_path
        self.tags_path = tags_path
        self.kwargs = kwargs

    def download(self) -> tuple[Path, Path]:
        log.info("Loading %s model file from %s", self.name, self.kwargs["repo_id"])
        model_path = Path(hf_hub_download(**self.kwargs, filename=self.model_path))
        tags_path = Path(hf_hub_download(**self.kwargs, filename=self.tags_path))
        return model_path, tags_path

    def load(self) -> None:
        model_path, tags_path = self.download()

        from onnxruntime import InferenceSession

        self.model = InferenceSession(str(model_path), providers=_providers())
        log.info("Loaded %s model from %s", self.name, model_path)

        with open(tags_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.tags = [row["name"] for row in rows]
        self.tag_categories = [_danbooru_category(row["category"]) for row in rows]

    def interrogate(self, image: Image.Image) -> Prediction:
        if self.model is None:
            self.load()

        # code for converting the image and running the model is taken from the link below
        # thanks, SmilingWolf!
        # https://huggingface.co/spaces/SmilingWolf/wd-v1-4-tags/blob/main/app.py
        _, height, _, _ = self.model.get_inputs()[0].shape

        image = preprocess.fill_transparent(image)
        array = np.asarray(image)

        # PIL RGB to OpenCV BGR
        array = array[:, :, ::-1]

        array = preprocess.make_square(array, height)
        array = preprocess.smart_resize(array, height)
        array = array.astype(np.float32)
        array = np.expand_dims(array, 0)

        input_name = self.model.get_inputs()[0].name
        label_name = self.model.get_outputs()[0].name
        confidences = self.model.run([label_name], {input_name: array})[0][0]

        return Prediction(self.tags, self.tag_categories, confidences)


class MLDanbooruInterrogator(Interrogator):
    """Interrogator for the ML-Danbooru model."""

    def __init__(
        self,
        name: str,
        repo_id: str,
        model_path: str,
        tags_path="classes.json",
    ) -> None:
        super().__init__(name)
        self.model_path = model_path
        self.tags_path = tags_path
        self.repo_id = repo_id

    def download(self) -> tuple[str, str]:
        log.info("Loading %s model file from %s", self.name, self.repo_id)
        model_path = hf_hub_download(repo_id=self.repo_id, filename=self.model_path)
        tags_path = hf_hub_download(repo_id=self.repo_id, filename=self.tags_path)
        return model_path, tags_path

    def load(self) -> None:
        model_path, tags_path = self.download()

        from onnxruntime import InferenceSession

        self.model = InferenceSession(model_path, providers=_providers())
        log.info("Loaded %s model from %s", self.name, model_path)

        with open(tags_path, encoding="utf-8") as f:
            self.tags = json.load(f)
        self.tag_categories = [Category.GENERAL] * len(self.tags)

    def interrogate(self, image: Image.Image) -> Prediction:
        if self.model is None:
            self.load()

        image = preprocess.fill_transparent(image)
        image = preprocess.resize(image, 448)

        x = np.asarray(image, dtype=np.float32) / 255
        # HWC -> 1CHW
        x = x.transpose((2, 0, 1))
        x = np.expand_dims(x, 0)

        input_ = self.model.get_inputs()[0]
        output = self.model.get_outputs()[0]
        (y,) = self.model.run([output.name], {input_.name: x})

        # sigmoid
        y = 1 / (1 + np.exp(-y))

        return Prediction(self.tags, self.tag_categories, y.flatten()[: len(self.tags)])


def _sigmoid(x: np.ndarray) -> np.ndarray:
    # Written with exp(-|x|) so large logits of either sign don't overflow
    e = np.exp(-np.abs(x))
    return np.where(x >= 0, 1 / (1 + e), e / (1 + e))


class PixAIV1Interrogator(Interrogator):
    """PixAI Tagger v1.0, as exported to ONNX (weights in an external data file)."""

    categories = (
        Category.GENERAL,
        Category.CHARACTER,
        Category.COPYRIGHT,
        Category.STYLE,
        Category.META,
        Category.RATING,
    )
    # Per-category macro-F1 optima from the model card
    default_thresholds = {
        Category.GENERAL: 0.17,
        Category.CHARACTER: 0.27,
        Category.COPYRIGHT: 0.24,
        Category.STYLE: 0.15,
        Category.META: 0.17,
        Category.RATING: 0.41,
    }
    image_size = 1008
    # External data file named in model.onnx
    data_file = "model.onnx.data"

    def __init__(self, name: str, repo_id: str, revision: str) -> None:
        super().__init__(name)
        self.repo_id = repo_id
        self.revision = revision
        self._weights: np.memmap | None = None

    def _download(self, filename: str) -> str:
        return hf_hub_download(repo_id=self.repo_id, filename=filename, revision=self.revision)

    def load(self) -> None:
        log.info("Loading %s model file from %s", self.name, self.repo_id)
        model_path = self._download("model.onnx")
        data_path = self._download(self.data_file)
        tags_path = self._download("tags.json")

        from onnxruntime import InferenceSession, SessionOptions

        # The Hugging Face cache stores files as symlinks into a shared blob directory, and
        # onnxruntime refuses external data that resolves outside the model's directory. Hand
        # it the weights as a memory-mapped buffer instead.
        self._weights = np.memmap(data_path, dtype=np.uint8, mode="r")
        options = SessionOptions()
        options.add_external_initializers_from_files_in_memory(
            [self.data_file], [self._weights], [len(self._weights)]
        )
        with open(model_path, "rb") as f:
            self.model = InferenceSession(f.read(), options, providers=_providers())
        log.info("Loaded %s model from %s", self.name, model_path)

        with open(tags_path, encoding="utf-8") as f:
            self.tags, self.tag_categories = self.parse_tags(json.load(f))

    @staticmethod
    def parse_tags(tag_map: dict) -> tuple[list[str], list[Category]]:
        """Flatten tags.json ({"categories": [{name, offset, count, tags}]}) into model order."""
        names: list[str] = []
        categories: list[Category] = []
        for group in sorted(tag_map["categories"], key=lambda g: g["offset"]):
            if group["offset"] != len(names) or len(group["tags"]) != group["count"]:
                raise ValueError(f"Inconsistent tag map for category {group['name']!r}")
            names.extend(group["tags"])
            categories.extend([Category(group["name"])] * group["count"])
        if len(names) != tag_map["num_classes"]:
            raise ValueError("Tag map does not cover num_classes")
        return names, categories

    def unload(self) -> bool:
        unloaded = super().unload()
        self._weights = None
        return unloaded

    def interrogate(self, image: Image.Image) -> Prediction:
        if self.model is None:
            self.load()

        x = preprocess.rescale_pad_normalize(image, self.image_size)
        input_name = self.model.get_inputs()[0].name
        (logits,) = self.model.run(None, {input_name: x})
        return Prediction(self.tags, self.tag_categories, _sigmoid(logits[0]))


class PixAIV09Interrogator(Interrogator):
    """PixAI Tagger v0.9 (deepghs ONNX export).

    It predicts general and character tags only. Copyright tags are derived from the characters
    through the `ips` column of the tag list.
    """

    categories = (Category.GENERAL, Category.CHARACTER, Category.COPYRIGHT)
    # From the export's thresholds.csv. Copyright has no threshold of its own: it follows the
    # characters it is derived from.
    default_thresholds = {
        Category.GENERAL: 0.3,
        Category.CHARACTER: 0.85,
    }
    image_size = 448

    def __init__(self, name: str, repo_id: str, revision: str) -> None:
        super().__init__(name)
        self.repo_id = repo_id
        self.revision = revision
        self.derived_copyright: dict[str, list[str]] = {}

    def load(self) -> None:
        log.info("Loading %s model file from %s", self.name, self.repo_id)
        model_path = hf_hub_download(repo_id=self.repo_id, filename="model.onnx", revision=self.revision)
        tags_path = hf_hub_download(
            repo_id=self.repo_id, filename="selected_tags.csv", revision=self.revision
        )

        from onnxruntime import InferenceSession

        self.model = InferenceSession(model_path, providers=_providers())
        log.info("Loaded %s model from %s", self.name, model_path)

        with open(tags_path, newline="", encoding="utf-8") as f:
            self.tags, self.tag_categories, self.derived_copyright = self.parse_tags(csv.DictReader(f))

    @staticmethod
    def parse_tags(rows) -> tuple[list[str], list[Category], dict[str, list[str]]]:
        names: list[str] = []
        categories: list[Category] = []
        ips: dict[str, list[str]] = {}
        for row in rows:
            names.append(row["name"])
            categories.append(_danbooru_category(row["category"]))
            if copyrights := json.loads(row.get("ips") or "[]"):
                ips[row["name"]] = copyrights
        return names, categories, ips

    def unload(self) -> bool:
        self.derived_copyright = {}
        return super().unload()

    def interrogate(self, image: Image.Image) -> Prediction:
        if self.model is None:
            self.load()

        x = preprocess.resize_normalize(image, self.image_size)
        input_name = self.model.get_inputs()[0].name
        (scores,) = self.model.run(["prediction"], {input_name: x})
        return Prediction(self.tags, self.tag_categories, scores[0], self.derived_copyright)
