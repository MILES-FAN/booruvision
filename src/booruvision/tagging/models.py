"""Registry of the models selectable in config.ini / the settings bar."""

from booruvision.tagging.interrogator import Interrogator, WaifuDiffusionInterrogator

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
}
