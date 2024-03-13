""" Utility class for generating request URLs """
import os
from urllib.parse import urlencode
from python_mts import utils, errors


class Urls:
    """ Create requests URLs to be used by the client """

    def __init__(self):
        self._username: str = os.getenv("MAPBOX_USER_NAME")
        self._token: str = os.getenv("MAPBOX_ACCESS_TOKEN")
        self.main_api = "https://api.mapbox.com"
        self.ts_api = f"{self.main_api}/tilesets/v1"
        self.styles_api = f"{self.main_api}/styles/v1"

    def mkurl_ts(self, ts_id: str, publish: bool = False):
        """ Generate the URL for most tileset operations.

        Args:
            ts_id (str): Tileset ID (username.handle).
            publish (bool, optional): Option to get publish URL. Disabled by default. 
        Returns:
            Get tileset URL (str): https://api.mapbox.com/tilesets/v1/{ts_id}?access_token={token}.
            Publish tileset URL (str): https://api.mapbox.com/tilesets/v1/{ts_id}/publish?access_token={token}. """

        if publish:
            return f"{self.ts_api}/{ts_id}/publish?access_token={self._token}"

        return f"{self.ts_api}/{ts_id}?access_token={self._token}"

    def mkurl_ts_jobs(self, ts_id: str, stage: str = None, limit: int = 100):
        """ Generate the URL for accessing a tileset's jobs.

        Args:
            ts_id (str): Tileset ID (username.handle).
            stage (str, optional): Job-stage filter. Defaults to None.
            limit (int, optional): Max number of jobs listed. Defaults to 100.
        Returns: 
            Tileset jobs URL (str): https://api.mapbox.com/tilesets/v1/{ts_id}/jobs?&{query_str}. """

        params = utils.filter_missing_params(
            access_token=self._token, ts_id=ts_id, stage=stage, limit=limit)

        query_str = urlencode(params)

        return f"{self.ts_api}/{ts_id}/jobs?&{query_str}"

    def mkurl_tjson(self, handles: list[str], secure: bool):
        """ Generate the URL for accessing a tileset's tileJSON.

        Args:
            handles: Handles (identifiers) of tilesets. 
                Combined with the username they form a tileset's id (username.handle).
            secure (bool): Force HTTPS. 
        Returns: 
            Tileset tileJSON data URL (str): https://api.mapbox.com/v4/{ts_ids}.json?access_token={token}. """

        ids = []
        for t in handles:
            ts_id = self._username + "." + t
            ids.append(ts_id)
            if not utils.validate_tileset_id(ts_id):
                raise errors.InvalidId(ts_id)

        url = f"https://api.mapbox.com/v4/{','.join(ids)}.json?access_token={self._token}"

        if secure:
            url = url + "&secure"

        return url

    def mkurl_ts_job(self, ts_id: str, job_id: str):
        """ Generate the URL to access a specific tileset job.

        Args:
            ts_id (string): Tileset ID.
            job_id (string): Tileset job ID. 
        Returns: 
            Specific tileset job URL (str): https://api.mapbox.com/tilesets/v1/{ts_id}/jobs/{job_id}?&access_token={token}. """

        return f"{self.ts_api}/{ts_id}/jobs/{job_id}?access_token={self._token}"

    def mkurl_tslist(self,
                     ts_type: str = None,
                     limit: int = 100,
                     visibility: str = None,
                     sortby=None):
        """ Generate the URL to list tilesets.

        Args:
            ts_type (str, optional): Type of tilesets to list. Defaults to None.
            limit (int): Max number of tilesets listed.
                Max 500.
                Defaults to None.
            visibility (str, optional): Filter by visibility.
                Accepts "public" or "private".
                Defaults to None.
            sortby (str, optional): Sorting preference.
                Accepts "created" or "modified".
                Defaults to None.
        Returns: 
            Tilesets list URL (str): https://api.mapbox.com/tilesets/v1/{username}?&{query_str}. """

        params = utils.filter_missing_params(access_token=self._token,
                                             ts_type=ts_type,
                                             limit=limit,
                                             visibility=visibility,
                                             sortby=sortby)
        query_str = urlencode(params)

        return f"{self.ts_api}/{self._username}?{query_str}"

    def mkurl_ts_rcp(self, ts_id: str):
        """ Generate the URL to access a tileset's recipe.

        Args:
            ts_id (str): Tileset ID.
        Returns: 
            Tilesets recipe URL (str): https://api.mapbox.com/tilesets/v1/{ts_id}/recipe?access_token={token}. """

        return f"{self.ts_api}/{ts_id}/recipe?access_token={self._token}"

    def mkurl_val_rcp(self):
        """ Generate the URL for validating a tileset recipe. 

        Returns: 
            Validate recipe URL (str): https://api.mapbox.com/tilesets/v1/validateRecipe?access_token={token}. """

        return f"{self.ts_api}/validateRecipe?access_token={self._token}"

    def mkurl_src(self, src_id: str):
        """ Generate the URL to access a specific source

        Args:
            src_id (str): Source ID.
        Returns: 
            Generic source URL (str): https://api.mapbox.com/tilesets/v1/sources/{username}/{src_id}?access_token={token}. """

        return f"{self.ts_api}/sources/{self._username}/{src_id}?access_token={self._token}"

    def mkurl_srclist(self):
        """ Generate the URL to list sources. 

        Returns:
            List sources URL (str): https://api.mapbox.com/tilesets/v1/sources/{username}?access_token={token}. """

        return f"{self.ts_api}/sources/{self._username}?access_token={self._token}"

    def mkurl_activity(self,
                       sortby: str = "requests",
                       orderby: str = "desc",
                       limit: int = 100,
                       start: str = None):
        """ Generate the URL to get an activity report.

        Args:
            sortby (str, optional): Sort by requests or last modified. 
                Defaults to "requests". 
                Accepts "modified".
            orderby (str, optional): Descending or ascending order.
                Defaults to "desc".
            limit (int, optional): Max number of listed activities.
                Defaults to 100.
            start (str, optional): Pagination key.
                Defaults to None. 
        Returns:
            Activity report URL (str): https://api.mapbox.com/activity/v1/{username}/tilesets?{query_str} """

        params = utils.filter_missing_params(
            access_token=self._token,
            sortby=sortby,
            orderby=orderby,
            limit=limit,
            start=start)

        query_str = urlencode(params)

        return f"https://api.mapbox.com/activity/v1/{self._username}/tilesets?{query_str}"

    def mkurl_liststyles(self, draft: bool = False, limit: int = None, start_id: str = None):
        """ Generate the URL to list styles. 

        Returns:
            Published styles list URL (str): https://api.mapbox.com/styles/v1/{username}?{query_str}. 
            Draft styles list URL (str): https://api.mapbox.com/styles/v1/{username}/draft?{query_str}. """

        params = utils.filter_missing_params(
            access_token=self._token, limit=limit, start_id=start_id)

        query_str = urlencode(params)

        url = f"{self.styles_api}/{self._username}"
        url = url + "/draft" if draft else url

        return url + f"?{query_str}"
