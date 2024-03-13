""" Base client class """
from python_mts import utils


class Client:
    """ Client. """

    def __init__(self):
        self._session = utils._get_session()

    def get_session(self):
        """ Getter """
        return self._session

    # REQUEST WRAPPERS
    def do_multipart(self, url: str, m, method: str):
        """ Send multipart data. """
        return getattr(self._session, method)(
            url,
            data=m,
            headers={
                "Content-Disposition": "multipart/form-data",
                "Content-type": m.content_type,
            }
        )

    def do_post(self, url: str, body=None):
        """ Post request."""
        if body:
            return self._session.post(url, json=body)

        return self._session.post(url)

    def do_patch(self, url: str, body=None):
        """ Patch request. """
        if body:
            return self._session.patch(url, json=body)

        return self._session.patch(url)

    def do_put(self, url: str, body):
        """ Put request. """
        return self._session.put(url, json=body)

    def do_get(self, url: str):
        """ Get request."""
        return self._session.get(url)

    def do_del(self, url: str):
        """ Delete request. """
        return self._session.delete(url)
