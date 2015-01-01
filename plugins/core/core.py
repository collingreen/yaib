import time
import logging
from plugins.baseplugin import BasePlugin


class Plugin(BasePlugin):
    """
    Core plugin with base level yaib functionality.
    """
    name = 'CorePlugin'

    def createDefaultSettings(self):
        info = (
            "Hi, my name is {nick} and I'm an open source python irc bot. " +
            "Check out my source code at " +
            "https://github.com/collingreen/yaib! Try {command_prefix}help " +
            "for the commands I currently support."
        )
        self.settings.set('yaib_info', info, initial=True)

    def command_login(self, user, nick, channel, more):
        """
        Logs you in to {nick} as an admin.
        Usage: {command_prefix}login [password]
        **does_not_notify_plugins**
        """
        if self.yaib.adminManager.login(user, nick, more):
            self.send(nick, 'Logged you in!')
        else:
            self.send(nick, 'Failed to log you in')

    def admin_logout(self, user, nick, channel, more):
        """Logs you out of {nick}."""
        success = self.yaib.adminManager.logout(user, nick)
        if success:
            self.send(nick, 'You have been logged out')
        else:
            self.send(nick, 'Failed to log you out. Something is wrong.')

    # automatically log users out on various actions
    def onUserLeft(self, user, nick, channel):
        self.yaib.adminManager.clearAdmin(nick)

    def onUserQuit(self, user, nick, quitMessage):
        self.yaib.adminManager.clearAdmin(nick)

    def onUserKicked(self, kickee, channel, kicker_user, kicker, message):
        self.yaib.adminManager.clearAdmin(kickee)

    def onUserRenamed(self, user, old_nick, new_nick):
        self.yaib.adminManager.clearAdmin(old_nick)
        self.yaib.adminManager.clearAdmin(new_nick)

    # log everyone out if yaib leaves or gets kicked from a channel
    # def onJoined(self, channel):
    #     self.yaib.adminManager.clearAdmins()

    # def onLeft(self, channel):
    #     self.yaib.adminManager.clearAdmins()

    # def onKicked(self, channel):
    #     self.yaib.adminManager.clearAdmins()

    def admin_testadmin(self, user, nick, channel, more):
        self.send(nick, "yep, you are an admin")

    def admin_admins(self, user, nick, channel, more):
        """List the currently logged in admins."""
        self.send(nick, "Current Admins: %s" % (
            ', '.join(self.yaib.adminManager.listAdmins())
            )
        )

    def admin_clear_admins(self, user, nick, channel, more):
        """Clear all the current admin sessions."""
        self.yaib.adminManager.clearAdmins()
        self.send(nick, 'Cleared all existing admin sessions.')

    def admin_disable_admins(self, user, nick, channel, more):
        """Disables admins until next restart. Use in an emergency."""
        self.yaib.adminManager.disable()
        logger.warning("Admins disabled by %s in %s" % (nick, channel))
        self.send(nick, 'Disabled all admins. Notify the owner.')

    def admin_set_setting(self, user, nick, channel, more):
        split = more.split(' ')
        if len(split) < 2:
            return self.send(
                nick,
                self.formatDoc(
                   "Usage: {command_prefix}set_setting key value"
                )
            )
        self.yaib.settings.set(split[0], split[1], ' '.join(split[2:]))

    def admin_reload_settings(self, user, nick, channel, more):
        """Reloads {nick}'s settings"""
        self.yaib.settings.loadSettings()
        self.reply(channel, nick, 'Reloaded settings')

    def admin_save_settings(self, user, nick, channel, more):
        """Save {nick}'s settings"""
        self.yaib.settings.saveSettings()
        self.reply(channel, nick, 'Saved settings')

    def admin_reset_settings(self, user, nick, channel, more):
        """
        Called to wipe all local settings for a plugin and restore
        the defaults.
        """
        self.yaib.settings.set(more, {})
        self.reply(channel, nick, "reset settings starting at %s" % more)

    def admin_reload(self, user, nick, channel, more):
        """Reloads all the plugins, or one specified plugin"""
        if more != '':
            try:
                result = self.yaib.loadPlugin(more.strip())
                if result is True:
                    self.reply(channel, nick, "Reloaded plugin %s" % more)
                    return
            # loading external code - catching all exceptions is ok
            except Exception, e:
                self.reply(channel, nick, "Failed to reload plugin %s" % more)

        # if we didnt find the specified plugin, just reload them all
        self.yaib.loadPlugins()
        self.reply(channel, nick, "%d plugins reloaded" % len(self.yaib.plugins))

    def admin_do(self, user, nick, channel, more):
        """Makes {nick} do an action."""

        # if channel is our nick, this is a PM
        if channel == self.nick:
            channel, action = more.strip().split(' ', 1)

        # command in the channel
        else:
            action = more

        self.action(channel, action)

    def admin_quit(self, user, nick, channel, more):
        """Makes {nick} disconnect from the server"""
        self.yaib.quit()

    def admin_join(self, user, nick, channel, more):
        """Makes {nick} join a channel - Usage: {command_prefix}join channel"""
        # TODO: remove server_connection from core plugin
        self.yaib.server_connection.join(more)

    def admin_leave(self, user, nick, channel, more):
        """
        Makes {nick} leave a channel - Usage: {command_prefix}leave channel"""
        # TODO: remove server_connection from core plugin
        self.yaib.server_connection.leave(more or channel)

    def admin_nick(self, user, nick, channel, more):
        """Makes {nick} change nick - Usage: {command_prefix}nick new_nick"""
        self.yaib.setNick(more.strip())



    def admin_shutup(self, user, nick, channel, more):
        """
        Makes {nick} shut up for a while. Can
        pass a number of seconds to shutup to
        override the default.
        """
        target = channel if channel == self.nick else nick

        duration = None
        if more:
            try:
                duration = int(more)
            except ValueError, TypeError:
                pass
        return self._shutup(duration)

    def command_shutup(self, user, nick, channel, more):
        """Makes {nick} shut up for a while."""
        return self._shutup()

    def _shutup(self, duration=None):
        if duration is None:
            duration = self.yaib.settings.get('shutup_duration')
        self.yaib.shutup_until = time.time() + duration

    def command_plugins(self, user, nick, channel, more):
        """Lists the loaded plugins"""
        self.reply(channel, nick, ', '.join([p.name for p in self.yaib.plugins]))

    def command_info(self, user, nick, channel, more):
        """Get some basic info about {nick}."""
        self.reply(channel, nick, self.formatDoc(self.settings.get('yaib_info')))

    # TODO: make this less ugly
    def command_help(self, user, nick, channel, more):
        """Sends the {nick} command documentation to the user who calls it."""

        # if more == '', show main help menu
        if more == '':
            content = self.formatDoc(
                "The following help categories are available. " + \
                "Select a category with '{command_prefix}help category'.\n" + \
                "--------------------------------\n"
            )

            content += ', '.join(
                    [self.nick] + [p.name for p in self.yaib.plugins]
                )

            for line in content.split("\n"):
                self.send(nick, line)

        else:
            searchables = []
            if more in [self.nick, 'core']:
                # show all built in commands
                searchables = [self]
            else:
                # look for plugin and use that
                for plugin in self.yaib.plugins:
                    if more.find(plugin.name) >= 0:
                        searchables.append(plugin)

            if len(searchables) == 0:
                self.send(nick, "Could not find help category %s" % more)
                return

            content = self.formatDoc(
                "Commands can be issued with a '{command_prefix}' or by " +
                "starting with '{nick}'. Example: '{command_prefix}help' " +
                "or '{nick}: help'.\n" +
                "The following commands are available in the category '%s'\n"
                    % more
            )

            is_admin = self.yaib.isAdmin(user, nick)
            admin_commands, commands = [], []
            for searchable in searchables:
                for item in dir(searchable):
                    prop = getattr(searchable, item)
                    if callable(prop):
                        is_command = item.startswith('command_')
                        is_admin_command = item.startswith('admin_')

                        # if this is a command
                        if (is_command or (is_admin and is_admin_command)):
                            # if function has a doc string
                            if prop.__doc__:
                                doc = prop.__doc__

                                if is_command:
                                    commands.append((
                                        item[len('command_'):],
                                        self.yaib.formatDoc(doc)
                                    ))
                                else:
                                    admin_commands.append((
                                        item[len('admin_'):],
                                        self.yaib.formatDoc(doc)
                                    ))

            # list admin commands first
            for admin_command, doc in admin_commands:
                content += """- %s (Admin only): %s\n""" % (admin_command, doc)

            for command, doc in commands:
                content += """- %s: %s\n""" % (command, doc)

            for line in content.split("\n"):
                self.send(nick, line)

    def command_ping(self, user, nick, channel, more):
        """Starts a ping request against the user who calls it
        and responds with the round trip time."""
        # TODO: abstract this more - plugins shouldn't
        # need to know about the connection
        self.yaib.server_connection.ping(nick, channel)


    # TODO: move to op plugin?
    # TODO: verify permission
    def admin_topic(self, user, nick, channel, more):
        """
        Makes {nick} change the topic -
        Usage: {command_prefix}topic new topic text
        """
        # TODO: abstract this more - plugins shouldn't
        # need to know about the connection
        self.yaib.server_connection.topic(channel, more)

    # TODO: move to op plugin?
    # TODO: verify op/hop permission first
    # TODO: verify user is in the target channel
    def admin_kick(self, user, nick, channel, more):
        """
        Makes {nick} kick the target user.
        Usage: {command_prefix}kick user [reason]
        """

        params = more.split(' ') if more else []
        reason = ''
        # if channel is our nick, this is a PM
        if channel == self.nick:
            if len(params) < 2:
                return self.send(
                    nick,
                    self.formatDoc(
                        "Usage: {command_prefix}kick target channel [reason]"
                    )
                )
            target = params[0]
            channel = params[1]

            if len(params) > 2:
                reason = ' '.join(params[2:])
            self.send(nick, "kicking %s from %s" % (target, channel))

        # command in the channel
        else:
            if len(params) < 1:
                return self.send(
                        channel,
                        self.formatDoc(
                            "Usage: {command_prefix}kick target channel [reason]"
                        )
                    )
            target = params[0]
            if len(params) > 1:
                reason = ' '.join(params[1:])
            self.action(channel, "kicks %s %s" % (target, reason))

        # TODO: abstract this more - plugins shouldn't
        # need to know about the connection
        self.yaib.server_connection.kick(channel, target, reason)
