import glob
import os
import time
from pathlib import Path

import matplotlib.pyplot as plt
import micasense.capture as capture
import numpy
import numpy as np
import skimage
from skimage.transform import (
    FundamentalMatrixTransform,
    ProjectiveTransform,
    estimate_transform,
    matrix_transform,
    resize,
    warp,
)

plt.rcParams["figure.facecolor"] = "w"

imagePath = Path("../data")

imageNames = list(imagePath.glob("IMG_0278_*.tif"))
imageNames = [x.as_posix() for x in imageNames]

panelNames = list(imagePath.glob("IMG_0000_*.tif"))
panelNames = [x.as_posix() for x in panelNames]

if panelNames is not None:
    panelCap = capture.Capture.from_filelist(panelNames)
else:
    panelCap = None

thecapture = capture.Capture.from_filelist(imageNames)

# get camera model for future use
cam_model = thecapture.camera_model
# if this is a multicamera system like the RedEdge-MX Dual,
# we can combine the two serial numbers to help identify
# this camera system later.
if len(thecapture.camera_serials) > 1:
    cam_serial = "_".join(thecapture.camera_serials)
    print(cam_serial)
else:
    cam_serial = thecapture.camera_serial

print("Camera model:", cam_model)
print("Bit depth:", thecapture.bits_per_pixel)
print("Camera serial number:", cam_serial)
print("Capture ID:", thecapture.uuid)

# determine if this sensor has a panchromatic band
if cam_model == "RedEdge-P" or cam_model == "Altum-PT":
    panchroCam = True
else:
    panchroCam = False
    panSharpen = False

if panelCap is not None:
    if panelCap.panel_albedo() is not None:
        panel_reflectance_by_band = panelCap.panel_albedo()
    else:
        panel_reflectance_by_band = [0.49] * len(
            thecapture.eo_band_names()
        )  # RedEdge band_index order
    panel_irradiance = panelCap.panel_irradiance(panel_reflectance_by_band)
    irradiance_list = panelCap.panel_irradiance(panel_reflectance_by_band) + [
        0
    ]  # add to account for uncalibrated LWIR band, if applicable
    img_type = "reflectance"
    thecapture.plot_undistorted_reflectance(panel_irradiance)
else:
    if thecapture.dls_present():
        img_type = "reflectance"
        irradiance_list = thecapture.dls_irradiance() + [0]
        thecapture.plot_undistorted_reflectance(thecapture.dls_irradiance())
    else:
        img_type = "radiance"
        thecapture.plot_undistorted_radiance()
        irradiance_list = None

if panchroCam:
    warp_matrices_filename = cam_serial + "_warp_matrices_SIFT.npy"
else:
    warp_matrices_filename = cam_serial + "_warp_matrices_opencv.npy"

if Path("./" + warp_matrices_filename).is_file():
    print("Found existing warp matrices for camera", cam_serial)
    load_warp_matrices = np.load(warp_matrices_filename, allow_pickle=True)
    loaded_warp_matrices = []
    for matrix in load_warp_matrices:
        if panchroCam:
            transform = ProjectiveTransform(matrix=matrix.astype("float64"))
            loaded_warp_matrices.append(transform)
        else:
            loaded_warp_matrices.append(matrix.astype("float32"))
    print("Warp matrices successfully loaded.")

    if panchroCam:
        warp_matrices_SIFT = loaded_warp_matrices
    else:
        warp_matrices = loaded_warp_matrices
else:
    print(
        "No existing warp matrices found. Create them later in the notebook."
    )
    warp_matrices_SIFT = False
    warp_matrices = False

if panchroCam:
    # set to True if you'd like to ignore existing warp matrices and create new ones
    regenerate = True
    st = time.time()
    if not warp_matrices_SIFT or regenerate:
        print("Generating new warp matrices...")
        warp_matrices_SIFT = thecapture.SIFT_align_capture(min_matches=10)

    sharpened_stack, upsampled = (
        thecapture.radiometric_pan_sharpened_aligned_capture(
            warp_matrices=warp_matrices_SIFT,
            irradiance_list=irradiance_list,
            img_type=img_type,
        )
    )

    # we can also use the Rig Relatives from the image metadata to do a quick, rudimentary alignment
    #     warp_matrices0=thecapture.get_warp_matrices(ref_index=5)
    #     sharpened_stack,upsampled = radiometric_pan_sharpen(thecapture,warp_matrices=warp_matrices0)

    print("Pansharpened shape:", sharpened_stack.shape)
    print("Upsampled shape:", upsampled.shape)
    # re-assign to im_aligned to match rest of code
    im_aligned = upsampled
    et = time.time()
    elapsed_time = et - st
    print("Alignment and pan-sharpening time:", int(elapsed_time), "seconds")

if panchroCam:
    working_wm = warp_matrices_SIFT
else:
    working_wm = warp_matrices
if not Path("./" + warp_matrices_filename).is_file() or regenerate:
    temp_matrices = []
    for x in working_wm:
        if isinstance(x, numpy.ndarray):
            temp_matrices.append(x)
        if isinstance(x, skimage.transform._geometric.ProjectiveTransform):
            temp_matrices.append(x.params)
    np.save(
        warp_matrices_filename,
        np.array(temp_matrices, dtype=object),
        allow_pickle=True,
    )
    print("Saved to", Path("./" + warp_matrices_filename).resolve())
else:
    print(
        "Matrices already exist at",
        Path("./" + warp_matrices_filename).resolve(),
    )
