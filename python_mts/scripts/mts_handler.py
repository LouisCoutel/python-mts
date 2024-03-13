""" This module exposes a handler class for Mapbox Tiling Service and Mapbox's API operations. """
import json
import logging
import os
import tempfile
from urllib.parse import urlparse, parse_qs
import re
from dotenv import load_dotenv
from requests_toolbelt import MultipartEncoder
from supermercado.super_utils import filter_features

from python_mts import utils, errors
from python_mts.urls import Urls
from python_mts.client import Client

load_dotenv()


class MtsHandlerBase:
    """ Exposes methods for interacting with the Mapbox Tiling Service.
    Base class to be paired with a Singleton meta-class """

    def __init__(self):
        self._username: str = os.getenv("MAPBOX_USER_NAME")
        self._token: str = os.getenv("MAPBOX_ACCESS_TOKEN")
        self.urls = Urls()
        self.client = Client()
        self._attribution: json = None

    def _mkbody_tileset(
            self,
            name: str,
            private: bool = True,
            desc: str = None,
            recipe_path: str = None,
            update: bool = False
    ):
        """ Generate the request body for various tileset operations.

        Args:
            name (str): Tileset name.
            private (bool): Set tileset visibility to private.
                Defaults to True.
            desc (str, optional): Tileset description.
                Defaults to None.
            recipe_path (str, optional): Path pointing to recipe file.
                Defaults to None.
            update (bool, optional): Specify if the request body to be generated is for an update.
                Defaults to False.

        Returns:
            body (dict): Request body. """

        body = {}
        body["name"] = name
        body["description"] = desc if desc else ""
        body["private"] = private

        if not update:
            recipe = recipe_path
            with open(recipe, encoding="utf-8") as json_recipe:
                body["recipe"] = json.load(json_recipe)

        if self._attribution:
            try:
                body["attribution"] = json.loads(self._attribution)
            except Exception as exc:
                raise errors.TilesetsError(
                    "Unable to parse attribution JSON") from exc

        return body

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
            handle (str): Tileset handle.
            name (str): Tileset name.
                Defaults to None.
            recipe_path (str, optional): Path to the recipe file.
                Defaults to None.
            desc (str, optional): Tileset description.
                Defaults to None.
            private (bool, optional): Set visibility to private.
                Defaults to False. """

        ts_id = self._username + "." + handle
        if not utils.validate_tileset_id(ts_id):
            raise errors.InvalidId(ts_id)

        url = self.urls.mkurl_ts(ts_id)
        body = self._mkbody_tileset(name, private, desc, recipe_path)
        r = self.client.do_post(url, body=body)

        if r.status_code == 200:
            content = r.json()
            return content

        raise errors.TilesetsError(r.text)

    # Publish a specific tileset

    def publish_ts(self, handle: str):
        """ Publish a tileset.

        Args:
            handle (str): Tileset handle. """

        ts_id = self._username + "." + handle
        url = self.urls.mkurl_ts(ts_id, publish=True)
        r = self.client.do_post(url)
        if r.status_code == 200:
            response_msg = r.json()
            print(json.dumps(response_msg))
            studio_url = f"https://studio.mapbox.com/tilesets/{ts_id}"
            msg = f"Tileset job received. Visit {studio_url} to view the status of your tileset."
            print(msg)

        else:
            logging.error(r.text)

        content = r.json()
        return content

    def update_ts(self, handle: str, name: str = None, desc: str = None, private: bool = False):
        """ Update a tileset's informations.

        Args:
            handle (str): Tileset handle
            name (str, optional): Tileset name. Defaults to None.
            desc (str, optional): Tileset description. Defaults to None.
            private (bool, optional): Set visibility to private.
                Defaults to False. """

        ts_id = self._username + "." + handle
        url = self.urls.mkurl_ts(ts_id)
        body = self._mkbody_tileset(name, private, desc, update=True)
        r = self.client.do_patch(url, body=body)

        if r.status_code != 204:
            raise errors.TilesetsError(r.text)

        return f"Tileset {handle} successfully updated."

    def delete_ts(self, handle: str):
        """ Delete a specific tileset.

        Args:
            handle (str): Tileset handle

        Raises:
            errors.TilesetsError: Custom exception.
            e: Re-raised Custom Mapbox Exception. """

        ts_id = self._username + "." + handle
        url = self.urls.mkurl_ts(ts_id)

        try:
            r = self.client.do_del(url)
            with open("deletion-ts.txt", "w", encoding="utf-8") as f:
                f.close()

            if r.status_code in (200, 204):
                content = r.json()
                return content

            raise errors.TilesetsError(r.text)

        except errors.TilesetsError as e:
            raise e

    def get_ts_status(self, handle: str):
        """ Get a tileset's current status.

        Args:
            handle (str): Tileset handle.

        Returns:
            status (dict): Tileset status information based on last job executed. """

        ts_id = self._username + "." + handle
        url = self.urls.mkurl_ts_jobs(ts_id)
        r = self.client.do_get(url)

        if r.status_code != 200:
            raise errors.TilesetsError(r.text)

        return utils.mk_status(r.json())

    def get_tilejson(self, handles, secure: bool = True):
        """ Get a tileset's corresponding tileJSON data.

        Args:
            handles (str or list[str]): A single tileset handle or a list of handles.
            secure (bool, optional): Force request to use HTTPS. Defaults to True. """

        handles = utils.enforce_islist(handles)

        url = self.urls.mkurl_tjson(handles, secure)
        r = self.client.do_get(url)

        if r.status_code == 200:
            content = r.json()
            return content

        raise errors.TilesetsError(r.text)

    def get_ts_jobs(self, handle: str, stage: str = None, limit: int = 100, job_id: str = None):
        """ Gets either a list of jobs or a single specific job corresponding to a tileset.

        Args:
            handle (str): Tileset handle.
            stage (str, optional): Filter jobs by stage. Defaults to None.
            limit (int, optional): Max number of jobs listed. Defaults to 100.
            job_id (str, optional): Get only a specific job. Defaults to None. """

        ts_id = self._username + "." + handle

        url = self.urls.mkurl_ts_job(
            ts_id, job_id) if job_id else self.urls.mkurl_ts_jobs(
            ts_id, stage=stage, limit=limit)

        r = self.client.do_get(url)

        content = r.json()
        return content

    def list_tsets(
            self,
            ts_type: str = None,
            visibility: str = None,
            sortby: str = None,
            limit: int = 100
    ):
        """ Get a list of uploaded tilesets.

        Args:
            ts_type (str, optional): Type of tilesets to list.
                Defaults to None.
            limit (int): Max number of tilesets listed.
                Max 500.
                Defaults to None.
            visibility (str, optional): Filter by visibility.
                Accepts "public" or "private".
                Defaults to None.
            sortby (str, optional): Sorting preference.
                Accepts "created" or "modified".
                Defaults to None. """

        url = self.urls.mkurl_tslist(ts_type, limit, visibility, sortby)
        r = self.client.do_get(url)

        if r.status_code == 200:
            content = r.json()
            return content

        raise errors.TilesetsError(r.text)

    def validate_recipe(self, path: str):
        """ Check if recipe is valid according to Mapbox's specifications.

        Args:
            path (str): Path to recipe file. """

        utils.validate_path(path)
        url = self.urls.mkurl_val_rcp()

        with open(path, encoding="utf-8") as json_recipe:
            recipe_json = json.load(json_recipe)

            r = self.client.do_put(url, body=recipe_json)
            content = r.json()
            return content

    def get_ts_recipe(self, handle: str):
        """ Get a specific tileset's recipe.

        Args:
            handle (str): Tileset handle. """

        ts_id = self._username + "." + handle
        url = self.urls.mkurl_ts_rcp(ts_id)
        r = self.client.do_get(url)

        if r.status_code == 200:
            content = r.json()
            return content

        raise errors.TilesetsError(r.text)

    def update_ts_recipe(self, handle: str, path: str):
        """ Update a tileset's recipe.

        Args:
            handle (str): Tileset handle.
            path (str): Path to recipe file. """

        ts_id = self._username + "." + handle
        utils.validate_path(path)
        url = self.urls.mkurl_ts_rcp(ts_id)

        with open(path, encoding="utf-8") as json_recipe:
            recipe_json = json.load(json_recipe)
            r = self.client.do_patch(url, body=recipe_json)

            if r.status_code == 204:
                return f"Tileset {handle}'s recipe successfully updated."

            raise errors.TilesetsError(r.text)

    # SOURCE OPERATIONS
    def upload_source(
            self,
            src_id: str,
            paths,
            replace: bool = False
    ):
        """ Upload a source to Mapbox's cloud storage.

        Args:
            src_id (str): ID for the source to be created or an existing source.
            paths (string or list[str]): Path or list of paths of GeoJSON files.
            no_validation (bool, optional): Skip source validation.
                Defaults to False.
            replace (bool, optional): Replace an existing source.
                Defaults to False. """

        paths = utils.enforce_islist(paths)
        url = self.urls.mkurl_src(src_id)
        method = "post"

        if replace:
            method = "put"

        with tempfile.TemporaryFile() as file:
            utils.reformat_geojson(file, paths)

            file.seek(0)

            m = MultipartEncoder(fields={"file": ("file", file)})
            r = self.client.do_multipart(url, m, method)

        if r.status_code == 200:
            content = r.json()
            return content

        raise errors.TilesetsError(r.text)

    def get_source(self, src_id: str):
        """ Retrieve a source informations.

        Args:
            src_id (str): Source ID. """

        url = self.urls.mkurl_src(src_id)
        r = self.client.do_get(url)

        if r.status_code == 200:
            content = r.json()
            return content

        raise errors.TilesetsError(r.text)

    def delete_source(self, src_id: str):
        """ Delete a specifc source

        Args:
            src_id (str): Source ID.

        Raises:
            errors.TilesetsError: Custom exception.
            e: Re-raised Mapbox exception. """

        url = self.urls.mkurl_src(src_id)
        r = self.client.do_del(url)

        if r.status_code == 204:
            return f"Source {src_id} successfully deleted."

        raise errors.TilesetsError(r.text)

    def list_sources(self):
        """ List all uploaded sources. """

        url = self.urls.mkurl_srclist()
        r = self.client.do_get(url)

        if r.status_code == 200:
            for source in r.json():
                print(source["id"])

            content = r.json()
            return content

        raise errors.TilesetsError(r.text)

    def estimate_area(
            self,
            features,
            precision: str,
            no_validation: bool = False,
            force_1cm: bool = False
    ):
        """ Estimate the total area covered by a tileset in order to estimate pricing.

        Args:
            features: List of GeoJSON features.
            precision (str): Selected estimate precision.
            no_validation (bool, optional): Skip validation.
                Defaults to False.
            force_1cm (bool, optional): Force 1cm precision. 
                This is an optional feature that needs to be agreed on with Mapbox's teams.
                Defaults to False. """

        features = utils.enforce_islist(features)
        features = map(utils.load_feature, features)

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

        return message

    def list_activity(
            self,
            sortby: str = "requests",
            orderby: str = "desc",
            limit: int = 100,
            start: str = None
    ):
        """ Get an account's tileset-related activity report.

        Args:
            sortby (str, optional): Selected sorting. Defaults to "requests".
            orderby (str, optional): Selected ordering. Defaults to "desc".
            limit (int, optional): Max number of listed operations. Defaults to 100.
            start (str, optional): Pagination key. Defaults to None.

        """

        url = self.urls.mkurl_activity(sortby, orderby, limit, start)
        r = self.client.do_get(url)

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

    def list_styles(self, draft: bool = False, limit: int = None, start_id: str = None):
        """ Retrieve a list of styles.

        Args:
            draft (bool, optional): Request draft styles only.
                Defaults to False.
            limit (int, optional): Set a limit to the number of styles listed.
                Defaults to None.
            start_id (str, optional): Start the list at a specific style ID.
                Defaults to None. """

        url = self.urls.mkurl_liststyles(draft, limit, start_id)

        r = self.client.do_get(url)

        if r.status_code == 200:
            content = r.json()
            return content

        raise errors.StylesError("Unable to fetch list of styles")


class MtsHandler(MtsHandlerBase, metaclass=utils.Singleton):
    """ Singleton class for the handler """
