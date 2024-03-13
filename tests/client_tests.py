""" Test client and requests. """

from python_mts.client import Client

client = Client()


def test_init():
    """ Test client instanciation. """
    assert client


def test_get():
    """ Test get request. """
    r = client.do_get("https://api.mapbox.com")
    assert r.status_code == 200


def test_post():
    """ Test post request. """
    r = client.do_post("https://api.mapbox.com")
    assert r.status_code == 403


def test_del():
    """ Test del request. """
    r = client.do_del("https://api.mapbox.com")
    assert r.status_code == 403


def test_put():
    """ Test put request. """
    r = client.do_put("https://api.mapbox.com", {"test": "test"})
    assert r.status_code == 403


def test_patch():
    """ Test patch request. """
    r = client.do_patch("https://api.mapbox.com")
    assert r.status_code == 403
