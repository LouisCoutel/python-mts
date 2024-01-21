import importlib
import logging
import os
import re
import time

import numpy as np

from jsonschema import validate, ValidationError
from requests import Session
from mts_handler import utils, errors
import mts_handler
import geojson
import json



def load_module(modulename):
    try:
        module = importlib.import_module(modulename)
    except ImportError:
        raise ValueError(
            f"Couldn't find {modulename}. Check installation steps in the readme for help: https://github.com/mapbox/tilesets-cli/blob/master/README.md"
        ) from None

    return module


def load_feature( path):
    utils.validate_path(path)
    abspath = os.path.abspath(path)
    with open(abspath) as file:
        return geojson.load(file)

def _get_token(token = None):
    token = (
        token
        or os.getenv("MAPBOX_ACCESS_TOKEN")
        or os.getenv("MapboxAccessToken")
    )

    if token is not None:
        return token

    logging.error(
        "No access token provided. Please set the MAPBOX_ACCESS_TOKEN environment variable or use the --token flag."
    )

def enforce_islist(input: str or list[str]):
    if type(input) == str:
        return [input]
    else:
        return input

def time_check(operation: str):
    if os.path.exists(f"{operation}.txt"):
        last_timestamp = os.path.getmtime(f"{operation}.txt")
        if last_timestamp >= time.time() - 20:
            raise errors.RestrictedError("deletion")

def validate_path(path):
    if not os.path.exists(path):
            raise AssertionError('Input should be a valid path')

def _get_session(application=mts_handler.__name__, version=mts_handler.__version__):
    s = Session()
    s.headers.update({"user-agent": "{}/{}".format(application, version)})
    return s


def validate_tileset_id(tileset_id: str):
    pattern = r"^[a-z0-9-_]{1,32}\.[a-z0-9-_]{1,32}$"

    return re.match(pattern, tileset_id, flags=re.IGNORECASE)


def geojson_validate(index, feature):
    geojsonFeature = geojson.loads(json.dumps(feature))
    if not geojsonFeature.is_valid:
        logging.error(
            f"Error in feature number {index}: " + "".join(geojsonFeature.errors())
        )

def paths_to_features(iterable: list[str]):
    features = []
    for path in iterable:
        file =  open(path)
        features.append(geojson.load(file))

    return features


def validate_stream(features):
    for index, feature in enumerate(features):
        validate_geojson(index, feature)
        yield feature


def validate_geojson(index, feature):
    schema = {
        "definitions": {},
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "http://example.com/root.json",
        "type": "object",
        "title": "GeoJSON Schema",
        "required": ["type", "geometry", "properties"],
        "properties": {
            "type": {
                "$id": "#/properties/type",
                "type": "string",
                "title": "The Type Schema",
                "default": "",
                "examples": ["Feature"],
                "pattern": "^(.*)$",
            },
            "geometry": {
                "$id": "#/properties/geometry",
                "type": "object",
                "title": "The Geometry Schema",
                "required": ["type", "coordinates"],
                "properties": {
                    "type": {
                        "$id": "#/properties/geometry/properties/type",
                        "type": "string",
                        "title": "The Type Schema",
                        "default": "",
                        "examples": ["Point"],
                        "pattern": "^(.*)$",
                    },
                    "coordinates": {
                        "$id": "#/properties/geometry/properties/coordinates",
                        "type": "array",
                        "title": "The Coordinates Schema",
                    },
                },
            },
            "properties": {
                "$id": "#/properties/properties",
                "type": "object",
                "title": "The Properties Schema",
            },
        },
    }
    try:
        validate(instance=feature, schema=schema)
    except ValidationError as e:
        logging.error(e)
    geojson_validate(index, feature)


def _convert_precision_to_zoom(precision: str):
    if precision == "10m":
        return 6
    elif precision == "1m":
        return 11
    elif precision == "30cm":
        return 14
    else:
        return 17


def _tile2lng(tile_x: int, zoom: int):
    return ((tile_x / 2**zoom) * 360.0) - 180.0


def _tile2lat(tile_y: int, zoom: int):
    n = np.pi - 2 * np.pi * tile_y / 2**zoom
    return (180.0 / np.pi) * np.arctan(0.5 * (np.exp(n) - np.exp(-n)))


def _calculate_tile_area(tile: list):
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
    burn = load_module("supermercado.burntiles").burn

    zoom = _convert_precision_to_zoom(precision)
    tiles = burn(features, zoom)
    return np.sum(_calculate_tile_area(tiles))

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]