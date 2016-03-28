import time
import logging
from pubsub import pub


class AdminManager(object):
    """
    Admin module for YAIB.


    To Enable Admin Features, the configuration file must contain an
    `admin` section which can include the following:
    - `enabled` (boolean, required) - defaults to False
    - `admin_type` (string, required) - 'stupid' or 'simple'

    - `admin_password` - (string) master password for 'stupid' type
    - `admins` (dict) - dict of admins in the form {'nick': 'password'} for
                        'simple' type
    - `admin_timeout` - (int) number of seconds an admin session lasts
                        between commands

    ***
    REMEMBER: this is not secure *in any way*! The configuration file is
    shared with all the plugins, it is stored in plain text, and anyone
    can use any nick on any irc server. Please do not put sensitive info in
    your bot, give your bot access to sensitive info, run unknown plugins
    without looking at the source, or use any of your personal passwords in
    your bot. You have been warned.
    ***

    Yaib supports two types of passwords out of the box, defaulting to the
    'simple' type. Each type has a different balance between security and
    convenience. See below for details.

    'stupid'
        This is the weakest type where anyone can log in using the
        admin_password. Your bot will eventually be compromised.

    'simple'
        This is the middle type. Any nick listed in the `admins` dict can log
        in to the bot using the password specified for their nick.

        Eg: 'admins': {'your_nick': 'your_password'}

        This gives each user a different password, but it must be set in the
        config file, which every plugin and admin can likely access it.
    """

    SUPPORTED_TYPES = ['stupid', 'simple', 'test']

    def __init__(self, configuration={}):
        """Initialize the module"""
        self._admin_enabled = False
        self._admin_type = None
        self._admin_password = None
        self._admin_timeout = 600
        self._admins = {}

        self._configure(configuration)
        pub.subscribe(self.onAdminCommand, 'core:adminCommand')

    def _configure(self, configuration):
        """Called on init with the bot configuration."""
        # require admin password
        if not configuration.admin:
            logging.warning(
                "Admin not configured - all admin functionality disabled."
            )
            return

        # require opt in to admin functionality
        if not configuration.admin.enabled:
            logging.warning("Admin disabled in configuration.")
            return

        self._admin_type = configuration.admin.admin_type
        if self._admin_type not in self.SUPPORTED_TYPES:
            logging.warning(
                "Admin configuration error - unsupported type %s" %
                self._admin_type
            )
            return

        if self._admin_type == 'stupid':
            self._admin_password = configuration.admin.admin_password
            if self._admin_password in ['', None]:
                logging.warning(
                    "Admin configuration error - admin password must be set"
                )
                return
            logging.info("Initialized admin system with master password.")

        elif self._admin_type == 'simple':
            if configuration.admin.admins is None:
                logging.warning(
                    "Admin configuration error - empty admins dict"
                )
                return

            admins = self._processSimpleAdmins(configuration.admin.admins)
            if admins is None:
                logging.warning(
                    "Admin configuration error - invalid admins dict"
                )
                return
            self._admins = admins
            logging.info(
                "Initialized admin system. Found %d admins" % len(self._admins)
            )
        elif self._admin_type == 'test':
            logging.warning("TEST ADMIN IS ON - ALL USERS ARE ADMINS")

        # if admin timeout is set, use it
        if configuration.admin.admin_timeout:
            self._admin_timeout = configuration.admin.admin_timeout

        logging.info("Admin configured")
        self._admin_enabled = True
        pub.sendMessage('admin:initialized')

    def _processSimpleAdmins(self, raw_admins):
        """Accepts the configuration of admins and validates it. Returns a
        correctly formatted dict of admins."""
        admins = {}
        if not raw_admins:
            return None

        for nick, password in raw_admins.iteritems():
            if password not in ['', None]:
                admins[nick] = {
                    '_password': password,
                    'user': None,
                    'expiration': 0
                }
        return admins

    def onAdminCommand(self, user, nick, channel, command, more):
        """Called when a user issues an admin command. Resets
        the expiration time for their admin session."""
        if nick in self._admins:
            self._admins[nick]['expiration'] = \
                time.time() + self._admin_timeout

    def isAdmin(self, user, nick):
        """Returns True if the user is currently in a valid admin session."""
        return (
            self._admin_enabled and
            (
                self._admin_type == 'test' or
                (
                    nick in self._admins.keys() and
                    self._admins[nick]['user'] == user and
                    self._admins[nick]['expiration'] > time.time()
                )
            )
        )

    def login(self, user, nick, more):
        if not self._admin_enabled:
            return False

        if self._admin_type == 'stupid':
            if more.strip() == self._admin_password:
                self._successfulLogin(user, nick)
                return True
        elif self._admin_type == 'simple':
            if (nick in self._admins and
                    more.strip() == self._admins[nick]['_password']):
                self._successfulLogin(user, nick)
                return True
        return False

    def logout(self, user, nick, more=None):
        return self.clearAdmin(nick)

    def _successfulLogin(self, user, nick):
        if nick not in self._admins:
            self._admins[nick] = {}
        self._admins[nick]['user'] = user
        self._admins[nick]['expiration'] = time.time() + self._admin_timeout

    def listAdmins(self):
        return [
            nick
            for nick, info in self._admins.iteritems()
            if info['expiration'] > time.time()
        ]

    def clearAdmin(self, nick):
        if nick in self._admins.keys():
            self._admins[nick]['user'] = None
            self._admins[nick]['expiration'] = 0
            return True
        return False

    def clearAdmins(self):
        [self.clearAdmin(nick) for nick in self._admins.keys()]

    def disable(self):
        self._admins = {}
        self._admin_enabled = False
