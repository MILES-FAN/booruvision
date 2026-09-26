"""Registry of the models selectable in config.ini / the settings bar."""

from booruvision.tagging.interrogator import (
    Interrogator,
    PixAIV09Interrogator,
    PixAIV1Interrogator,
    WaifuDiffusionInterrogator,
)

DEFAULT_MODEL = "wd-swinv2-v3"

interrogators: dict[str, Interrogator] = {
    "wd-convnext-v3": WaifuDiffusionInterrogator(
        "wd-convnext-v3",
        repo_id="SmilingWolf/wd-convnext-tagger-v3",
    ),
    "wd-swinv2-v3": WaifuDiffusionInterrogator(
        "wd-swinv2-v3",
        repo_id="SmilingWolf/wd-swinv2-tagger-v3",
    ),
    "wd-vit-v3": WaifuDiffusionInterrogator(
        "wd-vit-v3",
        repo_id="SmilingWolf/wd-vit-tagger-v3",
    ),
    "wd14-convnextv2-v2": WaifuDiffusionInterrogator(
        "wd14-convnextv2-v2",
        repo_id="SmilingWolf/wd-v1-4-convnextv2-tagger-v2",
        revision="v2.0",
    ),
    "wd14-swinv2-v2": WaifuDiffusionInterrogator(
        "wd14-swinv2-v2",
        repo_id="SmilingWolf/wd-v1-4-swinv2-tagger-v2",
        revision="v2.0",
    ),
    "wd14-vit-v2": WaifuDiffusionInterrogator(
        "wd14-vit-v2",
        repo_id="SmilingWolf/wd-v1-4-vit-tagger-v2",
        revision="v2.0",
    ),
    "wd14-moat-v2": WaifuDiffusionInterrogator(
        "wd-v1-4-moat-tagger-v2",
        repo_id="SmilingWolf/wd-v1-4-moat-tagger-v2",
        revision="v2.0",
    ),
    # Community ONNX exports of pixai-labs/pixai-tagger-*, pinned to a known revision
    "pixai-v1.0": PixAIV1Interrogator(
        "pixai-v1.0",
        repo_id="noaione/pixai-tagger-v1.0-onnx",
        revision="68e8f4f02dd56a5f40c1b7474489fa0f599dec34",
    ),
    "pixai-v0.9": PixAIV09Interrogator(
        "pixai-v0.9",
        repo_id="deepghs/pixai-tagger-v0.9-onnx",
        revision="d8cf666911a2c3d10d586d7823259192313c7eb7",
    ),
}
