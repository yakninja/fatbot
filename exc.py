class FatbotError(Exception):
    """Generic error class."""
    pass


class FoodNotFound(FatbotError):
    pass


class UnitNotFound(FatbotError):
    pass


class UnitNotDefined(FatbotError):
    pass
