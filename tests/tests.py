"""

Test suite for the package

"""

import json
import os
from dotenv import load_dotenv
import pytest
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
json.dump(basic_recipe, fp, indent = 2)
fp.close()

fp2 = open("./testFeature.json", "w", encoding="utf-8")
json.dump(test_feature, fp2, indent = 2)
fp2.close()

handler = MtsHandler()



def test_init():
    assert isinstance(handler, MtsHandler) is True

def test_list_sources():
    r = handler.list_sources()
    assert r.status_code == 200

def test_validate_source():
    assert handler.validate_source("./testFeature.json") == "✔ valid"

def test_list_tsets():
    r = handler.list_tsets()
    assert r.status_code == 200

def test_validate_source_id():
    assert handler.validate_source_id("test-test_1234") == "test-test_1234"

def test_upload_source():
    r = handler.upload_source("test-2", "./testFeature.json", replace=True)
    assert r.status_code == 200

def test_validate_recipe():
    r = handler.validate_recipe("./basicRecipe.json")
    assert r.json() == {'valid': True}

def test_get_source():
    r = handler.get_source("test-2")
    assert r.status_code == 200

class TestDeleteSource:
    def test_valid_operation(self):
        r = handler.delete_source("test-2")
        assert r.status_code == 204

    def test_mass_deletion_attempt(self):
        with pytest.raises(RestrictedError):
            handler.upload_source("test-2", "./testFeature.json", replace=True)
            handler.delete_source("test-2")

def test_estimate_area():
    estimate = handler.estimate_area("./testFeature.json", "10m")
    assert isinstance(estimate, str)

def test_list_activity():
    result = handler.list_activity()
    assert isinstance(result, object)

def test_create_ts():
    r = handler.create_ts("test-ts-2","Test-2", private = True)
    assert r.status_code == 200 or 204

def test_update_ts():
    r = handler.update_ts("test-ts-2", "Test-2-2")
    assert r.status_code == 204

def test_publish_ts():
    r = handler.publish_ts("test-ts-2")
    assert r.status_code == 200

def test_get_ts_status():
    msg = handler.get_ts_status("test-ts-2")
    assert msg["id"]

def test_get_tilejson():
    r = handler.get_tilejson("test-ts-2")
    assert r.status_code == 200

def test_list_ts_jobs():
    r = handler.list_ts_jobs("test-ts-2")
    assert r.status_code == 200


def test_get_ts_job():
    status = handler.get_ts_status("test-ts-2")
    print(status["latest_job"])
    r = handler.get_ts_job("test-ts-2", status["latest_job"])
    assert r.status_code == 200

def test_get_ts_recipe():
    r = handler.get_ts_recipe("test-ts-2")
    assert r.status_code == 200

def test_update_ts_recipe():
    r = handler.update_ts_recipe("test-ts-2", "./basicRecipe.json")
    assert r.status_code == 201 or 204

def test_delete_ts():
    r = handler.delete_ts("test-ts-2")
    assert r.status_code == 200 or 204
