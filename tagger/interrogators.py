from typing import List, Dict

from tagger.interrogator import Interrogator, WaifuDiffusionInterrogator, MLDanbooruInterrogator

interrogators: Dict[str, Interrogator] = {
    'wd-convnext-v3': WaifuDiffusionInterrogator(
        'wd-convnext-v3',
        repo_id='SmilingWolf/wd-convnext-tagger-v3',
    ),
    'wd-swinv2-v3': WaifuDiffusionInterrogator(
        'wd-swinv2-v3',
        repo_id='SmilingWolf/wd-swinv2-tagger-v3',
    ),
    'wd-vit-v3': WaifuDiffusionInterrogator(
        'wd14-vit-v3',
        repo_id='SmilingWolf/wd-vit-tagger-v3',
    ),
    'wd14-convnextv2-v2': WaifuDiffusionInterrogator(
        'wd14-convnextv2-v2', repo_id='SmilingWolf/wd-v1-4-convnextv2-tagger-v2',
        revision='v2.0'
    ),
    'wd14-swinv2-v2': WaifuDiffusionInterrogator(
        'wd14-swinv2-v2', repo_id='SmilingWolf/wd-v1-4-swinv2-tagger-v2',
        revision='v2.0'
    ),
    'wd14-vit-v2': WaifuDiffusionInterrogator(
        'wd14-vit-v2', repo_id='SmilingWolf/wd-v1-4-vit-tagger-v2',
        revision='v2.0'
    ),
    'wd14-moat-v2': WaifuDiffusionInterrogator(
        'wd-v1-4-moat-tagger-v2',
        repo_id='SmilingWolf/wd-v1-4-moat-tagger-v2',
        revision='v2.0'
    ),
}
