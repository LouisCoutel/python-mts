"""

This module exposes a handler class for Mapbox Tiling Service and Mapbox's API operations.

"""

import json
import logging
import os
import tempfile
from urllib.parse import urlencode, urlparse, parse_qs
import base64
import re
from dotenv import load_dotenv
from requests_toolbelt import MultipartEncoder

from python_mts import utils, errors

load_dotenv()

class MtsHandlerBase:
    """

    This class exposes methods that allow interacting with the Mapbox Tiling Service,
    like uploading sources, generating tilesets or retrieving activity reports.

    """

    def __init__(self):
        self._username: str = os.getenv("MAPBOX_USER_NAME")
        self._token: str = os.getenv("MAPBOX_ACCESS_TOKEN")
        self._api = "https://api.mapbox.com"
        self._default_recipe: str
        self._json_indent: int = 4
        self._attribution: json = None
        self._session = utils._get_session()


    # REQUEST WRAPPERS
    def _do_post(self, url: str, body = None):
        s = self._session
        if body:
            r = s.post(url, json = body)
        else:
            r = s.post(url)
        return r


    def _do_patch(self, url: str, body = None):
        s = self._session
        if body:
            r = s.patch(url, json = body)
        else:
            r = s.patch(url)
        return r


    def _do_put(self, url: str, body):
        s = self._session
        print(json)
        return s.put(url, json = body)


    def _do_get(self, url: str):
        s = self._session
        return s.get(url)


    def _do_del(self, url: str):
        s = self._session
        return s.delete(url)


    # GETTERS
    def get_default_recipe(self):
        return self._default_recipe

    def get_json_indent(self):
        return self._json_indent

    def get_session(self):
        return self._session


    # SETTERS
    def set_default_recipe(self, path: str):
        utils.validate_path(path)
        self._default_recipe = os.path.abspath(path)

    def set_indent(self, indent: int):
        self._json_indent = indent


    # URL BUILDERS
    # URL for a specific tileset
    def _mkurl_ts(self, ts_id: str, publish: bool = None):

        """ Generate the URL needed for most tileset operations.

        Args:
            ts_id (string): Tileset ID (username.handle)
            publish (bool, optional): Option to get publish URL. Disabled by default.

        """

        if publish:
            return f"{self._api}/tilesets/v1/{ts_id}/publish?access_token={self._token}"

        return f"{self._api}/tilesets/v1/{ts_id}?access_token={self._token}"


    # URL for a specific tileset's jobs
    def _mkurl_ts_jobs(self, ts_id: str, stage: str = None, limit: int = 100):

        """ Generate the URL needed for accessing a tileset's jobs.

        Args:
            ts_id (str): Tileset ID (username.handle)
            stage (str, optional): Job-stage filter. Defaults to None.
            limit (int, optional): Max number of jobs listed. Defaults to 100.
        """

        url = f"{self._api}/tilesets/v1/{ts_id}/jobs?access_token={self._token}"
        url = f"{self._api}&stage={stage}" if stage else url
        url = f"{self._api}&limit={limit}" if limit else url
        return url


    # URL for a specific tileset's tilejson
    def _mkurl_tjson(self, handles: list[str], secure: bool):
        """ Generate the URL needed for accessing a tileset's tileJSON.

        Args:
            handles (list of strings): Handles (name) of tilesets. 
            Combined with the username they form a tileset's id (username.handle).
            secure (boolean): Optional parameter that instructs Mapbox API to respond through HTTPS.

        Raises:
            errors.TilesetNameError: _description_

        Returns:
            _type_: _description_
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


    # URL for a specific tileset job
    def _mkurl_ts_job(self, ts_id, job_id):
        return f"{self._api}/tilesets/v1/{ts_id}/jobs/{job_id}?access_token={self._token}"


    # URL for a list of tilesets
    def _mkurl_tslist(self, ts_type = None, limit= None, visibility = None, sortby = None):
        url = f"{self._api}/tilesets/v1/{self._username}?access_token={self._token}"
        url = f"{url}&limit={limit}" if limit else url
        url = f"{url}&type={ts_type}" if ts_type else url
        url = f"{url}&visibility={visibility}" if visibility else url
        url = f"{url}&sortby={sortby}" if sortby else url

        return url


    # URL for a tileset's recipe
    def _mkurl_ts_rcp(self, ts_id: str):
        return f"{self._api}/tilesets/v1/{ts_id}/recipe?access_token={self._token}"


    # URL for validating a tileset's recipe
    def _mkurl_val_rcp(self):
        return f"{self._api}/tilesets/v1/validateRecipe?access_token={self._token}"


    # URL for a specific source
    def _mkurl_src(self, src_id):
        return f"{self._api}/tilesets/v1/sources/{self._username}/{src_id}?access_token={self._token}"


    # URL for a list of all sources
    def _mkurl_srclist(self):
        return f"{self._api}/tilesets/v1/sources/{self._username}?access_token={self._token}"


    # URL for a complete report on tileset related activity
    def _mkurl_activity(self, sortby, orderby, limit, start):
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
    # Tileset Operation request body
    def _mkbody_tileset(
            self,
            name: str,
            private: bool,
            desc: str = None,
            recipe_path: str = None,
            update: bool = False
            ):

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
                raise errors.TilesetsError("Unable to parse attribution JSON") from exc

        return body


    # RESPONSES UTILS
    # Parse response and return a tileset's status based on it's latest job
    def _mkstatus(self, response):
        status = {}
        for job in response.json():
            status["id"] = job["tilesetId"]
            status["latest_job"] = job["id"]
            status["status"] = job["stage"]

        return status


    # TILESETS OPERATIONS
    # Create a new tileset
    def create_ts(
            self,
            handle: str,
            name: str,
            recipe_path: str = None,
            desc: str = None,
            private: bool = False
            ):

        ts_id = self._username + "." + handle
        if not utils.validate_tileset_id(ts_id):
            logging.error(ts_id)

        url = self._mkurl_ts(ts_id)
        body = self._mkbody_tileset(name, private, desc, recipe_path)

        r = self._do_post(url, body = body)

        print(json.dumps(r.json(), indent=self._json_indent))
        return r


    # Publish a specific tileset
    def publish_ts(self, handle: str):
        ts_id = self._username + "." + handle
        url = self._mkurl_ts(ts_id, publish = True)
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


    # Update a specific tileset
    def update_ts(self, handle: str, name: str = None, desc: str = None, private: bool = False):
        ts_id = self._username + "." + handle
        url = self._mkurl_ts(ts_id)
        body = self._mkbody_tileset(name, private, desc, update = True)
        r = self._do_patch(url, body = body)

        if r.status_code != 204:
            raise errors.TilesetsError(r.text)

        return r


    # Delete a specific tileset
    def delete_ts(self, handle: str):
        ts_id = self._username + "." + handle
        url = self._mkurl_ts(ts_id)

        try:
            utils.time_check("deletion-ts")
            r = self._do_del(url)
            f = open("deletion-ts.txt","w", encoding="utf-8")
            f.close()

            if r.status_code == 200 or r.status_code == 204:
                print("Tileset deleted.")
                return r
            else:
                raise errors.TilesetsError(r.text)

        except errors.TilesetsError as e:
            raise e


    # Get the current status of a tileset
    def get_ts_status(self, handle: str):
        ts_id = self._username + "." + handle
        url = self._mkurl_ts_jobs(ts_id)
        r = self._do_get(url)

        if r.status_code != 200:
            raise errors.TilesetsError(r.text)

        status = self._mkstatus(r)
        print(json.dumps(status, indent = self._json_indent))

        return status


    # Get the tilejson of a specific tileset
    def get_tilejson(self, handles: str or list[str], secure: bool = True):
        handles = utils.enforce_islist(handles)

        url = self._mkurl_tjson(handles, secure)
        print(url)
        r = self._do_get(url)

        if r.status_code == 200:
            print(json.dumps(r.json(), indent=self._json_indent))
            return r
        else:
            raise errors.TilesetsError(r.text)


    # Get a list of jobs for a specific tileset
    def list_ts_jobs( self, handle: str, stage: str = None, limit: int = 100):
        ts_id = self._username + "." + handle
        url = self._mkurl_ts_jobs(ts_id, stage = stage, limit = limit)
        r = self._do_get(url)

        print(json.dumps(r.json(), indent=self._json_indent))
        return r


    # Get the status of a specific job for a specific tileset
    def get_ts_job(self, handle: str, job_id: str):
        ts_id = self._username + "." + handle
        url = self._mkurl_ts_job(ts_id, job_id)
        r = self._session.get(url)

        print(json.dumps(r.json(), indent=self._json_indent))
        return r


    # Get a list of tilesets
    def list_tsets(
            self,
            verbose: bool = False,
            ts_type: str = None,
            visibility: str = None,
            sortby: str = None,
            limit: int = 100
            ):

        url = self._mkurl_tslist(ts_type, limit, visibility, sortby)
        r = self._do_get(url)

        if r.status_code == 200:
            if verbose:
                for tileset in r.json():
                    print(json.dumps(tileset, indent=self._json_indent))
            else:
                for tileset in r.json():
                    print(tileset["id"])

            return r
        else:
            raise errors.TilesetsError(r.text)


    # Validate a recipe
    def validate_recipe(self, path: str):
        utils.validate_path(path)
        url = self._mkurl_val_rcp()
        log = logging.getLogger('urllib3')

        log.setLevel(logging.DEBUG)

        with open(path, encoding="utf-8") as json_recipe:
            recipe_json = json.load(json_recipe)

            r = self._do_put(url, body = recipe_json)
            print(json.dumps(r.json(), indent=self._json_indent))
            return r


    # Get a tileset's recipe
    def get_ts_recipe(self, handle: str):
        ts_id = self._username + "." + handle
        url = self._mkurl_ts_rcp(ts_id)
        r = self._do_get(url)

        if r.status_code == 200:
            print(json.dumps(r.json(), indent=self._json_indent))
            return r
        else:
            raise errors.TilesetsError(r.text)


    def update_ts_recipe(self, handle: str, path: str):
        ts_id = self._username + "." + handle
        utils.validate_path(path)
        url = self._mkurl_ts_rcp(ts_id)

        with open(path, encoding="utf-8") as json_recipe:
            recipe_json = json.load(json_recipe)
            r = self._do_patch(url, body = recipe_json)

            if r.status_code == 201 or r.status_code == 204:
                print("Updated recipe.")
                return r
            else:
                raise errors.TilesetsError(r.text)


    # SOURCE OPERATIONS
    # Validate a source
    def validate_source(self, paths: str or list[str]):
        paths = utils.enforce_islist(paths)

        print("Validating features")
        for index, path in enumerate(paths):
            utils.validate_path(path)
            ft = utils.load_feature(path)
            utils.validate_geojson(index, ft)

        print("✔ valid")
        return "✔ valid"


    # Validate a source ID
    def validate_source_id(self, value: str):
        """ Check if a source id is valid.

        Args:
            value (string): The string ID to validate.

        Raises:
            Exception: ID is not valid.

        Returns:
            value: The ID passed to the function.
        """

        if re.match("^[a-zA-Z0-9-_]{1,32}$", value):
            return value
        raise AssertionError(
            'Invalid TS ID. Max-length: 32 chars and only include "-", "_", and alphanumeric chars.'
        )


    # Upload a source
    def upload_source(
            self,
            src_id: str,
            paths: str or list[str],
            no_validation: bool = False,
            replace: bool = False
            ):

        """ Upload a source to Mapbox's cloud storage.

        Args:
            src_id (str): The id chosen for the source or an existing source's ID.
            paths (string or list[str]): A filepath or list of filepaths pointing to GeoJSON files.
            no_validation (bool, optional): Option to skip source validation. Defaults to False.
            replace (bool, optional): Option to replace an existing source. Defaults to False.

        """

        paths = utils.enforce_islist(paths)
        url = self._mkurl_src(src_id)
        method = "post"

        if replace:
            method = "put"

        # This does the decoding by hand instead of using pyjwt because
        # pyjwt rejects tokens that don't pad the base64 with = signs.
        token_parts = self._token.split(".")
        if len(token_parts) < 2:
            raise errors.TilesetsError(f"Token {self._token} does not contain a payload component")


        while len(token_parts[1]) % 4 != 0:
            token_parts[1] = token_parts[1] + "="
        body = json.loads(base64.b64decode(token_parts[1]))

        if "u" in body:
            if self._username != body["u"]:
                raise errors.TilesetsError(
                    f"Token username {body['u']} does not match username {self._username}"
                )
        else:
            raise errors.TilesetsError(
                f"Token {self._token} does not contain a self._username"
            )

        with tempfile.TemporaryFile() as file:
            for index, path in enumerate(paths):
                feature = utils.load_feature(path)
                if not no_validation:
                    utils.validate_geojson(index, feature)

                file.write(
                    (json.dumps(feature, separators=(",", ":")) + "\n").encode("utf-8")
                )

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

        else:
            raise errors.TilesetsError(r.text)


    # Get a specific uploaded source
    def get_source(self, src_id: str):
        url = self._mkurl_src(src_id)
        r = self._session.get(url)

        if r.status_code == 200:
            print(json.dumps(r.json(), indent=self._json_indent))
            return r
        else:
            raise errors.TilesetsError(r.text)


    # Delete a specific source
    def delete_source(self, src_id: str):
        try:
            utils.time_check("deletion-src")
            url = self._mkurl_src(src_id)
            r = self._do_del(url)
            f = open("deletion-src.txt","w", encoding="utf-8")
            f.close()

            if r.status_code == 204:
                print("Source deleted.")
                return r
            else:
                raise errors.TilesetsError(r.text)

        except errors.TilesetsError as e:
            raise e


    # List all sources
    def list_sources(self):
        url = self._mkurl_srclist()
        r = self._do_get(url)

        if r.status_code == 200:
            for source in r.json():
                print(source["id"])

            return r
        else:
            raise errors.TilesetsError(r.text)


    # Estimate the area of a tileset generated with a specific source
    def estimate_area(
            self,
            features: list[str] or str,
            precision: str,
            no_validation: bool = False,
            force_1cm: bool = False
            ):

        features = utils.enforce_islist(features)
        features = map(utils.load_feature, features)

        filter_features = utils.load_module("supermercado.super_utils").filter_features

        area = 0
        if precision == "1cm" and not force_1cm:
            raise errors.TilesetsError(
                "The force_1cm arg must be present and the option must be enabled through Mapbox support.")
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
                "Error with feature parsing. Ensure that feature inputs are valid and formatted correctly."
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


    # List tileset activity for an account.
    def list_activity(
            self,
            sortby: str = "requests",
            orderby: str = "desc",
            limit: int = 100,
            start: str = None
            ):
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
            print(result)
            return result

        raise errors.TilesetsError(r.text)


class MtsHandler(MtsHandlerBase, metaclass = utils.Singleton):
    """ 

    Singleton class for the handler.

    """
