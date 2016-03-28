from pubsub import pub


class BaseSettings(object):
    """
    Base settings module for YAIB.
    In-memory only - Must be extended to perform actual settings functionality.
    Subclasses should extend this class and overwrite the loadSettings and
    saveSettings functions to customize persistence.

    Uses '.' delimited strings to make accessing settings convenient.
    You can configure which character to use for delimiting by setting
    the `delimiter` field in the settings configuration.
    """

    def __init__(self, configuration={}):
        """Initialize the module"""
        self._settings = {}
        self._configure(configuration)

    def _configure(self, configuration):
        """Called on init with the bot configuration."""
        self._delimiter = '.'
        if hasattr(configuration, 'delimiter'):
            configuration.delimiter

    def loadSettings(self):
        """
        Called to populate all the settings into memory if necessary.
        Return True on Success, False on Failure.
        """
        pub.sendMessage('settings:loaded')
        return True

    def saveSettings(self):
        """
        Called to flush all the settings to storage if necessary.
        Return True on Success, False on Failure.
        """
        pub.sendMessage('settings:saved')

    def set(self, key, value, initial=False, more=False):
        """
        Called to set a particular setting.
        @param key: string key for setting
        @param value: string value for key
        @param initial: (default False) boolean - if True, will only set value
            if it doesn't already exist in the database.
        @param more: (default False) boolean if more settings are immediately
            being added. Can be used to help prevent unnecessary rapid fire
            writes.
        """

        subkeys = key.split('.')
        subkeys.reverse()
        node = self._settings

        while len(subkeys) > 0:
            is_leaf = len(subkeys) == 1
            subkey = subkeys.pop()

            # if this is the leaf, set it
            if is_leaf:
                if not initial or subkey not in node:
                    node[subkey] = value
                    break

            # look for this key in the current node
            if subkey in node:
                # set current node and try the next subkey
                node = node[subkey]
            else:
                # does not exist - create an empty dict for it
                node[subkey] = {}
                node = node[subkey]

        if not more:
            self.afterUpdate()

    def setMulti(self, settingsDict, initial=False):
        """
        Called to set a bunch of settings at once.
        Simply pipes them to set individually while setting the more flag.

        @param settingsDict: dictionary of key, value settings to save
        @param initial: (default False) boolean - if True, will only set value
            if it doesn't already exist in the database.
        """

        count = len(settingsDict)
        for k, v in settingsDict.iteritems():
            count -= 1
            self.set(k, v, initial, more=count > 0)

    def afterUpdate(self):
        """
        Called after a write (or batch of writes).
        Saves the current settings and notifies the bot.
        """
        self.saveSettings()
        pub.sendMessage('settings:updated')

    def get(self, key, default=None):
        """
        Return the given setting.
        If the setting is not found, returns None or the given default.

        @param key: string key to fetch
        @param default: (default None) value to return if key not found
        """
        subkeys = key.split('.')
        subkeys.reverse()
        node = self._settings

        while len(subkeys) > 0:
            is_leaf = len(subkeys) == 1
            subkey = subkeys.pop()

            # look for this key in the current node
            if subkey in node:
                # if this is the leaf, return it
                if is_leaf:
                    return node[subkey]
                else:
                    # set current node and try the next node
                    node = node[subkey]
            else:
                # does not exist - return default
                return default

    def getMulti(self, keys, default=None):
        """
        Returns a dict of multiple settings at once. If the requested key is
        not found, returns None or the given default.

        @param keys: list of keys
        @param default: (default None) value to return if key not found
        """
        return dict([
            (k, self.get(k, default=default)) for k in keys
        ])
