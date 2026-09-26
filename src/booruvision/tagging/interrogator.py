"""ONNX interrogators for WD tagger and ML-Danbooru models."""

import csv
import json
import logging
import re
from pathlib import Path

import numpy as np
from huggingface_hub import hf_hub_download
from PIL import Image

from booruvision.tagging import preprocess

log = logging.getLogger(__name__)

tag_escape_pattern = re.compile(r"([\\()])")

use_cpu = True


def _providers() -> list[str]:
    # https://onnxruntime.ai/docs/execution-providers/
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    if use_cpu:
        providers.pop(0)
    return providers


class Interrogator:
    @staticmethod
    def postprocess_tags(
        tags: dict[str, float],
        threshold=0.35,
        additional_tags: list[str] | None = None,
        exclude_tags: list[str] | None = None,
        sort_by_alphabetical_order=False,
        add_confident_as_weight=False,
        replace_underscore=False,
        replace_underscore_excludes: list[str] | None = None,
        escape_tag=False,
    ) -> dict[str, float]:
        additional_tags = additional_tags or []
        exclude_tags = exclude_tags or []
        replace_underscore_excludes = replace_underscore_excludes or []

        for t in additional_tags:
            tags[t] = 1.0

        tags = {
            t: c
            # sort by tag name or confidence
            for t, c in sorted(
                tags.items(),
                key=lambda i: i[0 if sort_by_alphabetical_order else 1],
                reverse=not sort_by_alphabetical_order,
            )
            if c >= threshold and t not in exclude_tags
        }

        new_tags = []
        for tag, confidence in tags.items():
            new_tag = tag

            if replace_underscore and tag not in replace_underscore_excludes:
                new_tag = new_tag.replace("_", " ")

            if escape_tag:
                new_tag = tag_escape_pattern.sub(r"\\\1", new_tag)

            if add_confident_as_weight:
                new_tag = f"({new_tag}:{confidence})"

            new_tags.append((new_tag, confidence))

        return dict(new_tags)

    def __init__(self, name: str) -> None:
        self.name = name
        self.model = None
        self.tags = None

    def load(self) -> None:
        raise NotImplementedError()

    def unload(self) -> bool:
        if self.model is None:
            return False
        self.model = None
        self.tags = None
        log.info("Unloaded %s", self.name)
        return True

    def interrogate(self, image: Image.Image) -> tuple[dict[str, float], dict[str, float]]:
        """Return (rating confidences, tag confidences)."""
        raise NotImplementedError()


class WaifuDiffusionInterrogator(Interrogator):
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
            self.tags = [row["name"] for row in csv.DictReader(f)]

    def interrogate(self, image: Image.Image) -> tuple[dict[str, float], dict[str, float]]:
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

        pairs = [(name, float(conf)) for name, conf in zip(self.tags, confidences, strict=True)]

        # first 4 items are for rating (general, sensitive, questionable, explicit)
        ratings = dict(pairs[:4])
        tags = dict(pairs[4:])
        return ratings, tags


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

    def interrogate(self, image: Image.Image) -> tuple[dict[str, float], dict[str, float]]:
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

        tags = {tag: float(conf) for tag, conf in zip(self.tags, y.flatten(), strict=False)}
        return {}, tags
