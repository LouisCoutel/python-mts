""" Various utility functions """
import base64
import os
import re
import json
import time

from requests import Session
import geojson

import python_mts
from python_mts import errors

def load_feature(path: str):
    """ Load a geoJSON feature as a dict.

    Args:
        path (str): File path.
    Returns:
        Loaded feature (dict): A dict containing feature data. """

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

    return val


def _validate_token(username: str, token: str):
    """ Check if Mapbox token is valid
    Raises:
        errors.TilesetsError: Token doesn't contain payload
        errors.TilesetsError: Token username doesn't match provided username
        errors.TilesetsError: Token doesn't contain a username
    """

    # Not sure if I'll ever need this but let's keep it for now
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
    """ Check a file's timestamp. """

    if os.path.exists(f"{operation}.txt"):
        last_timestamp = os.path.getmtime(f"{operation}.txt")

        if last_timestamp >= time.time() - 20:
            raise errors.RestrictedError("deletion")


def validate_path(path):
    """ Validate file path. """

    if not os.path.exists(path):
        raise AssertionError('Input should be a valid path')

    return True


def get_session(application=__name__, version=python_mts.__version__):
    """ Create a session and set headers. """

    s = Session()
    s.headers.update({"user-agent": "{}/{}".format(application, version)})

    return s


def validate_tileset_id(tileset_id: str):
    """ Check if a tileset's id is valid according to Mapbox's specifications. """

    pattern = r"^[a-z0-9-_]{1,32}\.[a-z0-9-_]{1,32}$"

    if re.match(pattern, tileset_id, flags=re.IGNORECASE):
        return True

    raise errors.InvalidId(tileset_id)

def paths_to_features(iterable: list[str]):
    """ Open geojson features from files paths """

    features = []

    for path in iterable:
        with open(path, "w", encoding="utf-8") as file:
            features.append(geojson.load(file))

    return features


def validate_stream(features):
    """ Validate a stream of geoJSON features """

    for feature in features:
        validate_geojson(feature)

        yield feature


def validate_geojson(feature: dict):
    """ Validate a geoJSON file according to Mapbox's specifications """

    if not feature.is_valid:
        raise errors.InvalidGeoJSON(feature)


def reformat_geojson(file, paths: list[str]):
    """ Reformat geoJSON files to Mapbox specifications.

    Args:
        paths (list): List of paths to source files.
        no_validation (bool, optional): Skip validation.
            Defaults to False. """

    for path in paths:
        feature = load_feature(path)

        validate_geojson(feature)

        file.write(
            (json.dumps(feature, separators=(",", ":")) + "\n").encode("utf-8")
        )


def mk_status(res_data):
    """ Parses an API response to get a tileset's current status from its latest job.

    Args:
        res_data: Raw response data.
    Returns:
        status (dict): Tileset status info. """

    joblist = list(res_data)
    status = {
        "id": joblist[-1].get("tilesetId"),
        "lastest_job": joblist[-1].get("id"),
        "status": joblist[-1].get("stage"),
    }

    return status

def validate_source(paths):
    """ Check if a source is valid according to Mapbox's specification.

    Args:
        paths: Path or list of paths to source files
    Returns:
        True (bool): Source files are valid. """

    paths = enforce_islist(paths)

    for path in paths:
        validate_path(path)

        ft = load_feature(path)

        validate_geojson(ft)

    return True

class Singleton(type):
    """ Singleton meta-class to be paired with any base class """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(

        return cls._instances[cls]
