# -*- coding: utf-8 -*-
from plugins.baseplugin import BasePlugin

class Plugin(BasePlugin):
    name = 'EchoPlugin'

    def command_unicode(self, user, nick, channel, more):
        self.reply(channel, nick, u'┠')

    def command_test_settings(self, user, nick, channel, more):
        self.settings.set('custom', 'woohooooo')

    def onShutdown(self):
        """Called when yaib is shutting down. Clean anything
        up and save all the settings necessary."""
        print "ECHO - on shutdown"


    def onPluginsLoaded(self):
        """Called when ALL the plugins are loaded."""
        print "ECHO - on plugins loaded"

    def onNickChange(self, nick, old_nick):
        """Called when yaib's nick changes."""
        print "ECHO - on nick change", nick, 'from', old_nick


    def onConnected(self):
        """Called when connected to a server."""
        print "ECHO - on connected"

    def onMessageOfTheDay(self, message):
        """Called with the server's message of the day."""
        print "ECHO - on MOTD", message

    def onNotification(self, user, nick, channel, message):
        """Called when noticed"""
        print "ECHO - on notification", user, nick, channel, message

    def onUserAction(self, user, nick, channel, action):
        """Called when a user performs an action."""
        print "ECHO - user action", user, nick, channel, action

    def onPrivateMessage(self, user, nick, message):
        """Called when a user sends yaib a private message"""
        print "ECHO - PM", user, nick, message

    def onMessage(self, user, nick, channel, message, highlight):
        """Called when something is said in a channel"""
        print "ECHO - message", user, nick, channel, message



    def onSend(self, channel, message):
        """Called when yaib sends a message to a channel (can be PM)."""
        print "ECHO - send", channel, message

    def onAction(self, channel, action):
        """Called when yaib does an action in a channel"""
        print "ECHO - action", channel, action

    def onCommand(self, user, nick, channel, command, more):
        """Called when {nick} runs a command on behalf of a user."""
        print "ECHO - onCommand", user, nick, channel, command, more

    def onAdminCommand(self, user, nick, channel, command, more):
        """Called when {nick} runs an admin command on behalf of a user."""
        print "ECHO - onAdminCommand", user, nick, channel, command, more

    def onJoined(self, channel):
        """Called after joining a channel."""
        print "ECHO - joined", channel

    def onLeave(self, channel):
        """Called after leaving a channel."""
        print "ECHO - left", channel

    def onKicked(self, kicker_user, kicker, channel, message):
        """Called when {nick} is kicked from a channel."""
        print "ECHO - kicked", kicker_user, kicker, channel, message

    def onUserJoined(self, user, nick, channel):
        """Called when a user joins a channel."""
        print "ECHO - user joined", user, nick, channel

    def onUserLeft(self, user, nick, channel):
        """Called when a user leaves a channel."""
        print "ECHO - user left", user, nick, channel

    def onUserQuit(self, user, nick, quitMessage):
        """Called when a user disconnects from the server."""
        print "ECHO - user quit", user, nick, quitMessage

    def onUserKicked(self, kickee, channel, kicker_user, kicker, message):
        """Called when a user is kicked from a channel"""
        print "ECHO - user kicked", kickee, channel, kicker_user, kicker, message

    def onUserRenamed(self, user, old_nick, new_nick):
        """Called when a user changes their nick"""
        print "ECHO - user renamed", user, old_nick, new_nick


    def onUserList(self, channel_type, channel_name, user_list):
        """
        Called when user_list is given for a channel
        (ie, upon joining the channel)
        """
        print "ECHO - userlist", channel_type, channel_name, user_list
