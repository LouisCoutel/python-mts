""" Custom exceptions """


class TilesetsError(Exception):
    """ Base Tilesets error """

    def __init__(self, message: str):
        """ Exception constructor """
        self.message = message


class InvalidId(TilesetsError):
    """ Not a valid tileset id. """

    def __init__(self, tileset_id: str):
        """ Exception constructor """

        super().__init__(f"Invalid Tileset ID: {tileset_id}")

    def __str__(self):
        return self.message


class StylesError(Exception):
    """ Base Styles error """

    def __init__(self, message: str):
        """ Exception constructor """

        self.message = message


class InvalidGeoJSON(Exception):
    """ Data is not valid GeoJSON """

    def __init__(self, feature: dict):
        """ Exception constructor """

        self.message = "Feature is not valid GeoJSON data."
        self.feature = feature


class CalcAreaError(Exception):
    """ Error when calculating a feature's area. """

    def __init__(self, message: str):
        """ Exception constructor """
        self.message = message


class MinPrecisionError(CalcAreaError):
    """ Error when asking to be precise to the centimeter. """
