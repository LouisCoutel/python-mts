"""

Test suite for the package

"""

import json
import os
from dotenv import load_dotenv
import pytest
from python_mts import utils
from python_mts.scripts.mts_handler import MtsHandler
from python_mts.errors import RestrictedError

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

fp = open("./basicRecipe.json", "w", encoding="utf-8")
json.dump(basic_recipe, fp, indent=2)
fp.close()

fp2 = open("./testFeature.json", "w", encoding="utf-8")
json.dump(test_feature, fp2, indent=2)
fp2.close()

handler = MtsHandler()
handler.set_default_recipe("./basicRecipe.json")


def test_token():
    """ Test if token is set """
    assert utils.get_token()


def test_init():
    """ Test if handler is instanciated """
    assert isinstance(handler, MtsHandler) is True


def test_list_sources():
    """ Test fetching list of sources"""
    r = handler.list_sources()
    assert r.status_code == 200


def test_validate_source():
    """ Test validating a source """
    assert handler.validate_source("./testFeature.json")


def test_list_tsets():
    """ Test fetching a list of tsets """
    r = handler.list_tsets()
    assert r.status_code == 200


def test_validate_source_id():
    """ Test validating a source ID """
    assert handler.validate_source_id("test-test_1234")

def test_upload_source():
    """ Test uploading a source """
    r = handler.upload_source("test-2", "./testFeature.json", replace=True)
    assert r.status_code == 200


def test_validate_recipe():
    """ Test validating a recipe """
    r = handler.validate_recipe("./basicRecipe.json")
    assert r.json() == {'valid': True}


def test_get_source():
    """ Test fetching a source """
    r = handler.get_source("test-2")
    assert r.status_code == 200


class TestDeleteSource:
    """ Test suite for source deletion """

    def test_valid_operation(self):
        """ Test if going through when enough time has passed """
        r = handler.delete_source("test-2")
        assert r.status_code == 204

    def test_mass_deletion_attempt(self):
        """ Test if not enough time has passed and deletion is forbidden """
        with pytest.raises(RestrictedError):
            handler.upload_source("test-2", "./testFeature.json", replace=True)
            handler.delete_source("test-2")


def test_estimate_area():
    """ Test estimating area """
    estimate = handler.estimate_area("./testFeature.json", "10m")
    assert isinstance(estimate, str)


def test_list_activity():
    """ Test getting an activity report """
    result = handler.list_activity()
    assert isinstance(result, object)


def test_create_ts():
    """ Test creating a tileset """
    r = handler.create_ts("test-ts-2", "Test-2", private=True)
    assert r.status_code == 200


def test_update_ts():
    """ Test updating a tileset's infos """
    r = handler.update_ts("test-ts-2", "Test-2-2")
    assert r.status_code == 204


def test_publish_ts():
    """ Test publishing a tileset """
    r = handler.publish_ts("test-ts-2")
    assert r.status_code == 200


def test_get_ts_status():
    """ Test getting a status report for a tileset """
    assert handler.get_ts_status("test-ts-2").get("id")

def test_get_tilejson():
    """ Test getting a tileset's tilejson """
    r = handler.get_tilejson("test-ts-2")
    assert r.status_code == 200


def test_get_ts_jobs():
    """ Test listing a tileset's jobs """
    r = handler.get_ts_jobs("test-ts-2")
    assert r.status_code == 200


def test_get_ts_job():
    """ Test getting a specific job """
    status = handler.get_ts_status("test-ts-2")
    r = handler.get_ts_job("test-ts-2", status["latest_job"])
    assert r.status_code == 200


def test_get_ts_recipe():
    """ Test getting a recipe """
    r = handler.get_ts_recipe("test-ts-2")
    assert r.status_code == 200


def test_update_ts_recipe():
    """ Test updating a recipe """
    r = handler.update_ts_recipe("test-ts-2", "./basicRecipe.json")
    assert r.status_code == 201 or 204


def test_delete_ts():
    """ Test deleting a tileset """
    r = handler.delete_ts("test-ts-2")
    assert r.status_code == 200 or 204
