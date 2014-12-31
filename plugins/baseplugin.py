class BasePlugin(object):
    """
    Extend this/copy its structure to create plugins. Your plugin
    class must be `Plugin` to be loaded. Can include commands (command_*),
    admin commands (admin_). Additionally, yaib will look functions for
    many of the connection events.

    Any commands with a docstring will be automatically added to the
    help command output, categorized by plugin name.

    Command docstrings can include {nick} and {command_prefix} which
    will automatically be replaced in the help text with the current
    values.
    """
    name = 'BasePlugin'

    def __init__(self, yaib, configuration):
        self.yaib = yaib

        # save a shortcut to just this plugin's settings
        self.settings = self.yaib.getPluginSettings(self.name)

        # configure the plugin
        self.configure(configuration)

        # create any default settings
        self.createDefaultSettings()

    @property
    def command_prefix(self):
        # this is a property so it stays updated, even if the setting changes
        return self.yaib.command_prefix

    @property
    def nick(self):
        return self.yaib.nick

    def configure(self, configuration):
        """
        Overwrite this to handle configuration.
        @param configuartion: (object) the entire yaib config file.
        """
        pass

    def createDefaultSettings(self):
        """
        Called during initialization.
        Use self.settings.setMulti({...}, initial=True)
        """
        pass

    def getDbSession(self):
        return self.yaib.persistence.getDbSession()

    def formatDoc(self, message):
        """Formats the given message with the {nick} and {command_prefix}."""
        return self.yaib.formatDoc(message)

    def callLater(self, delay, func, *args, **kwargs):
        """
        Wait for the delay (in seconds) then call the function with
        the given arguments."""
        return self.yaib.callLater(delay, func, *args, **kwargs)

    def onShutdown(self):
        """Called when yaib is shutting down. Clean anything
        up and save all the settings necessary."""
        pass

    def send(self, channel, message):
        """Send a message in the given channel."""
        return self.yaib.sendMessage(channel, message)

    def reply(self, channel, nick, message):
        """
        If the channel is the bot (ie, was a private message to the bot)
        sends a message back to the sender, otherwise sends to the channel.
        """
        return self.send(
                channel if channel != self.nick else nick,
                message
            )

    def action(self, channel, action):
        """Send an action in the given channel."""
        return self.yaib.action(channel, action)

    def onPluginsLoaded(self):
        """Called when ALL the plugins are loaded."""
        pass


    def onNickChange(self, nick, old_nick):
        """Called when {nick}'s nick changes."""
        pass

    def onConnected(self):
        """Called when connected to a server."""
        pass

    def onMessageOfTheDay(self, message):
        """Called with the server's message of the day."""
        pass

    def onNotification(self, user, nick, channel, message):
        """Called when noticed"""
        pass

    def onUserAction(self, user, nick, channel, action):
        """Called when a user performs an action."""
        pass

    def onPrivateMessage(self, user, nick, message):
        """Called when a user sends {nick} a private message"""
        pass

    def onMessage(self, user, nick, channel, message, highlight):
        """Called when something is said in a channel"""
        pass

    def onSend(self, channel, message):
        """Called when {nick} sends a message to a channel (can be PM)."""
        pass

    def onAction(self, channel, action):
        """Called when {nick} does an action in a channel"""
        pass

    def onCommand(self, user, nick, channel, command, more):
        """Called when {nick} runs a command on behalf of a user."""
        pass

    def onAdminCommand(self, user, nick, channel, command, more):
        """Called when {nick} runs an admin command on behalf of a user."""
        pass

    def onJoined(self, channel):
        """Called after joining a channel."""
        pass

    def onLeave(self, channel):
        """Called after leaving a channel."""
        pass

    def onKicked(self, kicker_user, kicker, channel, message):
        """Called when {nick} is kicked from a channel."""
        pass

    def onUserJoined(self, user, nick, channel):
        """Called when a user joins a channel."""
        pass

    def onUserLeave(self, user, nick, channel):
        """Called when a user leaves a channel."""
        pass

    def onUserQuit(self, user, nick, quitMessage):
        """Called when a user disconnects from the server."""
        pass

    def onUserKicked(self, kickee, channel, kicker_user, kicker, message):
        """Called when a user is kicked from a channel"""
        pass

    def onUserRenamed(self, user, old_nick, new_nick):
        """Called when a user changes their nick"""
        pass

    def onUserList(self, channel_type, channel_name, user_list):
        """
        Called when user_list is given for a channel (ie, upon joining the
        channel).
        NOTE: this is a list of nicks, not user strings.
        """
        pass
