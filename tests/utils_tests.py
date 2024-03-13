""" Test utilities. """

import pytest
from python_mts import utils


feature_dict = {
    "type": "Feature",
    "geometry": {
        "type": "LineString",
        "coordinates": [[45.6, 42.53], [49.758, 48]]},
    "properties": {"id": 2}
}


class TestValidatePath:
    """ Test validating a file's path. """

    def test_valid(self):
        """ Test with valid path. """

        assert utils.validate_path("./testFeature.json")

    def test_invalid(self):
        """ Test with invalid path. """

        with pytest.raises(AssertionError):
            utils.validate_path("./invalid.json")


def test_load_valid():
    """ Test loading a geoJSON feature from valid file path. """

    feature = utils.load_feature("./testFeature.json")
    assert feature == feature_dict


def test_calc_area():
    """ Test calculating area. """

    features = [utils.load_feature("./testFeature.json"),
                utils.load_feature("./testFeature.json")]

    assert isinstance(utils.calculate_tiles_area(features, "10m"), float)
