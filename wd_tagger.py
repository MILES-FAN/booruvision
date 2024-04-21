from tagger.interrogator import Interrogator, WaifuDiffusionInterrogator
from PIL import Image
from pathlib import Path

from tagger.interrogators import interrogators

class wd_tagger:
    def image_interrogate(self,image, threshold, model):
        interrogator = interrogators[model]
        print(f"Using model: {model}\n Threshold: {threshold}")
        im = image
        result = interrogator.interrogate(im)
        if(self.unloadAfterAnalysis):
            interrogator.unload()

        return Interrogator.postprocess_tags(result[1], threshold)

    def __init__(self, threshold=0.35, model='wd-swinv2-v3'):
        self.threshold = threshold
        self.model = model
        self.unloadAfterAnalysis = False

    def set_threshold_and_model(self, threshold, model):
        self.threshold = threshold
        self.model = model

    def tag_image_by_path(self, image_path):
        image = Image.open(image_path)
        tags = self.image_interrogate(image, threshold=self.threshold, model=self.model)
        return tags
    
    def tag_image_by_pil(self, image):
        tags = self.image_interrogate(image, threshold=self.threshold, model=self.model)
        return tags

    def tag_images(self, image_dir, ext='.txt'):
        d = Path(image_dir)
        for f in d.iterdir():
            if not f.is_file() or f.suffix not in ['.png', '.jpg', '.webp']:
                continue
            image_path = Path(f)
            print('processing:', image_path)
            tags = self.image_interrogate(image_path, threshold=self.threshold, model=self.model)
            tags_str = ", ".join(tags.keys())
            with open(f.parent / f"{f.stem}{ext}", "w") as fp:
                fp.write(tags_str)

    def tag_file(self, image_path):
        tags = self.image_interrogate(Path(image_path), threshold=self.threshold, model=self.model)
        tags_str = ", ".join(tags.keys())
        print(tags_str)
