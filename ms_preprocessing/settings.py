import cv2

# Settings
# General Settings
NUM_BANDS = 5

# Alignment settings
MATCH_INDEX = 2  # Index of the band
MAX_ALIGN_ITERATIONS = 10
WARP_MODE = cv2.MOTION_HOMOGRAPHY  # MOTION_HOMOGRAPHY or MOTION_AFFINE.
PYRAMID_LEVELS = (
    0  # for images with RigRelatives, setting this to 0 or 1 may improve align
)
IMG_TYPE = "reflectance"

# OpenDroneMap settings
ODM_SETTINGS = {
    "boundary": None,
    "cameras": None,
    "fast-orthophoto": True,
    "feature-quality": "ultra",
    "feature-type": "akaze",
    "optimize-disk-space": True,
    "orthophoto-cutline": True,
    "orthophoto-resolution": 2.4,
    "rerun-from": "opensfm",
    "skip-3dmodel": True,
    "texturing-skip-global-seam-leveling": True
}
