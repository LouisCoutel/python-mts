""" Test tileset operations """

import json
import os
from dotenv import load_dotenv
from python_mts import utils
from python_mts.scripts.mts_handler import MtsHandler

load_dotenv()

basic_recipe = {
    "version": 1,
    "layers": {
        "test": {
            "source": f"mapbox://tileset-source/{os.getenv('MAPBOX_USER_NAME')}/test-2",
            "minzoom": 0,
            "maxzoom": 5
        }
    }
}

test_feature = {
    "type": "Feature",
    "geometry": {
        "type": "LineString",
        "coordinates": [[45.6, 42.53], [49.758, 48]]
    },
    "properties": {
        "id": 2,
    }
}

with open("./basicRecipe.json", "w", encoding="utf-8") as f:
    json.dump(basic_recipe, f, indent=2)
    f.close()

with open("./testFeature.json", "w", encoding="utf-8") as f2:
    json.dump(test_feature, f2, indent=2)
    f2.close()

handler = MtsHandler()


def test_token():
    """ Test if token is set """
    assert utils.get_token()


def test_init():
    """ Test if handler is instanciated """
    assert isinstance(handler, MtsHandler) is True


def test_list_sources():
    """ Test fetching list of sources"""
    r = handler.list_sources()
    assert isinstance(r, list)


def test_list_tsets():
    """ Test fetching a list of tsets """
    r = handler.list_tsets()
    assert isinstance(r, list)


def test_upload_source():
    """ Test uploading a source """
    r = handler.upload_source("test-2", "./testFeature.json", replace=True)
    assert isinstance(r, dict)


def test_validate_recipe():
    """ Test validating a recipe """
    r = handler.validate_recipe("./basicRecipe.json")
    assert r == {'valid': True}


def test_get_source():
    """ Test fetching a source """
    r = handler.get_source("test-2")
    assert isinstance(r, dict)


def test_estimate_area():
    """ Test estimating area """
    estimate = handler.estimate_area("./testFeature.json", "10m")
    assert isinstance(estimate, str)


def test_list_activity():
    """ Test getting an activity report """
    r = handler.list_activity()
    assert isinstance(r, dict)


def test_create_ts():
    """ Test creating a tileset """
    r = handler.create_ts("test-ts-2", "Test-2",
                          "./basicRecipe.json", private=True)
    assert isinstance(r, dict)


def test_update_ts():
    """ Test updating a tileset's infos """
    r = handler.update_ts("test-ts-2", "Test-2-2")
    assert r == "Tileset test-ts-2 successfully updated."


def test_publish_ts():
    """ Test publishing a tileset """
    r = handler.publish_ts("test-ts-2")
    assert isinstance(r, dict)


def test_get_ts_status():
    """ Test getting a status report for a tileset """
    assert handler.get_ts_status("test-ts-2").get("id")


def test_get_tilejson():
    """ Test getting a tileset's tilejson """
    r = handler.get_tilejson("test-ts-2")
    assert isinstance(r, dict)


def test_get_ts_jobs():
    """ Test listing a tileset's jobs """
    r = handler.get_ts_jobs("test-ts-2")
    assert isinstance(r, list)


def test_get_ts_recipe():
    """ Test getting a recipe """
    r = handler.get_ts_recipe("test-ts-2")
    assert isinstance(r, dict)


def test_update_ts_recipe():
    """ Test updating a recipe """
    r = handler.update_ts_recipe("test-ts-2", "./basicRecipe.json")
    assert r == "Tileset test-ts-2's recipe successfully updated."


def test_delete_ts():
    """ Test deleting a tileset """
    r = handler.delete_ts("test-ts-2")
    assert isinstance(r, dict)


def test_delete_source():
    """ Test if going through when enough time has passed """
    r = handler.delete_source("test-2")
    assert r == "Source test-2 successfully deleted."
