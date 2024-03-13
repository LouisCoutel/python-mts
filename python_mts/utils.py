""" Various utility functions """
import base64
import importlib
import logging
import os
import re
import json
import time

import numpy as np

from jsonschema import validate, ValidationError
from requests import Session
import geojson

import python_mts
from python_mts import errors


def load_module(modulename):
    """ Load a python module """
    try:
        module = importlib.import_module(modulename)
    except ImportError:
        raise ValueError(
            f"Couldn't find {modulename}."
            "Check installation steps in the readme for help:"
            "https://github.com/mapbox/tilesets-cli/blob/master/README.md"
        ) from None

    return module


def load_feature(path):
    """ Load a geoJSON feature as a dict """
    validate_path(path)
    abspath = os.path.abspath(path)
    with open(abspath, "r", encoding="utf-8") as file:
        return geojson.load(file)


def filter_missing_params(**params):
    """ Turn params into a dict and remove none values"""
    return {k: v for k, v in params.items() if v}


def validate_source_id(src_id: str):
    """ Check if a source ID is valid according to Mapbox's specifications

    Args:
        src_id (string): String ID to validate.

    Raises:
        AssertionError: ID is not valid.

    Returns:
        True (bool): Source ID is valid. """

    if re.match("^[a-zA-Z0-9-_]{1,32}$", src_id):
        return True
    raise AssertionError(
        'Invalid TS ID. Max-length: 32 chars and only include "-", "_", and alphanumeric chars.'
    )


def get_token():
    """ Get access token from .env. """

    token = os.getenv("MAPBOX_ACCESS_TOKEN")

    if token:
        return token

    raise errors.TilesetsError(
        "No access token provided. Please set the MAPBOX_ACCESS_TOKEN env var")


def enforce_islist(val):
    """ Wraps a string in a list or do nothing if it is already a list. """

    if isinstance(val, str):
        return [val]

    return input


def _validate_token(username: str, token: str):
    """ Check if Mapbox token is valid

    Raises:
        errors.TilesetsError: Token doesn't contain payload
        errors.TilesetsError: Token username doesn't match provided username
        errors.TilesetsError: Token doesn't contain a username
    """
    # This does the decoding by hand instead of using pyjwt because
    # pyjwt rejects tokens that don't pad the base64 with = signs.
    token_parts = token.split(".")
    if len(token_parts) < 2:
        raise errors.TilesetsError(
            f"Token {token} does not contain a payload component")

    while len(token_parts[1]) % 4 != 0:
        token_parts[1] = token_parts[1] + "="
    body = json.loads(base64.b64decode(token_parts[1]))

    if "u" in body:
        if username != body["u"]:
            raise errors.TilesetsError(
                f"Token username {body['u']} does not match username {username}"
            )
    else:
        raise errors.TilesetsError(
            f"Token {token} does not contain a username"
        )


def time_check(operation: str):
    """ Check a file's timestamp """
    if os.path.exists(f"{operation}.txt"):
        last_timestamp = os.path.getmtime(f"{operation}.txt")
        if last_timestamp >= time.time() - 20:
            raise errors.RestrictedError("deletion")


def validate_path(path):
    """ Validate file path """
    if not os.path.exists(path):
        raise AssertionError('Input should be a valid path')


def _get_session(application=__name__, version=python_mts.__version__):
    """ Create a session and set headers """
    s = Session()
    s.headers.update({"user-agent": "{}/{}".format(application, version)})
    return s


def validate_tileset_id(tileset_id: str):
    """ Check if a tileset's id is valid according to Mapbox's specifications """
    pattern = r"^[a-z0-9-_]{1,32}\.[a-z0-9-_]{1,32}$"

    return re.match(pattern, tileset_id, flags=re.IGNORECASE)


def geojson_validate(index, feature):
    """ Check if a feature is valid geojson """
    feature_dict = geojson.loads(json.dumps(feature))
    if not feature_dict.is_valid:
        message = f"Error in feature number {index}: {feature_dict.errors()}"

        logging.error(
            message
        )


def paths_to_features(iterable: list[str]):
    """ Open geojson features from files paths """
    features = []
    for path in iterable:
        with open(path, "w", encoding="utf-8") as file:
            features.append(geojson.load(file))

    return features


def validate_stream(features):
    """ Validate a stream of geoJSON features """
    for index, feature in enumerate(features):
        validate_geojson(index, feature)
        yield feature


def validate_geojson(index, feature):
    """ Validate a geoJSON file according to Mapbox's specifications """
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


def _calculate_tile_area(tile: list):
    """ Calculate a tile's area """
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


def reformat_geojson(file, paths: list[str]):
    """ Reformat geoJSON files to Mapbox specifications.

    Args:
        paths (list): List of paths to source files.
        no_validation (bool, optional): Skip validation.
            Defaults to False. """

    for index, path in enumerate(paths):
        feature = load_feature(path)
        validate_geojson(index, feature)
        file.write(
            (json.dumps(feature, separators=(",", ":")) + "\n").encode("utf-8")
        )


def mk_status(response):
    """ Parses an API response to get a tileset's current status from its latest job.

    Args:
        response (API Response): Response to parse

    Returns:
        status (dict): Tileset status info. """

    joblist = list(response.json())

    status = {
        "id": joblist[-1].get("tilesetId"),
        "lastest_job": joblist[-1].get("id"),
        "status": joblist[-1].get("stage"),
    }

    return status


def validate_source(paths):
    """ Check if a source is valid according to Mapbox's specification
    Args:
        paths (str or list[str]): Path or list of paths to source files
    Returns:
        True (bool): Source files are valid
    """

    paths = enforce_islist(paths)
    for index, path in enumerate(paths):
        validate_path(path)
        ft = load_feature(path)
        validate_geojson(index, ft)
    return True


def calculate_tiles_area(features: list, precision: str):
    """ Calculate features area. """

    burn = load_module("supermercado.burntiles").burn

    zoom = _convert_precision_to_zoom(precision)
    tiles = burn(features, zoom)
    return np.sum(_calculate_tile_area(tiles))


class Singleton(type):
    """ Singleton meta-class to be paired with any base class """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
