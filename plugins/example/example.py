"""
Example plugin with a few simple features to demonstrate how Yaib
plugins work.

Includes custom settings and using the persistence layer via sqlalchemy.
"""

from plugins.baseplugin import BasePlugin

# import models for this plugin - import from top
from plugins.example.models import ExampleThing


class Plugin(BasePlugin):
    """This is an example plugin."""
    name = 'ExamplePlugin'

    def command_plugintest(self, user, nick, channel, rest):
        """
        A one line docstring that will automatically be added to the help
        contents for this plugin. Try `{command_prefix}help example` and look
        for plugintest.
        """
        self.send(channel, "This came from a plugin!")

    def admin_pluginadmintest(self, user, nick, channel, rest):
        """
        This text appears under this plugin's help menu, but only if
        you are logged in as an admin
        """
        self.send(channel, "Admin plugin commands too!")

    def command_dbtest(self, user, nick, channel, rest):
        """
        Demonstrates how to correctly use the sqlalchemy db session from the
        persistence module. Every time this function is called, this creates a
        new row in the ExampleThing table.
        """
        with self.getDbSession() as db_session:
            contrived_example = ExampleThing(
                    name='hello world',
                    count=99
                )
            db_session.add(contrived_example)

    def command_whois(self, user, nick, channel, rest):
        """
        Calls the whois command. Unstable usage - depends on IRC and goes
        beyond existing api. This is an example of a fairly elaborate,
        stateful command.
        """
        if not rest:
            self.send(channel, '%s: who is who?' % nick)
            return False

        try: target_nick = rest.split(' ')[0]
        except: target_nick = rest

        self.whois_channel= channel
        self.whois_result = {'nick': target_nick}
        self.yaib.server_connection.whois(target_nick)

    def irc_RPL_WHOISUSER(self, *args):
        """Can listen for unhandled connection events by name."""
        #print "WHOIS USER", args
        self.whois_result['user'] = '%s <%s@%s> "%s"' % (
            args[0][1], args[0][2], args[0][3], args[0][5]
        )

    def irc_RPL_WHOISSERVER(self, *args):
        #print 'WHOIS SERVER: ', args
        pass

    def irc_RPL_WHOISCHANNELS(self, *args):
        #print "WHOIS CHANNELS", args
        channels = args[0][2].strip().split(' ')
        self.whois_result['channels'] = channels

    def irc_RPL_WHOISIDLE(self, *args):
        #print "WHOIS IDLE", args
        pass

    def irc_RPL_ENDOFWHOIS(self, *args):
        #print 'END OF WHOIS'
        self.send(self.whois_channel, self.whois_result['user'])
        self.send(
            self.whois_channel,
            "Member of " + ', '.join(self.whois_result['channels'])
        )

    def command_echo_wait(self, user, nick, channel, more):
        """Echos the message passed (and appends 'woohoo') after a 2 second
        delay. Demonstrates scheduling future commands."""
        self.send(channel, "waiting...")
        self.callLater(2, self.sendAfterWait, channel, more, other='woohoo')

    def sendAfterWait(self, channel, message, notused=None, other=''):
        """echo_wait command calls this after a delay"""
        self.send(channel, message + ' ' + other)

