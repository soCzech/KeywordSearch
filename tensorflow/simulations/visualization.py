import os
from PIL import Image as pImage, ImageDraw as pDraw, ImageFont as pFont


class VisImgInstance:

    def __init__(self, image_dims, max_iterations, max_images):
        self.image = pImage.new('RGB', (image_dims[0] * max_iterations, image_dims[1] * max_images), (255, 255, 255))
        self.canvas = pDraw.Draw(self.image)
        self.current = -1
        self.iteration = -1


class SimilarityVisualization:

    def __init__(self, filename, image_dims, max_images, max_iterations, image_dir):
        self.filename = filename
        self.instances = dict()

        self.image_dims = image_dims
        self.max_images = max_images
        self.max_iterations = max_iterations
        self.image_dir = image_dir

        self.curr_instance = None

    def new_image(self, plot_name, image_id):
        if plot_name not in self.instances:
            self.instances[plot_name] = VisImgInstance(self.image_dims, self.max_iterations, self.max_images)

        self.curr_instance = self.instances[plot_name]

        if self.curr_instance.current >= self.max_images:
            return

        self.curr_instance.current += 1
        self.curr_instance.iteration = 0
        self.new_iteration(image_id, text="ID " + str(image_id))

    def new_iteration(self, image_id, text=None):
        if self.curr_instance.iteration >= self.max_iterations:
            return

        x = self.curr_instance.iteration * self.image_dims[0]
        y = self.curr_instance.current * self.image_dims[1]

        img = pImage.open(os.path.join(self.image_dir, str(image_id).zfill(7) + ".jpg"))
        img = img.resize((self.image_dims[0], self.image_dims[1]))
        self.curr_instance.image.paste(img, (x, y, x + self.image_dims[0], y + self.image_dims[1]))

        if text is not None:
            font = pFont.truetype("courbd", 18)
            if isinstance(text, list):
                self.curr_instance.canvas.text((x, y), text[0], fill=(0, 255, 0, 255), font=font)
                self.curr_instance.canvas.text((x, y + self.image_dims[1] - 18), text[1],
                                               fill=(0, 255, 0, 255), font=font)
            else:
                self.curr_instance.canvas.text((x, y), text, fill=(0, 255, 0, 255), font=font)
        self.curr_instance.iteration += 1

    def save(self):
        for k in self.instances.keys():
            self.instances[k].image.save(self.filename + '-' + k + ".jpg", "JPEG")
