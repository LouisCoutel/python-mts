""" Test URL generator. """
import os
from dotenv import load_dotenv
from python_mts.urls import Urls

load_dotenv()


urls = Urls()
token = os.getenv("MAPBOX_ACCESS_TOKEN")
username = os.getenv("MAPBOX_USER_NAME")


def test_init():
    """ Test instanciation """
    assert urls


def test_mkurl_ts():
    """ Test getting generic TS request URL """
    expected = f"https://api.mapbox.com/tilesets/v1/test?access_token={token}"
    assert urls.mkurl_ts("test") == expected


def test_mkurl_activity():
    """ Test getting activity report URL """
    expected = f"https://api.mapbox.com/activity/v1/{username}/tilesets?access_token={token}&sortby=requests&orderby=desc&limit=100"
    assert urls.mkurl_activity() == expected


def test_mkurl_liststyles():
    """ Test getting styles list URL """
    expected = f"https://api.mapbox.com/styles/v1/{username}?access_token={token}"
    assert urls.mkurl_liststyles() == expected


def test_mkurl_src():
    """ Test getting generic source request URL """
    assert urls.mkurl_src(
        "test") == f"https://api.mapbox.com/tilesets/v1/sources/{username}/test?access_token={token}"


def test_mkurl_srclist():
    """ Test getting sources list URL """
    assert urls.mkurl_srclist(
    ) == f"https://api.mapbox.com/tilesets/v1/sources/{username}?access_token={token}"


def test_mkurl_ts_job():
    """ Test getting specific job request URL """
    assert urls.mkurl_ts_job(
        "test", "test") == f"https://api.mapbox.com/tilesets/v1/test/jobs/test?access_token={token}"
