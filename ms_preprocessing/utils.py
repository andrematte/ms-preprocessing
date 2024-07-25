import os
import logging
import tifffile

import numpy as np

from glob import glob
from micasense.metadata import Metadata


def set_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)8s] -> %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        # filename="logfile.log",
    )


def retrieve_files(path: str, panchro: bool = False):
    """
    Scans list of files, remove the panchromatic band file (Band number 6) if panchro==false.
    """
    file_list = glob(os.path.join(path, "IMG*.tif"))
    pan_files = glob(os.path.join(path, "IMG*_6.tif"))

    if panchro:
        return sorted(list(set(file_list)))
    else:
        return sorted(list(set(file_list) - set(pan_files)))


def read_directory(path: str, panchro: bool = False):
    """
    Scans the directory containing the images. It is assumed that
    the image containing the reflectance panel is named 'IMG_0000_*.tif'.
    Returns a dictionary containing the filepaths for each image.
    """
    file_list = retrieve_files(path, panchro=panchro)

    dictionary = {}

    for x in file_list:
        key = x[-14:-6]
        group = dictionary.get(key, [])
        group.append(x)
        dictionary[key] = group

    return dictionary


def get_image_list(image_dict: dict, panel_name: str):
    """
    Remove the panel image from the image_dict and returns list of images.
    """
    return list(set(image_dict.keys()) - set([panel_name]))


def load_metadata(path, remove_list=[]):
    """
    Retrive image metadata from a single .tif image file (single band).
    """
    # Micasense Function
    metadata = Metadata(path).get_all()

    # Filter metadata fields contained in remove_list
    for key in remove_list:
        if key in metadata.keys():
            del metadata[key]

    return metadata


def transfer_metadata(original_path, new_path, config_path="exiftool.config"):
    """
    Transfer metadata from one file to another.
    Requires configuration file path.
    """
    os.system(
        f"exiftool -config {config_path} -tagsfromfile {original_path} -all:all>all:all {new_path}"
    )

    logging.debug(f"Transfered metadata from {original_path} to {new_path}.")


def save_as_tiff(array, load_paths, save_path, name):
    """
    Saves an array as tiff files, one band per file.
    """
    create_directory(save_path)

    bands_suffix = {
        "Blue": "_1.tiff",
        "Green": "_2.tiff",
        "Red": "_3.tiff",
        "NIR": "_4.tiff",
        "Red edge": "_5.tiff",
    }

    for band_index, load_path in enumerate(load_paths):
        # Capture single band metadata
        metadata = load_metadata(load_path)

        # Set save path
        file_suffix = bands_suffix[metadata["XMP:BandName"]]
        filename = name + file_suffix
        current_save_path = os.path.join(save_path, filename)

        # Save image
        tifffile.imwrite(current_save_path, array[:, :, band_index])

        logging.info(f"Saved {filename} as .tiff file.")

        # Write metadata
        transfer_metadata(load_path, current_save_path)


def load_tiff(path):
    """
    Load multichannel tiff image as a numpy array.
    """
    image = tifffile.imread(path)
    logging.debug(f"Loaded file from {path}.")
    return np.moveaxis(image, 0, -1)


def create_directory(directory):
    """
    Create a new directory if it does not exist.

    Args:
        directory (str): Path to directory
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.debug("Creating directory - ", directory)
