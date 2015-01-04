
def dictToObject(d):
    """
    Accepts a dictionary and returns an object with properties
    matching the keys and values from the original dict. If the
    key is not in the dict, returns the default given to the
    constructor (defaults to None).
    """
    class Container(object):

        def __init__(self, d, default=None):
            self._d = d
            self._default = None

        def __getitem__(self, *args, **kwargs):
            return object.__getattribute__(self, '_d')\
                    .__getitem__(*args, **kwargs)

        def __getattribute__(self, key, context=None):
            if key in [
                    'keys', 'iterkeys',
                    'values', 'itervalues'
                    'items', 'iteritems',
                    '__len__', '__eq__']:
                return getattr(object.__getattribute__(self, '_d'), key)

            value = object \
                .__getattribute__(self, context or '_d') \
                .get(
                    key,
                    object.__getattribute__(self, '_default')
                )
            if value and type(value) == type({}):
                return Container(value)
            return value

    return Container(d)
