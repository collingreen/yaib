"""
An IRC protocol for use with a twisted protocol factory.
Adds support for irc to Yaib.

Assumes several things about available functions on
the factory
"""

import time
import string

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from kitchen.text.converters import to_bytes

from pubsub import pub


def connectToServer(config, yaib):
    factory = IRCFactory(config.host, config.port, yaib)
    reactor.connectTCP(config.host, config.port, factory)
    return factory


def start():
    reactor.run()


class YaibTwistedIRCProtocol(irc.IRCClient):
    # http://twistedmatrix.com/documents/8.2.0/api/twisted.words.protocols.irc.IRCClient.html

    messages = []

    def sendMessage(self, channel, message):
        """
        Sends a message to the specified channel.
        Handles flood prevention automatically.
        """

        # check time of max_flood messages ago
        settings = self.factory.getSettings()
        max_flood = settings.get('connection.max_flood')
        flood_interval = settings.get('connection.flood_interval')
        flood_wait = settings.get('connection.flood_wait')

        if len(self.messages) >= max_flood:
            flood_time = self.messages[-1]

            # if we are flooded, queue this send
            if time.time() - flood_time < flood_interval:
                reactor.callLater(
                        flood_wait,
                        self.sendMessage,
                        *[channel, message]
                    )
                return False

        # add it to our messages log
        self.messages.insert(0, time.time())
        self.messages = self.messages[:max_flood]

        self.msg(to_bytes(channel), to_bytes(message))

    def describe(self, channel, action):
        irc.IRCClient.describe(self, to_bytes(channel), to_bytes(action))

    def setNick(self, nick):
        irc.IRCClient.setNick(self, to_bytes(nick))

    def quit(self):
        # stop the irc connection
        reactor.stop()

    def publish(self, eventName, *args, **kwargs):
        # kwargs['connection'] = self
        if hasattr(self.factory, 'publish'):
            self.factory.publish(eventName, *args, **kwargs)

    def keepAlive(self, *args):
        # get elapsed time since most recent message
        time_since_last_message = 1000000
        if len(self.messages) > 0:
            time_since_last_message = time.time() - self.messages[0]

        keep_alive = self.factory.yaib.settings.get(
                'connection.keepalive_delay'
            )
        delay = keep_alive

        # if we haven't sent a message recently, do it now
        if time_since_last_message >= keep_alive:
            self.ping(to_bytes(self.factory.host))
            self.messages.insert(0, time.time())

        # else, we HAVE sent a message, try again DELAY after last message sent
        else:
            delay -= time_since_last_message

        # schedule this again
        reactor.callLater(delay, self.keepAlive, [])

    def getNickFromUser(self, user):
        return user.split('!', 1)[0]

    def callLater(self, delay, func, *args, **kwargs):
        reactor.callLater(delay, func, *args, **kwargs)

    def join(self, channel, key=None):
        """
        Join a channel.

        @type channel: C{str}
        @param channel: The name of the channel to join. If it has no
            prefix, C{'#'} will to prepended to it.
        @type key: C{str}
        @param key: If specified, the key used to join the channel.
        """
        channel = to_bytes(channel)

        if channel[0] not in '&#!+':
            channel = '#' + channel
        if key:
            key = to_bytes(key)
            self.sendLine("JOIN %s %s" % (channel, key))
        else:
            self.sendLine("JOIN %s" % (channel,))

    def leave(self, channel, reason=None):
        """
        Leave a channel.

        @type channel: C{str}
        @param channel: The name of the channel to leave. If it has no
            prefix, C{'#'} will to prepended to it.
        @type reason: C{str}
        @param reason: If given, the reason for leaving.
        """
        channel = to_bytes(channel)
        reason = to_bytes(reason)
        if channel[0] not in '&#!+':
            channel = '#' + channel
        if reason:
            self.sendLine("PART %s :%s" % (channel, reason))
        else:
            self.sendLine("PART %s" % (channel,))

    def kick(self, channel, user, reason=None):
        """
        Attempt to kick a user from a channel.

        @type channel: C{str}
        @param channel: The name of the channel to kick the user from. If it
            has no prefix, C{'#'} will to prepended to it.
        @type user: C{str}
        @param user: The nick of the user to kick.
        @type reason: C{str}
        @param reason: If given, the reason for kicking the user.
        """
        channel = to_bytes(channel)
        if channel[0] not in '&#!+':
            channel = '#' + channel
        if reason:
            reason = to_bytes(reason)
            self.sendLine("KICK %s %s :%s" % (channel, user, reason))
        else:
            self.sendLine("KICK %s %s" % (channel, user))

    def signedOn(self):
        # reset factory delay
        self.factory.resetDelay()

        # notify yaib
        self.publish('connected', connection=self)

        # start keep-alive loop
        self.keepAlive()

    def receivedMOTD(self, motd):
        self.publish('messageOfTheDay', message=motd)

    def action(self, user, channel, action):
        self.publish(
                'userAction',
                user=user,
                nick=self.getNickFromUser(user),
                channel=channel,
                action=action
            )

    def noticed(self, user, channel, message):
        self.publish(
                'notification',
                user=user,
                nick=self.getNickFromUser(user),
                channel=channel,
                message=message
            )

    def privateMessage(self, user, nick, message):
        # notify yaib
        self.publish(
                'privateMessage',
                user=user,
                nick=nick,
                message=message
            )

    def directMessage(self, user, nick, channel, message):
        self.publish(
                'directMessage',
                user=user,
                nick=nick,
                channel=channel,
                message=message
            )

    def command(self, user, nick, channel, command, more):
        """Called when a user appears to issue a command."""
        self.publish(
                'command',
                user=user,
                nick=nick,
                channel=channel,
                command=command,
                more=more
            )

    def message(self, user, nick, channel, message, highlight=False):
        """Called with every normal message said in each channel to
        which yaib is connected (not actions, commands, or PMs)."""
        self.publish(
                'message',
                user=user,
                nick=nick,
                channel=channel,
                message=message,
                highlight=highlight
            )

    # all incoming text goes through this poorly named function
    def privmsg(self, user, channel, message):
        # convert text to unicode before anything else happens
        user = to_bytes(user)
        channel = to_bytes(channel)
        message = to_bytes(message)

        nick, x, nick_host = user.partition('!')

        # private message
        if channel == self.factory.yaib.nick:
            self.privateMessage(user, nick, message)

        # not private message
        else:

            # if message starts with bot name, call it a command
            if message.lower().startswith(self.nickname):
                self.directMessage(user, nick, channel, message)

            # if message starts with command prefix, call it a command
            elif message.startswith(self.factory.command_prefix):

                # remove leading command prefix
                message = message[len(self.factory.command_prefix):]

                # split it into command name and the arguments
                command, x, more = message.partition(' ')

                self.command(user, nick, channel, command, more)

            else:
                # just a regular message
                if message.find(self.factory.yaib.nick) >= 0:
                    self.message(user, nick, channel, message, True)
                else:
                    self.message(user, nick, channel, message, False)

    def joined(self, channel):
        self.publish('joined', channel=channel)

    def left(self, channel):
        self.publish('left', channel=channel)

    def kickedFrom(self, channel, kicker, kicker_user, message):
        self.publish('kicked',
                kicker_user=kicker_user,
                kicker=kicker,
                channel=channel,
                message=message
            )

    def userJoined(self, user, nick, channel):
        self.publish(
                'userJoined',
                user=user,
                nick=nick,
                channel=channel
            )

    # overwrite default irc_JOIN in order to send user
    def irc_JOIN(self, prefix, params):
        """
        Called when a user joins a channel.
        """
        user = prefix
        nick = self.getNickFromUser(user)
        channel = params[-1]
        if nick == self.nickname:
            self.joined(channel)
        else:
            self.userJoined(user, nick, channel)

    def userLeft(self, user, nick, channel):
        self.publish(
                'userLeft',
                user=user,
                nick=nick,
                channel=channel
            )

    # overwrite default irc_PART in order to send user
    def irc_PART(self, prefix, params):
        """
        Called when a user leaves a channel.
        """
        user = prefix
        nick = self.getNickFromUser(user)
        channel = params[0]
        if nick == self.nickname:
            self.left(channel)
        else:
            self.userLeft(user, nick, channel)

    def userQuit(self, user, nick, quitMessage):
        self.publish(
                'userQuit',
                user=user,
                nick=nick,
                quitMessage=quitMessage
            )

    def irc_QUIT(self, prefix, params):
        """
        Called when a user has quit.
        """
        user = prefix
        nick = self.getNickFromUser(user)
        self.userQuit(user, nick, params[0])

    def irc_KICK(self, prefix, params):
        """
        Called when a user is kicked from a channel.
        """
        kicker_user = prefix
        kicker = self.getNickFromUser(kicker_user)
        channel = params[0]
        kicked = params[1]
        message = params[-1]

        # overwrite message with blank if message is simply the kicker nick
        if message == kicker:
            message = ''

        if string.lower(kicked) == string.lower(self.nickname):
            self.kickedFrom(channel, kicker_user, kicker, message)
        else:
            self.userKicked(kicked, channel, kicker_user, kicker, message)

    def userKicked(self, kickee, channel, kicker_user, kicker, message):
        self.publish(
                'userKicked',
                kickee=kickee,
                channel=channel,
                kicker_user=kicker_user,
                kicker=kicker,
                message=message
            )

    def userRenamed(self, user, old_nick, new_nick):
        self.publish(
                'userRenamed',
                user=user,
                old_nick=old_nick,
                new_nick=new_nick
            )

    # overwrite default irc_NICK in order to send user
    def irc_NICK(self, prefix, params):
        """
        Called when a user changes their nickname.
        """
        user = prefix
        nick = self.getNickFromUser(user)
        if nick == self.nickname:
            self.nickChanged(params[0])
        else:
            self.userRenamed(user, nick, params[0])

    def getTopic(self, channel):
        return self.topic(channel)

    def setTopic(self, channel, topic):
        self.topic(channel, topic)

    def topicUpdated(self, user, channel, newTopic):
        nick = self.getNickFromUser(user)
        self.publish(
                'topicChanged',
                user=user,
                nick=nick,
                channel=channel,
                topic=newTopic
            )

    def irc_ERR_NOSUCHNICK(self, *args):
        pass

    def irc_RPL_NAMREPLY(self, server, info):
        my_name, channel_type, channel_name, user_list = info
        self.publish(
                'userList',
                channel_type=channel_type,
                channel=channel_name,
                user_list=user_list
            )

    def irc_RPL_ENDOFNAMES(self, *args):
        pass

    def irc_unknown(self, prefix, command, params):
        self.publish(
                'IRCUnknown',
                prefix=prefix,
                command=command,
                params=params
            )

    def ping(self, nick, answer_channel=None):
        self._ping_channel = answer_channel
        irc.IRCClient.ping(self, nick)

    def pong(self, user, seconds):
        nick = self.getNickFromUser(user)
        if self._ping_channel:
            self.publish(
                    'pong',
                    user=user,
                    nick=nick,
                    channel=self._ping_channel,
                    seconds=seconds
                )
            self._ping_channel = None


class IRCFactory(protocol.ReconnectingClientFactory):
    protocol = YaibTwistedIRCProtocol

    def __init__(self, host, port, yaib, *args, **kwargs):
        # protocol.ReconnectingClientFactory.__init__(self, *args, **kwargs)

        # store a reference to yaib and server info
        self.yaib = yaib
        self.host = host
        self.port = port

    @property
    def command_prefix(self):
        return self.yaib.command_prefix

    def getSettings(self):
        return self.yaib.settings.getMulti([
            'connection.max_flood',
            'connection.flood_interval',
            'connection.flood_wait'
        ])

    def publish(self, eventName, *args, **kwargs):
        pub.sendMessage('connection:%s' % eventName, **kwargs)
