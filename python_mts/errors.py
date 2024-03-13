""" Custom exceptions """


class TilesetsError(Exception):
    """ Base Tilesets error """

    def __init__(self, message):
        """ Exception constructor """
        self.message = message


class InvalidId(TilesetsError):
    """ Not a valid tileset id. """

    def __init__(self, tileset_id):
        """ Exception constructor """

        super().__init__(f"Invalid Tileset ID: {tileset_id}")

    def __str__(self):
        return self.message


class StylesError(Exception):
    """ Base Styles error """

    def __init__(self, message):
        """ Exception constructor """

        self.message = message


class InvalidGeoJSON(Exception):
    """ Data is not valid GeoJSON """

    def __init__(self, index, feature: dict):
        """ Exception constructor """

        self.message = f"Feature at index {index} is not valid GeoJSON data."
        self.feature = feature
