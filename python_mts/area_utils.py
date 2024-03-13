""" Estimate area utility function. """
from supermercado.burntiles import burn
import numpy as np


def _convert_precision_to_zoom(precision: str):
    """ Convert a precision value from string to a Mapbox zoom level """
    if precision == "10m":
        return 6

    if precision == "1m":
        return 11

    if precision == "30cm":
        return 14

    return 17


def _tile2lng(tile_x: int, zoom: int):
    """ Calculate a tile's longitude from it's x-axis and zoom level """

    return ((tile_x / 2**zoom) * 360.0) - 180.0


def _tile2lat(tile_y: int, zoom: int):
    """ Calculate a tile's latitude from it's y-axis and zoom level """

    n = np.pi - 2 * np.pi * tile_y / 2**zoom

    return (180.0 / np.pi) * np.arctan(0.5 * (np.exp(n) - np.exp(-n)))


def calculate_tile_area(tile: list):
    """ Calculate a tile's area.

    Args:
        tile (list): List of tiles.
    Returns:
        area (float) """

    EARTH_RADIUS = 6371.0088
    left = np.deg2rad(_tile2lng(tile[:, 0], tile[:, 2]))
    top = np.deg2rad(_tile2lat(tile[:, 1], tile[:, 2]))
    right = np.deg2rad(_tile2lng(tile[:, 0] + 1, tile[:, 2]))
    bottom = np.deg2rad(_tile2lat(tile[:, 1] + 1, tile[:, 2]))

    return (
        (np.pi / np.deg2rad(180))
        * EARTH_RADIUS**2
        * np.abs(np.sin(top) - np.sin(bottom))
        * np.abs(left - right)
    )


def calculate_tiles_area(features: list, precision: str):
    """ Calculate features area.

    Args:
        features (list): List of features
        precision (str): Precision selected, in meters.
    Returns:
        area (float) """

    zoom = _convert_precision_to_zoom(precision)
    tiles = burn(features, zoom)

    float_area = np.sum(calculate_tile_area(tiles))
    return int(round(float_area))
