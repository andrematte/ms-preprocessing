import argparse
import os
import time
from pathlib import Path

import micasense.capture as capture
import micasense.imageset as imageset
import numpy as np
import pandas as pd
from mapboxgl.utils import df_to_geojson
from skimage.transform import ProjectiveTransform

parser = argparse.ArgumentParser(
    prog="MicaSenseBatchProcessing",
    description="Create aligned, radiometrically corrected image stacks from raw MicaSense imagery",
    epilog="epilog",
)

parser.add_argument("--imagepath", required=True, type=Path)
parser.add_argument("--outputpath", required=True, type=Path)
parser.add_argument("--alignmentimage")

args = parser.parse_args()

print(args.imagepath)

panchro_cam = True
pan_sharpen = True
use_dls = False

image_path = args.imagepath

# these will return lists of image paths as strings
panel_names = list(image_path.glob("IMG_0000_*.tif"))
panel_names = [x.as_posix() for x in panel_names]
print(panel_names)

# panel_names = args.panelpath
panelCap = capture.Capture.from_filelist(panel_names)

# destinations on your computer to put the stacks
# and RGB thumbnails
outputPath = args.outputpath.resolve().as_posix()
print(outputPath)
thumbnailPath = args.outputpath / "thumbnails"
thumbnailPath = thumbnailPath.resolve().as_posix()
print(thumbnailPath)

cam_model = panelCap.camera_model
cam_serial = panelCap.camera_serial
print(f"cam_model: {cam_model}, cam_serial: {cam_serial}")


cam_serial = panelCap.camera_serial
print("Serial number:", cam_serial)

overwrite = True  # can be set to False to continue interrupted processing
generateThumbnails = True

# Allow this code to align both radiance and reflectance images; but excluding
# a definition for panelNames above, radiance images will be used
# For panel images, efforts will be made to automatically extract the panel information
# but if the panel/firmware is before Altum 1.3.5, RedEdge 5.1.7 the panel reflectance
# will need to be set in the panel_reflectance_by_band variable.
# Note: radiance images will not be used to properly create NDVI/NDRE images below.
panelCap = capture.Capture.from_filelist(panel_names)

if panelCap is not None:
    if panelCap.panel_albedo() is not None and not any(
        v is None for v in panelCap.panel_albedo()
    ):
        panel_reflectance_by_band = panelCap.panel_albedo()
    else:
        panel_reflectance_by_band = [0.49] * len(
            panelCap.eo_band_names()
        )  # RedEdge band_index order

    panel_irradiance = panelCap.panel_irradiance(panel_reflectance_by_band)
    img_type = "reflectance"
else:
    if use_dls:
        img_type = "reflectance"
    else:
        img_type = "radiance"

imgset = imageset.ImageSet.from_directory(image_path)

data, columns = imgset.as_nested_lists()
df = pd.DataFrame.from_records(data, index="timestamp", columns=columns)

geojson_data = df_to_geojson(df, columns[3:], lat="latitude", lon="longitude")

warp_matrices_filename = cam_serial + "_warp_matrices_SIFT.npy"

if Path("./" + warp_matrices_filename).is_file():
    print("Found existing warp matrices for camera", cam_serial)
    load_warp_matrices = np.load(warp_matrices_filename, allow_pickle=True)
    loaded_warp_matrices = []
    for matrix in load_warp_matrices:
        if panchro_cam:
            transform = ProjectiveTransform(matrix=matrix.astype("float64"))
            loaded_warp_matrices.append(transform)
        else:
            loaded_warp_matrices.append(matrix.astype("float32"))

    if panchro_cam:
        warp_matrices_SIFT = loaded_warp_matrices
    else:
        warp_matrices = loaded_warp_matrices
    print(
        "Loaded warp matrices from",
        Path("./" + warp_matrices_filename).resolve(),
    )
else:
    print(
        "No warp matrices found at expected location:", warp_matrices_filename
    )

if not os.path.exists(outputPath):
    os.makedirs(outputPath)
if generateThumbnails and not os.path.exists(thumbnailPath):
    os.makedirs(thumbnailPath)

# Save out geojson data, so we can open the image capture locations in our GIS
with open(os.path.join(outputPath, "imageSet.json"), "w") as f:
    f.write(str(geojson_data))

try:
    irradiance = panel_irradiance + [0]
except NameError:
    irradiance = None

start = time.time()
for i, capture in enumerate(imgset.captures):
    outputFilename = capture.uuid + ".tif"
    thumbnailFilename = capture.uuid + ".jpg"
    fullOutputPath = os.path.join(outputPath, outputFilename)
    fullThumbnailPath = os.path.join(thumbnailPath, thumbnailFilename)
    if (not os.path.exists(fullOutputPath)) or overwrite:
        if len(capture.images) == len(imgset.captures[0].images):
            if panchro_cam:
                reflectance = (
                    capture.radiometric_pan_sharpened_aligned_capture(
                        warp_matrices=warp_matrices_SIFT,
                        irradiance_list=irradiance,
                        img_type="reflectance",
                    )
                )
            # capture.save_capture_as_stack(
            #     fullOutputPath,
            #     pansharpen=pan_sharpen,
            #     sort_by_wavelength=False,
            # )
            capture.save_capture_as_individual_bands(
                output_dir=outputPath,
                id=capture.uuid,
                pansharpen=pan_sharpen,
                sort_by_wavelength=False,
            )
            if generateThumbnails:
                capture.save_capture_as_rgb(fullThumbnailPath)

    current = time.time()
    diff = current - start
    print(
        "Saved stack",
        str(i),
        "of",
        str(len(imgset.captures)),
        "in",
        str(int(diff)),
        "seconds",
        end="\r",
    )
    capture.clear_image_data()
end = time.time()

print("Saving time:", end - start)
