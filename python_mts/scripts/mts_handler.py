""" This module exposes a handler class for Mapbox Tiling Service and Mapbox's API operations. """
import json
import logging
import os
import tempfile
from urllib.parse import urlencode, urlparse, parse_qs
import re
from dotenv import load_dotenv
from requests_toolbelt import MultipartEncoder

from python_mts import utils, errors

load_dotenv()


class MtsHandlerBase:
    """ Exposes methods for interacting with the Mapbox Tiling Service.
    Base class to be paired with a Singleton meta-class """

    def __init__(self):
        self._username: str = os.getenv("MAPBOX_USER_NAME")
        self._token: str = os.getenv("MAPBOX_ACCESS_TOKEN")
        self._api = "https://api.mapbox.com"
        self._default_recipe: str
        self._json_indent: int = 4
        self._attribution: json = None
        self._session = utils._get_session()

    # REQUEST WRAPPERS
    def _do_post(self, url: str, body=None):
        s = self._session
        if body:
            r = s.post(url, json=body)
        else:
            r = s.post(url)
        return r

    def _do_patch(self, url: str, body=None):
        s = self._session
        if body:
            r = s.patch(url, json=body)
        else:
            r = s.patch(url)
        return r

    def _do_put(self, url: str, body):
        s = self._session
        print(json)
        return s.put(url, json=body)

    def _do_get(self, url: str):
        s = self._session
        return s.get(url)

    def _do_del(self, url: str):
        s = self._session
        return s.delete(url)

    # GETTERS
    def get_default_recipe(self):
        """ Getter """
        return self._default_recipe

    def get_json_indent(self):
        """ Getter """
        return self._json_indent

    def get_session(self):
        """ Getter """
        return self._session

    # SETTERS
    def set_default_recipe(self, path: str):
        """ Select a file to be used as default recipe

        Args:
            path (str): File path
        """

        utils.validate_path(path)
        self._default_recipe = os.path.abspath(path)

    def set_indent(self, indent: int):
        """ Set indentation preference for JSON data """

        self._json_indent = indent

    # URL BUILDERS
    def _mkurl_ts(self, ts_id: str, publish: bool = None):
        """ Generate the URL needed for most tileset operations.

        Args:
            ts_id (string): Tileset ID (username.handle)
            publish (bool, optional): Option to get publish URL. Disabled by default.

        Returns:
            URL (string): URL for tileset operations
        """

        if publish:
            return f"{self._api}/tilesets/v1/{ts_id}/publish?access_token={self._token}"

        return f"{self._api}/tilesets/v1/{ts_id}?access_token={self._token}"

    def _mkurl_ts_jobs(self, ts_id: str, stage: str = None, limit: int = 100):
        """ Generate the URL needed for accessing a tileset's jobs

        Args:
            ts_id (str): Tileset ID (username.handle)
            stage (str, optional): Job-stage filter. Defaults to None.
            limit (int, optional): Max number of jobs listed. Defaults to 100.

        Returns:
            URL (string): URL for accessing a tileset's jobs
        """

        url = f"{self._api}/tilesets/v1/{ts_id}/jobs?access_token={self._token}"
        url = url + f"{self._api}&stage={stage}" if stage else url
        url = url + f"{self._api}&limit={limit}" if limit else url

        print(url)
        return url

    def _mkurl_tjson(self, handles: list[str], secure: bool):
        """ Generate the URL needed for accessing a tileset's tileJSON.

        Args:
            handles (list of strings): Handles (name) of tilesets. 
            Combined with the username they form a tileset's id (username.handle).
            secure (boolean): Optional parameter that instructs Mapbox API to respond through HTTPS.

        Raises:
            errors.TilesetNameError: Custom Mapbox Exception

        Returns:
            URL (string): URL for accessing a tileset's tileJson
        """

        ids = []
        for t in handles:
            ts_id = self._username + "." + t
            ids.append(ts_id)
            if not utils.validate_tileset_id(ts_id):
                raise errors.TilesetNameError(ts_id)

        url = f"{self._api}/v4/{','.join(ids)}.json?access_token={self._token}"

        if secure:
            url = url + "&secure"

        return url

    def _mkurl_ts_job(self, ts_id: str, job_id: str):
        """ Generate the URL needed to access a specific tileset job

        Args:
            ts_id (string): Tileset ID
            job_id (string): Tileset job ID

        Returns:
            URL (string): URL for accessing a tileset job
        """

        return f"{self._api}/tilesets/v1/{ts_id}/jobs/{job_id}?access_token={self._token}"

    def _mkurl_tslist(self,
                      ts_type: str = None,
                      limit: int = 100,
                      visibility: str = None,
                      sortby=None):
        """ Generate the URL needed to list tilesets

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
            URL (string): URL for tileset list
        """

        url = f"{self._api}/tilesets/v1/{self._username}?access_token={self._token}"
        url = f"{url}&limit={limit}" if limit else url
        url = f"{url}&type={ts_type}" if ts_type else url
        url = f"{url}&visibility={visibility}" if visibility else url
        url = f"{url}&sortby={sortby}" if sortby else url

        return url

    def _mkurl_ts_rcp(self, ts_id: str):
        """ Generate the URL needed to access a tileset's recipe

        Args:
            ts_id (str): Tileset ID

        Returns:
            URL (string): URL for tileset recipe
        """

        return f"{self._api}/tilesets/v1/{ts_id}/recipe?access_token={self._token}"

    def _mkurl_val_rcp(self):
        """ Generate the URL needed for validating a tileset recipe

        Returns:
            URL (string): URL for recipe validation
        """
        return f"{self._api}/tilesets/v1/validateRecipe?access_token={self._token}"

    def _mkurl_src(self, src_id: str):
        """ Generate the URL needed to access a specific source

        Args:
            src_id (str): Source ID

        Returns:
            URL (string): URL for source

        """
        return f"{self._api}/tilesets/v1/sources/{self._username}"\
            f"/{src_id}?access_token={self._token}"

    def _mkurl_srclist(self):
        """ Generate the URL needed to list sources

        Returns:
            URL (string): URL for source list
        """

        return f"{self._api}/tilesets/v1/sources/{self._username}?access_token={self._token}"

    def _mkurl_activity(self,
                        sortby: str = "requests",
                        orderby: str = "desc",
                        limit: int = 100,
                        start: str = None):
        """ Generate the URL needed to get an activity report

        Args:
            sortby (str, optional): Sort by requests or last modified. 
                Defaults to "requests". 
                Accepts "modified".
            orderby (str, optional): Descending or ascending order. Defaults to "desc".
            limit (int, optional): Max number of listed activities. Defaults to 100.
            start (str, optional): Pagination key. Defaults to None.

        Returns:
            URL (string): URL for activity report
        """
        params = {
            "access_token": self._token,
            "sortby": sortby,
            "orderby": orderby,
            "limit": limit,
            "start": start,
        }
        params = {k: v for k, v in params.items() if v}
        query_string = urlencode(params)
        return f"{self._api}/activity/v1/{self._username}/tilesets?{query_string}"

    # REQUESTS UTILS
    def reformat_geojson(self, file, paths: list[str]):
        """ Reformat geoJSON files to Mapbox specifications

        Args:
            paths (list): List of paths to source files.
            no_validation (bool, optional): Skip validation.
                Defaults to False.

        """
        for index, path in enumerate(paths):
            feature = utils.load_feature(path)
            utils.validate_geojson(index, feature)

            file.write(
                (json.dumps(feature, separators=(",", ":")) + "\n").encode("utf-8")
            )

    def _mkbody_tileset(
            self,
            name: str,
            private: bool = True,
            desc: str = None,
            recipe_path: str = None,
            update: bool = False
    ):
        """ Generate the request body for various tileset operations

        Args:
            name (str): Tileset name
            private (bool): Set tileset visibility to private.
                Defaults to True.
            desc (str, optional): Tileset description.
                Defaults to None.
            recipe_path (str, optional): Path pointing to recipe file.
                Defaults to None.
            update (bool, optional): Specify if the request body to be generated is for an update.
                Defaults to False.

        Raises:
            errors.TilesetsError: Custom Mapbox Exception

        Returns:
            body (dict): Request body
        """

        body = {}
        body["name"] = name
        body["description"] = desc if desc else ""
        body["private"] = private

        if not update:
            recipe = recipe_path if recipe_path else self._default_recipe
            with open(recipe, encoding="utf-8") as json_recipe:
                body["recipe"] = json.load(json_recipe)

        if self._attribution:
            try:
                body["attribution"] = json.loads(self._attribution)
            except Exception as exc:
                raise errors.TilesetsError(
                    "Unable to parse attribution JSON") from exc

        return body

    # RESPONSES UTILS
    def _mkstatus(self, response):
        """ Parses an API response to get a tileset's current status from its latest job


        Args:
            response (API Response): Response to parse

        Returns:
            status (dict): Tileset status info
        """

        joblist = list(response.json())

        status = {
            "id": joblist[-1].get("tilesetId"),
            "lastest_job": joblist[-1].get("id"),
            "status": joblist[-1].get("stage"),
        }

        return status

    # TILESETS OPERATIONS
    def create_ts(
            self,
            handle: str,
            name: str = None,
            recipe_path: str = None,
            desc: str = None,
            private: bool = False
    ):
        """ Create a new tileset with a recipe. 

        <tileset_id> is in the form of username.handle - for example "mapbox.neat-tileset".
        The handle may only include "-" or "_" special characters
        and must be 32 characters or fewer.

        Args:
            handle (str): Tileset handle
            name (str): Tileset name.
                Defaults to None.
            recipe_path (str, optional): Path to the recipe file.
                Defaults to None.
            desc (str, optional): Tileset description.
                Defaults to None.
            private (bool, optional): Set visibility to private.
                Defaults to False.

        Returns:
            r: API response
        """
        ts_id = self._username + "." + handle
        if not utils.validate_tileset_id(ts_id):
            logging.error(ts_id)

        url = self._mkurl_ts(ts_id)
        body = self._mkbody_tileset(name, private, desc, recipe_path)

        r = self._do_post(url, body=body)

        return r

    # Publish a specific tileset

    def publish_ts(self, handle: str):
        """_summary_

        Args:
            handle (str): Tileset handle.

        Returns:
            r: API response
        """
        ts_id = self._username + "." + handle
        url = self._mkurl_ts(ts_id, publish=True)
        r = self._do_post(url)
        if r.status_code == 200:
            response_msg = r.json()
            print(json.dumps(response_msg, indent=self._json_indent))
            studio_url = f"https://studio.mapbox.com/tilesets/{ts_id}"
            msg = f"Tileset job received. Visit {studio_url} to view the status of your tileset."
            print(msg)

        else:
            logging.error(r.text)

        return r

    def update_ts(self, handle: str, name: str = None, desc: str = None, private: bool = False):
        """ Update a tileset's informations

        Args:
            handle (str): Tileset handle
            name (str, optional): Tileset name. Defaults to None.
            desc (str, optional): Tileset description. Defaults to None.
            private (bool, optional): Set visibility to private.
                Defaults to False.

        Raises:
            errors.TilesetsError: Custom Mapbox Exception

        Returns:
            r: API response
        """
        ts_id = self._username + "." + handle
        url = self._mkurl_ts(ts_id)
        body = self._mkbody_tileset(name, private, desc, update=True)
        r = self._do_patch(url, body=body)

        if r.status_code != 204:
            raise errors.TilesetsError(r.text)

        return r

    def delete_ts(self, handle: str):
        """ Delete a specific tileset

        Args:
            handle (str): Tileset handle

        Raises:
            errors.TilesetsError: Custom Mapbox Exception
            e: Re-raised Custom Mapbox Exception

        Returns:
            r: API response
        """
        ts_id = self._username + "." + handle
        url = self._mkurl_ts(ts_id)

        try:
            utils.time_check("deletion-ts")
            r = self._do_del(url)
            with open("deletion-ts.txt", "w", encoding="utf-8") as f:
                f.close()

            if r.status_code in (200, 204):
                return r

            raise errors.TilesetsError(r.text)

        except errors.TilesetsError as e:
            raise e

    def get_ts_status(self, handle: str):
        """ Get a tileset's current status

        Args:
            handle (str): Tileset handle

        Raises:
            errors.TilesetsError: Custom Mapbox Exception

        Returns:
            status (dict): Tileset status information based on last job executed.
        """

        ts_id = self._username + "." + handle
        url = self._mkurl_ts_jobs(ts_id)
        r = self._do_get(url)

        if r.status_code != 200:
            raise errors.TilesetsError(r.text)

        status = self._mkstatus(r)

        return status

    def get_tilejson(self, handles: str or list[str], secure: bool = True):
        """ Get a tileset's corresponding tileJson data

        Args:
            handles (str or list[str]): A single tileset handle or a list of handles.
            secure (bool, optional): Force request to use HTTPS. Defaults to True.

        Raises:
            errors.TilesetsError: Custom Mapbox Exception

        Returns:
            r: API response
        """

        handles = utils.enforce_islist(handles)

        url = self._mkurl_tjson(handles, secure)
        print(url)
        r = self._do_get(url)

        if r.status_code == 200:
            return r

        raise errors.TilesetsError(r.text)

    def get_ts_jobs(self, handle: str, stage: str = None, limit: int = 100, job_id: str = None):
        """ Gets either a list of jobs or a single specific job corresponding to a tileset

        Args:
            handle (str): Tileset handle
            stage (str, optional): Filter jobs by stage. Defaults to None.
            limit (int, optional): Max number of jobs listed. Defaults to 100.
            job_id (str, optional): Get only a specific job. Defaults to None.

        Returns:
            r: API response
        """

        ts_id = self._username + "." + handle

        url = self._mkurl_ts_job(ts_id, job_id) if job_id else self._mkurl_ts_jobs(
            ts_id, stage=stage, limit=limit)

        r = self._do_get(url)

        return r

    def list_tsets(
            self,
            ts_type: str = None,
            visibility: str = None,
            sortby: str = None,
            limit: int = 100
    ):
        """ Get a list of uploaded tileset

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

        Raises:
            errors.TilesetsError: _description_

        Returns:
            _type_: _description_
        """
        url = self._mkurl_tslist(ts_type, limit, visibility, sortby)
        r = self._do_get(url)

        if r.status_code == 200:
            return r

        raise errors.TilesetsError(r.text)

    def validate_recipe(self, path: str):
        """ Check if recipe is valid according to Mapbox's specifications

        Args:
            path (str): Path to recipe file.

        Returns:
            r: API response
        """

        utils.validate_path(path)
        url = self._mkurl_val_rcp()

        with open(path, encoding="utf-8") as json_recipe:
            recipe_json = json.load(json_recipe)

            r = self._do_put(url, body=recipe_json)
            return r

    def get_ts_recipe(self, handle: str):
        """ Get a specific tileset's recipe

        Args:
            handle (str): Tileset handle

        Raises:
            errors.TilesetsError: Custom Mapbox Exception

        Returns:
            r: API response
        """

        ts_id = self._username + "." + handle
        url = self._mkurl_ts_rcp(ts_id)
        r = self._do_get(url)

        if r.status_code == 200:
            return r

        raise errors.TilesetsError(r.text)

    def update_ts_recipe(self, handle: str, path: str):
        """ Update a tileset's recipe

        Args:
            handle (str): Tileset handle
            path (str): Path to recipe file

        Raises:
            errors.TilesetsError: Custom Mapbox Exception

        Returns:
            r: API response
        """
        ts_id = self._username + "." + handle
        utils.validate_path(path)
        url = self._mkurl_ts_rcp(ts_id)

        with open(path, encoding="utf-8") as json_recipe:
            recipe_json = json.load(json_recipe)
            r = self._do_patch(url, body=recipe_json)

            if r.status_code in (201, 204):
                return r

            raise errors.TilesetsError(r.text)

    # SOURCE OPERATIONS
    def validate_source(self, paths: str or list[str]):
        """ Check if a source is valid according to Mapbox's specification

        Args:
            paths (str or list[str]): Path or list of paths to source files

        Returns:
            True (bool): Source files are valid
        """

        paths = utils.enforce_islist(paths)

        for index, path in enumerate(paths):
            utils.validate_path(path)
            ft = utils.load_feature(path)
            utils.validate_geojson(index, ft)

        return True

    def validate_source_id(self, value: str):
        """ Check if a source ID is valid according to Mapbox's specifications

        Args:
            value (string): String ID to validate.

        Raises:
            AssertionError: ID is not valid.

        Returns:
            True (bool): Source ID is valid
        """

        if re.match("^[a-zA-Z0-9-_]{1,32}$", value):
            return True
        raise AssertionError(
            'Invalid TS ID. Max-length: 32 chars and only include "-", "_", and alphanumeric chars.'
        )

    def upload_source(
            self,
            src_id: str,
            paths: str or list[str],
            replace: bool = False
    ):
        """ Upload a source to Mapbox's cloud storage.

        Args:
            src_id (str): ID for the source to be created or an existing source
            paths (string or list[str]): Path or list of paths of GeoJSON files.
            no_validation (bool, optional): Skip source validation. Defaults to False.
            replace (bool, optional): Replace an existing source. Defaults to False.

        """

        paths = utils.enforce_islist(paths)
        url = self._mkurl_src(src_id)
        method = "post"

        if replace:
            method = "put"

        with tempfile.TemporaryFile() as file:
            self.reformat_geojson(file, paths)

            file.seek(0)

            m = MultipartEncoder(fields={"file": ("file", file)})
            r = getattr(self._session, method)(
                url,
                data=m,
                headers={
                    "Content-Disposition": "multipart/form-data",
                    "Content-type": m.content_type,
                },
            )

        if r.status_code == 200:
            print(json.dumps(r.json(), indent=self._json_indent))
            return r

        raise errors.TilesetsError(r.text)

    def get_source(self, src_id: str):
        """ Get a source

        Args:
            src_id (str): Source ID

        Raises:
            errors.TilesetsError: Mapbox Custom Exception

        Returns:
            r: API response
        """
        url = self._mkurl_src(src_id)
        r = self._session.get(url)

        if r.status_code == 200:
            print(json.dumps(r.json(), indent=self._json_indent))
            return r

        raise errors.TilesetsError(r.text)

    def delete_source(self, src_id: str):
        """ Delete a specifc source

        Args:
            src_id (str): Source ID 

        Raises:
            errors.TilesetsError: Mapbox Custom Exception
            e: Re-raised Mapbox Exception

        Returns:
            r: API response
        """

        utils.time_check("deletion-src")
        url = self._mkurl_src(src_id)
        r = self._do_del(url)
        with open("deletion-src.txt", "w", encoding="utf-8") as f:
            f.close()

        if r.status_code == 204:
            return r

        raise errors.TilesetsError(r.text)

    def list_sources(self):
        """ List all currently uploaded sources

        Raises:
            errors.TilesetsError: Mapbox Custom Exception

        Returns:
            r: API response
        """

        url = self._mkurl_srclist()
        r = self._do_get(url)

        if r.status_code == 200:
            for source in r.json():
                print(source["id"])

            return r

        raise errors.TilesetsError(r.text)

    def estimate_area(
            self,
            features: list[str] or str,
            precision: str,
            no_validation: bool = False,
            force_1cm: bool = False
    ):
        """ Estimate the total area covered by a tileset in order to estimate pricing

        Args:
            features (list[str] or str): List of GeoJSON feature
            precision (str): Selected estimate precision
            no_validation (bool, optional): Skip validation. Defaults to False.
            force_1cm (bool, optional): Force 1cm precision. 
                This is an optional feature that needs to be agreed on with Mapbox's teams.
                Defaults to False.

        Raises:
            errors.TilesetsError: Mapbox Custom Exception
            errors.TilesetsError: Mapbox Custom Exception
            errors.TilesetsError: Mapbox Custom Exception

        Returns:
            r (API Response): Tileset area estimate
        """

        features = utils.enforce_islist(features)
        features = map(utils.load_feature, features)

        filter_features = utils.load_module(
            "supermercado.super_utils").filter_features

        area = 0
        if precision == "1cm" and not force_1cm:
            raise errors.TilesetsError(
                "The force_1cm arg must be present and the option must \
                be enabled through Mapbox support.")
        if precision != "1cm" and force_1cm:
            raise errors.TilesetsError(
                "The force_1cm arg is enabled but the precision is not 1cm."
            )

        try:
            # expect users to bypass source validation when users rerun
            # if their features passed validation previously
            if not no_validation:
                features = utils.validate_stream(features)
            # It is a list because calculate_tiles_area does not work with a stream
            features = list(filter_features(features))
        except (ValueError, json.decoder.JSONDecodeError) as exc:
            raise errors.TilesetsError(
                "Error with feature parsing."
                "Ensure that feature inputs are valid and formatted correctly."
            ) from exc

        area = utils.calculate_tiles_area(features, precision)
        area = str(int(round(area)))
        message = json.dumps({
            "km2": area,
            "precision": precision,
            "pricing_docs": "https://www.mapbox.com/pricing/#tilesets",
        })

        print(message)
        return message

    def list_activity(
            self,
            sortby: str = "requests",
            orderby: str = "desc",
            limit: int = 100,
            start: str = None
    ):
        """ Get a list of tileset operations

        Args:
            sortby (str, optional): Selected sorting. Defaults to "requests".
            orderby (str, optional): Selected ordering. Defaults to "desc".
            limit (int, optional): Max number of listed operations. Defaults to 100.
            start (str, optional): Pagination key. Defaults to None.

        Raises:
            errors.TilesetsError: Custom Mapbox Exception

        Returns:
            result (dict): API response and pagination key for chaining requests.
        """

        url = self._mkurl_activity(sortby, orderby, limit, start)
        r = self._do_get(url)

        if r.status_code == 200:
            if r.headers.get("Link"):
                url = re.findall(r"<(.*)>;", r.headers.get("Link"))[0]
                query = urlparse(url).query
                start = parse_qs(query)["start"][0]

            result = {
                "data": r.json(),
                "next": start,
            }
            return result

        raise errors.TilesetsError(r.text)


class MtsHandler(MtsHandlerBase, metaclass=utils.Singleton):
    """ Singleton class for the handler """
