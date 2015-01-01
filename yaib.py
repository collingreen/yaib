#!/usr/bin/env python
"""
    YAIB - Yet Another IRC Bot
    https://github.com/collingreen/yaib

    Collin "Keeyai" Green - collingreen.com

    You can see the original yaib in #ludumdare on irc.afternet.org.

    The official yaib channel is #yaib on irc.afternet.org.

    Yaib is built using Twisted:
    http://twistedmatrix.com/documents/14.0.2/api/twisted.words.protocols.irc.IRCClient.html

"""

import sys, os, time, imp, json, logging
from pubsub import pub

from tools import util
from modules import settings, connections, persistence
from modules.admin.admin_manager import AdminManager

# add path to make importing plugins work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


# TODO: configure from command line or config.json
logging.basicConfig(level=logging.DEBUG)

class Yaib(object):
    def __init__(self, *args, **kwargs):

        # TODO: support multiple IRC connections at once
        self.channels = []
        self.plugins = []
        self.shutup_until = None

        self.DONT_NOTIFY_PLUGINS_FLAG = '**does_not_notify_plugins**'

        # load configuration
        configFile = 'config.json'
        try:
            f = open(configFile)
        except: # TODO: Catch the real exceptions here
            logging.error(
                "Could not open configuration file %s. Quitting." % configFile
            )
            sys.exit(1)

        try:
            self.config = util.dictToObject(json.loads(f.read()))
            logging.info("Loaded configuration from %s" % configFile)
        except ValueError, e:
            logging.error(
                "Could not load configuration file %s. Exiting. %s" %
                    (configFile, repr(e))
            )
            sys.exit(1)

        # load settings module based on configuration
        # TODO: move this config check to settings module itself
        if self.config.settings.module == 'json':
            self.settings = settings.json(self.config)
            self.settings.loadSettings()
        else:
            logging.error(
                "Unsupported settings module %s. Exiting." %
                    self.config.settings.module
                )
            sys.exit(1)

        # load admin module based on configuration
        self.adminManager = AdminManager(self.config)

        # subscribe to events
        self.subscribeToEvents()

        # ensure default settings are all available
        self.createDefaultSettings()

        # create persistence layer
        self.persistence = persistence.default(self.config)

        # load plugins
        self.loadPlugins()

    def subscribeToEvents(self):
        # subscribe to events from the default modules
        pub.subscribe(self.onSettingsUpdated, 'settings:updated')
        pub.subscribe(self.onSettingsUpdated, 'settings:loaded')

        # subscribe to events from the server connections
        pub.subscribe(self.onConnected, 'connection:connected')
        pub.subscribe(self.onMessageOfTheDay, 'connection:messageOfTheDay')
        pub.subscribe(self.onUserAction, 'connection:userAction')
        pub.subscribe(self.onNotification, 'connection:notification')
        pub.subscribe(self.onPrivateMessage, 'connection:privateMessage')
        pub.subscribe(self.onDirectMessage, 'connection:directMessage')
        pub.subscribe(self.onCommand, 'connection:command')
        pub.subscribe(self.onMessage, 'connection:message')

        pub.subscribe(self.onJoined, 'connection:joined')
        pub.subscribe(self.onLeave, 'connection:left')
        pub.subscribe(self.onKicked, 'connection:kicked')
        pub.subscribe(self.onTopicChanged, 'connection:topicChanged')
        pub.subscribe(self.onUserJoined, 'connection:userJoined')
        pub.subscribe(self.onUserLeft, 'connection:userLeft')
        pub.subscribe(self.onUserQuit, 'connection:userQuit')
        pub.subscribe(self.onUserKicked, 'connection:userKicked')
        pub.subscribe(self.onUserRenamed, 'connection:userRenamed')

        pub.subscribe(self.onUserList, 'connection:userList')
        pub.subscribe(self.onPong, 'connection:pong')
        pub.subscribe(self.onIRCUnknown, 'connection:IRCUnknown')

    def onSettingsUpdated(self):
        # set command prefix
        self.command_prefix = self.settings.get('connection.command_prefix')

    def start(self):
        """
        Called after initialization. Connects to the servers in the settings.
        """
        # create a connection
        connection = connections.irc
        self.connection_factory = connection.connectToServer(
                self.config.connection,
                self
            )
        connection.start()

    def createDefaultSettings(self):
        """Ensure the default settings exist from the config file."""
        # TODO: just load everything from config without explicitly listing
        default_channels = [c.strip() for c in
                self.config.default_channels.split(',')]
        self.settings.setMulti({
            'nick': self.config.nick,
            'default_channels': default_channels,

            'connection.command_prefix': self.config.connection.command_prefix,
            'connection.keepalive_delay': \
                    self.config.connection.keepalive_delay,
            'connection.max_flood': self.config.connection.max_flood,
            'connection.flood_interval': self.config.connection.flood_interval,
            'connection.flood_wait': self.config.connection.flood_wait,

            'shutup_duration': 30
            },
            initial=True
        )

    def loadPlugins(self):
        """
        Loads plugins from the plugins folder. Plugins
        should be in folders with the same name as their main
        script and expose a class Plugin that inherits from
        baseplugin. Example: plugins/baseplugin.py
        """

        logging.info("loading plugins")
        # load each plugin and put in self.plugins
        self.plugins = []
        for path in os.listdir(self.config.plugins.root):
            self.loadPlugin(path)

        # notify listeners that the plugins have finished loading
        pub.sendMessage('core:pluginsLoaded')
        self.callInPlugins('onPluginsLoaded')

    def loadPlugin(self, path):
        """Load a plugin from the given path"""
        logging.debug("looking for plugin in %s" % path)
        # if path is a folder
        if os.path.isdir(os.path.join(self.config.plugins.root, path)):

            # if found plugin in folder
            plugin_file_path = os.path.join(
                    self.config.plugins.root, path, "%s.py" % path
                )
            if os.path.isfile(plugin_file_path):
                try:
                    # try to import it
                    logging.debug("- importing plugin %s module" % path)
                    plugin_module = imp.load_source(
                        path,
                        plugin_file_path
                    )
                    logging.debug("Imported plugin module %s" % path)

                # TODO: change to only catch import errors here
                except Exception, e:
                    logging.error(
                        "Error importing plugin %s: %s" % (path, repr(e))
                    )
                    return False

                if hasattr(plugin_module, 'Plugin'):
                    try:
                        logging.debug("Creating plugin")
                        plugin = plugin_module.Plugin(
                                self,
                                self.config
                            )
                        logging.debug("Loaded plugin %s" % plugin.name)

                    # loading external code - catch all exceptions
                    except Exception, e:
                        logging.error("Error loading plugin %s: %s" % (
                            plugin_file_path, repr(e))
                        )
                        return False

                    # TODO: what does the comment below mean? does this work?
                    # this probably doesnt work singly bc it sticks the same
                    # plugin on the end of the list
                    for p in self.plugins:
                        if p.name == plugin.name:
                            self.plugins.remove(p)
                    self.plugins.append(plugin)
                    return True

        return False

    def getPluginSettings(self, pluginName):
        """Create a wrapper around the settings object that namespaces
        the getters and setters based on the plugin name."""
        yaibSettings = self.settings
        class SettingsWrapper(object):
            def getKey(self, key):
                return '%s.%s' % (pluginName, key)

            def set(self, key, *args, **kwargs):
                return yaibSettings.set(self.getKey(key), *args, **kwargs)

            def setMulti(self, settingsDict, initial=False):
                settingsDict = dict([
                    (self.getKey(k), v) for k,v in settingsDict.items()
                ])
                return yaibSettings.setMulti(settingsDict, initial=initial)

            def get(self, key, default=None):
                return yaibSettings.get(self.getKey(key), default=default)

            def getMulti(self, keys, default=None):
                keys = [self.getKey(k) for k in keys]
                return yaibSettings.getMulti(keys, default=default)
        return SettingsWrapper()

    def callInPlugins(self, command, *args, **kwargs):
        for p in self.plugins:
            if hasattr(p, command):
                try:
                    getattr(p, command)(*args, **kwargs)
                except Exception, e: # running plugin command - catch everything
                    logging.error("Exception running %s in plugin %s: %s" %
                            (command, p.name, repr(e))
                        )

    def formatDoc(self, message):
        """
        Formats the given message by replacing {nick} and {command_prefix}
        with their current values and stripping any control flags."""
        doc = message.replace(self.DONT_NOTIFY_PLUGINS_FLAG, '')
        return doc.format(
                nick=self.nick,
                command_prefix=self.command_prefix
            )

    def callLater(self, delay, func, *args, **kwargs):
        """Wait for the given delay then call the function with the args."""
        self.server_connection.callLater(delay, func, *args, **kwargs)

    # connection functionality
    def onConnected(self, connection):
        # save the active server connection
        # (refactor when supporting multiple servers)
        self.server_connection = connection

        # set nick
        self.setNick(self.settings.get('nick'))

        # join default channels
        default_channels = self.settings.get('default_channels')
        for channel in default_channels:
            self.server_connection.join(str(channel))

        # call in plugins
        self.callInPlugins('onConnected')

    def onMessageOfTheDay(self, message):
        self.callInPlugins('onMessageOfTheDay', message)

    def onNotification(self, user, nick, channel, message):
        self.callInPlugins('onNotification', user, nick, channel, message)

    def onUserAction(self, user, nick, channel, action):
        self.callInPlugins('onUserAction', user, nick, channel, action)

    def onPrivateMessage(self, user, nick, message):
        # split it
        command, x, more = message.lstrip(' ').partition(' ')

        # strip command prefix if there is one
        if command.startswith(self.command_prefix):
            command = command[len(self.command_prefix):]

        # try to call this like a command
        result = self.findAndCall(command, user, nick, self.nick, more)

        # didnt find command, pass on to plugins
        if result is None:
            self.callInPlugins('onPrivateMessage', user, nick, message)

    def onDirectMessage(self, user, nick, channel, message):
        # remove nick from front
        processed = message[len(self.nick):]
        processed = processed.lstrip(
                self.settings.get('nick_command_delimiters')
            )

        # split it into command name and the arguments
        command, x, more = processed.partition(' ')

        # check if first word is a command
        found = self.findAndCall(command, user, nick, channel, more)
        if not found:
            self.callInPlugins(
                'onMessage', user, nick, channel, message, highlight=True
            )

    def onMessage(self, user, nick, channel, message, highlight):
        self.callInPlugins('onMessage', user, nick, channel, message, highlight)

    def onCommand(self, user, nick, channel, command, more):
        found = self.findAndCall(command, user, nick, channel, more)
        if not found:
            self.callInPlugins(
                'onMessage', user, nick, channel, more, highlight=True
            )

    def findAndCall(self, command, user, nick, channel, more):
        """Searches for the specified command and calls it if possible. Returns
        False if didn't have permission, None if not found, True if found and
        executed. If multiple plugins provide the same command, whichever one
        is found first will be executed."""
        searchables = [self] + self.plugins
        for searchable in searchables:
            func, is_admin_command = \
                    self.findCommand(searchable, user, nick, channel, command)

            # found it, execute it
            if func:
                command_event_name = 'onCommand'
                func(user, nick, channel, more)

                # if admin command, publish and notify plugins
                if is_admin_command:
                    command_event_name = 'onAdminCommand'
                    pub.sendMessage(
                        'core:adminCommand',
                        user=user,
                        nick=nick,
                        channel=channel,
                        command=command,
                        more=more
                    )

                # special cases not to send to plugins
                if (not func.__doc__ or
                        self.DONT_NOTIFY_PLUGINS_FLAG not in func.__doc__):
                    self.callInPlugins(
                        command_event_name, user, nick, channel, command, more
                    )

                return True

        # never found it or didn't have permission, return None
        return None

    def findCommand(self, obj, user, nick, channel, command):

        # look for admin command if user is admin
        if self.isAdmin(user, nick):
            f = 'admin_%s' % command
            if hasattr(obj, f):
                return getattr(obj, f), True

        # look for op command if user is op
        if self.isOp(nick, channel):
            f = 'op_%s' % command
            if hasattr(obj, f):
                return getattr(obj, f), False

        # look for regular handler for this command - None otherwise
        func = getattr(obj, 'command_' + command, None)
        return func, False

    # TODO: implement this correctly
    def quit(self):
        # shutdown all the plugins
        self.callInPlugins('onShutdown')

        # shutdown all the modules
        pub.sendMessage('core:shutdown')

        # save settings
        self.settings.saveSettings()

        # TODO: support multiple connections
        self.server_connection.quit()

    def setNick(self, nick):
        old_nick = self.nick if hasattr(self, 'nick') else ''
        # TODO: support multiple connections
        if hasattr(self, 'server_connection'):
            self.server_connection.setNick(nick)
            self.nick = nick
            self.callInPlugins('onNickChange', nick, old_nick)

    def sendMessage(self, channel, message):
        """
        Sends a message to the specified channel on the current
        server connection.
        """
        # do nothing if in 'shutup' mode
        if self.shutup_until and time.time() < self.shutup_until:
            return False

        # TODO: support multiple connections
        self.server_connection.sendMessage(channel, message)

        # send to plugins
        self.callInPlugins('onSend', channel, message)

    def action(self, channel, action):
        """Sends an action in the specified channel (or nick!)."""
        self.server_connection.describe(channel, action)
        self.callInPlugins('onAction', channel, action)

    def isAdmin(self, user, nick):
        """Returns true if the user is currently an admin."""
        return self.adminManager.isAdmin(user, nick)

    def isOp(self, nick, channel):
        # TODO: implement this
        return False


## IRC Commands

    def onJoined(self, channel):
        logging.info("Joined %s" % channel)

        # add to list of channels
        self.channels.append(channel)

        # add to settings
        channels = self.settings.get('default_channels')
        if channel not in channels:
            channels.append(channel)
            self.settings.set('default_channels', channels)

        # notify plugins
        self.callInPlugins('onJoined', channel)

    def onLeave(self, channel):
        logging.info("Left %s" % channel)

        self.channels.remove(channel)
        # remove from settings
        channels = self.settings.get('default_channels')
        if channel in channels:
            channels.remove(channel)
            self.settings.set('default_channels', channels)

        # call in plugins
        self.callInPlugins('onLeave', channel)

    def onKicked(self, kicker_user, kicker, channel, message):
        """Called when kicked from a channel."""
        self.onLeave(channel)
        self.callInPlugins('onKicked', kicker_user, kicker, channel, message)

    def onTopicChanged(self, user, nick, channel, topic):
        self.callInPlugins('onTopicChanged', user, nick, channel, topic)

    def onUserJoined(self, user, nick, channel):
        """Called when another user joins the channel"""
        self.callInPlugins('onUserJoined', user, nick, channel)

    def onUserLeft(self, user, nick, channel):
        """Called when another user leaves the channel"""
        self.callInPlugins('onUserLeft', user, nick, channel)

    def onUserQuit(self, user, nick, quitMessage):
        """Called when another user disconnections from the server."""
        self.callInPlugins('onUserQuit', user, nick, quitMessage)

    def onUserKicked(self, kickee, channel, kicker_user, kicker, message):
        """Called when a user is kicked from the channel"""
        # TODO: onUserLeft expects user, nick channel
        # self.onUserLeft(kickee, channel)
        self.callInPlugins(
            'onUserKicked', kickee, channel, kicker_user, kicker, message
        )

    def onUserRenamed(self, user, old_nick, new_nick):
        """
        Called when another user changes their nick from old_nick to new_nick.
        NOTE: User is the old user string before the chaneg.
        """
        if old_nick != self.settings.get('nick'):
            self.callInPlugins('onUserRenamed', user, old_nick, new_nick)

    def onUserList(self, channel_type, channel, user_list):
        self.callInPlugins('onUserList', channel_type, channel, user_list)

    def onPong(self, user, nick, channel, seconds):
        self.sendMessage(
            channel,
            "%s pong! Round trip time: %.2f seconds" % (nick, seconds)
        )

    def onIRCUnknown(self, prefix, command, params):
        self.callInPlugins('irc_%s' % command, params)

if __name__ == '__main__':
    yaib = Yaib()
    yaib.start()

