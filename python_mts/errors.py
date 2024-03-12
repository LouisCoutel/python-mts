""" Custom exceptions """


class TilesetsError(Exception):
    """ Base Tilesets error """

    def __init__(self, message):
        """ Exception constructor """
        self.message = message


class TilesetNameError(TilesetsError):
    """Not a valid tileset id"""

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
