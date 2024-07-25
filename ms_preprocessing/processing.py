import logging
import settings
from micasense import imageutils


def compute_panel_irradiance(panel_capture):
    """
    Computes irradiance values from panel capture object.
    """
    assert panel_capture is not None
    assert panel_capture.panel_albedo() is not None

    logging.info("Panel image detected.")

    panel_reflectance_by_band = panel_capture.panel_albedo()
    panel_irradiance = panel_capture.panel_irradiance(
        panel_reflectance_by_band
    )

    logging.info("Panel irradiance captured.")

    return panel_irradiance


def compute_warp_matrices(capture):
    """
    Returns warp matrices for image alignment.
    """
    warp_matrices, alignment_pairs = imageutils.align_capture(
        capture,
        ref_index=settings.MATCH_INDEX,
        max_iterations=settings.MAX_ALIGN_ITERATIONS,
        warp_mode=settings.WARP_MODE,
        pyramid_levels=settings.PYRAMID_LEVELS,
    )
    return warp_matrices, alignment_pairs


def align_image(capture):
    """
    Perform image alignment operations. Returns aligned bands.
    """
    warp_matrices, _ = compute_warp_matrices(capture)

    cropped_dimensions, edges = imageutils.find_crop_bounds(
        capture, warp_matrices, warp_mode=settings.WARP_MODE
    )

    aligned = imageutils.aligned_capture(
        capture,
        warp_matrices,
        settings.WARP_MODE,
        cropped_dimensions,
        settings.MATCH_INDEX,
        img_type=settings.IMG_TYPE,
    )

    return aligned
