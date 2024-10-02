import os
import logging
import numpy as np
from tqdm import tqdm
from glob import glob
from utils import set_logger, read_directory, get_image_list, save_as_tiff
from processing import compute_panel_irradiance, align_image
from micasense import capture


set_logger()

image_path = "../data"
output_path = "../output/"
panel_file_number = "0000"
skip_alignment = True

# def multispectral_batch_processing(image_path, output_path, panel_file_number="0000"):
# ...

logging.info("Starting batch processing...")
logging.info(f"Image Path: {image_path}")
logging.info(f"Output Path: {output_path}")

image_dict = read_directory(image_path)
panel_name = f"IMG_{panel_file_number}"
image_list = sorted(get_image_list(image_dict, panel_name))

panel_capture = capture.Capture.from_filelist(image_dict[panel_name])
panel_irradiance = compute_panel_irradiance(panel_capture)

logging.info(
    f"Number of images to be processed: {len(get_image_list(image_dict, panel_name))}"
)

for image in image_list:
    image_name = image.split("/")[-1]
    # progress.set_description(f"Processing {image_name}")
    logging.info(f"Processing {image_name}.")

    img_capture = capture.Capture.from_filelist(image_dict[image])

    if skip_alignment:
        final_img = []
        img_capture.compute_reflectance(panel_irradiance)

        for band in img_capture.images:
            final_img.append(band.reflectance())

        final_img = np.asarray(final_img).astype("float32")
        final_img = np.moveaxis(final_img, 0, -1)

    else:
        img_capture.compute_undistorted_reflectance(panel_irradiance)
        # TODO Fix align_image error
        # final_img = align_image(img_capture)

    # TODO Fix save_as_tiff error
    # save_as_tiff(final_img, image_dict[image], image_path, image_name)

# for file_backup in glob(f"{image_path}/*_original"):
#     os.remove(file_backup)

logging.info("Batch processing finished!")
