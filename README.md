yaib
====

Yet Another IRC Bot --  Plugin-based IRC bot written in Python

Yaib is a python IRC bot that uses plugins to add any desired
functionality. Yaib runs anywhere python can run and just needs network access
to connect to the irc servers.

Please contribute to yaib by filing issues, contributing pull
requests, or creating new plugins!

You can chat about yaib in #yaib on irc.afternet.org.


## Quick Start
You must have python installed to run Yaib. You should also
have virtualenv (for any python project) or, if not, pip. You
will also need git to clone the repository.

clone this repository (you can also just download the master zip)
~~~
git clone git@github.com:collingreen/yaib
~~~

change to the yaib directory
~~~
`cd yaib`
~~~

(optional) create a virtualenvironment in the venv folder, then activate it
~~~
virtualenv venv
. venv/bin/activate
// (on windows venv\Scripts\activate.bat)
~~~

install the requirements
~~~
pip install -r requirements.txt --allow-external PyPubSub
~~~


Yaib ships with an example config file, but will not function until you
create a `config.json` file with your real configuration. In particular,
you will probably want to change the server Yaib connects to, her nick,
and the default channels to which she should connect.

~~~
cp config-example.json config.json
~~~
-- edit your config.json as necessary --

Now that Yaib is fully configured, you can start her up!
~~~
python yaib.py
~~~

If you are running Yaib on a server somewhere, you probably want to either
run her disconnected from your current shell (`python yaib.py &`), in the
background (usually ctrl-z, then `bg`), or in a separate `screen`. This will
let Yaib keep running while you do other things (just don't turn off the
server).


## Usage
Yaib ships with several plugins that provide many features out of the box. You
can learn more about plugins below, but to get started immediately, simply
join a channel where Yaib is running and type `!help` (assuming you haven't
changed your `command_prefix` in the configuration file).


## Help Wanted
- Tests! Yaib currently uses nosetest, but the test coverage is extremely
lacking.
- Plugin Test System - this almost certainly goes hand in hand with adding
tests in general, but Yaib greatly needs a way for plugin developers
to quick test their plugins.
- Documentation - Yaib can do a *lot* of things, but not all of them are well
documented for new users or developers. In particular:
  - plugin development
  - config.json fields
- More Plugins - Making new plugins and sharing them with the Yaib community!


## Configuration
The initial configuration for Yaib is provided in a `config.json` file in the
root directory of the project. This controls many of the default settings,
configures the various modules (persistence, settings, admin), and is passed to
all of the plugins upon initialization, meaning you can configure pretty much
anything you want by editing this one file.

Yaib ships with a default example config.json (but no *actual* config.json),
which you should use as a starting point for your own configuration.

The following is a non-exhaustive list of some of the configuration options.
Almost all of these will be immediately placed into the settings module and
will change as admins interact with the bot (for example, changing the nick).

~~~
connection.host - the target irc server host
connection.port - the target irc server port
connection.command_prefix - the initial character(s) that indicate a command
nick - this controls the initial nick for your bot
default_channels - a list of the initial channels for your bot to join
shutup_duration - the number of seconds to block communication after !shutup
plugins.root - the path to the plugins folder (default: 'plugins')
persistence.connection - the sqlalchemy db connection string
~~~

## Admin
The Yaib core includes a simple admin system to allow your users to log in
and administer the bot while it is running. Plugins can provide commands
exclusively for admins - see the plugins section below.

To Enable Admin Features, the configuration file must contain an
`admin` section which can include the following:
~~~
enabled (boolean, required) - defaults to False
admin_type (string, required) - 'stupid' or 'simple'
admin_password - (string) master password for 'stupid' type
admins (dict) - dict of admins in the form {'nick': 'password'} for
                'simple' type
admin_timeout - (int) number of seconds an admin session lasts
                between commands
~~~


REMEMBER: this is not secure *in any way*! The configuration file is
shared with all the plugins, it is stored in plain text, and anyone
can use any nick on any irc server. Please do not put sensitive info in
your bot, give your bot access to sensitive info, run unknown plugins
without looking at the source, or use any of your personal passwords in
your bot. You have been warned.

Yaib supports two types of passwords out of the box, defaulting to the
'simple' type. Each type has a different balance between security and
convenience. See below for details.

#### `stupid`
This is the weakest type where anyone can log in using the
`admin_password`. Your bot will eventually be compromised.

#### `simple`
This is the middle type. Any nick listed in the `admins` dict can log
in to the bot using the password specified for their nick.

Example:
`'admins': {'your_nick': 'your_password'}`

This gives each user a different password, but it must be set in the
config file, which every plugin and admin can likely access it.


## Settings
Yaib creates and stores data while going about her normal business, including
persisting changes made by admins (like joining new channels, for example). This
is all stored via the settings module, which defaults to simply writing a json
file in the same directory as yaib.py. This system is also extended for use
by the plugins - see the plugin section below.

Admins can change any setting while they are logged in using the `!set_setting`
command. Nested settings can be referenced using '.' as a delimeter.

Example:
`!set_setting connection.command_prefix @`

This will change the bot to listen for commands starting with the '@' character
instead of the '!'. This change will be persisted until it is changed again or
the settings file is destroyed.


## Persistence
Yaib can store large amounts of data, including complicated relational data,
by leveraging the SQLAlchemy ORM. This provides a database agnostic way to
store and share data with external tools (like log viewers, achievement
websites, or anything else). This system is also exposed to any plugins that
need to persist data - see the plugin section and the example plugin for more
details. Note, this is an advanced topic, so make sure you understand
relational databases, ORMs, and SQLAlchemy before trying to dive in.


## Plugins
Yaib uses a plugin system to add commands and functionality for users. Almost
all actions are available for plugins, and adding anything missing is fairly
trivial.

The goals of the plugin system are:
 - to greatly simplify adding chat functionality
 - to separate the development of chat functionality from the yaib core
 - to allow bot owners to pick and choose functionality they want for their bot
 - to allow many developers to effectively add to yaib without getting in each
   other's way
 - to separate the bot functionality from IRC in particular (so other
   connections can be created without breaking all functionality)


### Loading Plugins
Yaib loads plugins from the `plugins` folder relative to yaib.py
(configurable). Each plugin needs to be in its own folder and provide a python
file with the same folder name. Inside this file should be a `Plugin` class
that subclasses `BasePlugin` found in <yaibfolder>/plugins/baseplugin.py.
See the default plugins for examples.

When Yaib loads a plugin, it is given the entire server configuration file,
so you can add sections to your config that plugins can consume to change their
behavior.

Note, Yaib provides the ability to load/reload plugins on the fly without a
restart, so ensure your plugin can handle being loaded multiple times.


### Adding Functionality
Plugins add functionality to Yaib in two ways - by responding to events and by
providing new commands. Both are accomplished by providing specially named
functions on the plugin class that correspond to the desired event or to the
new command being added.

This system allows for a wide range of new functionality - in fact, this is
how Yaib implements her own default chat interactions.


#### New Commands
New commands come in two forms - admin commands and normal commands. To create
a command that anyone can call, simply name your method in the form:
`command_your_command`. Yaib will automatically make this command available
to all users via the command prefix (default !) or by starting with the current
nick. For example, a method named `command_your_command` will be callable from
chat by saying `!your_command` or `yaib: your_command` (or whatever your bot
is named). To make a command visible only to admins, name your method starting
with `admin_` instead of `command_`. Note, you *can* create two versions of each
command - if a user is logged in as an admin they will call the admin version,
everyone else will call the standard version (this is how the `shutup` command
allows anyone to squelch the bot for a fixed amount of time but allows admins
to specify the shutup duration).


#### !Help
Yaib ships with a !help command that automatically generates the help content
based on the currently available plugins and the commands they provide. Any
command method in your plugins that includes a standard python docstring will
be automatically added to the help system. Additionally, to make your plugin
help strings more portable, you can use `{nick}` and `{command_prefix}`
in the text and Yaib will automatically replace them with the current nick
and the current command prefix, ensuring your plugin help string is always
accurate.


### Saving Plugin Data
Plugins can store data in two ways, depending on how the data is expected to
be used.

First, all plugins have access to their own namespaced section of
Yaib's `settings` module, allowing them to `set` and `get` any data they
need and ensure it is persisted between sessions. Settings should be used
for small amounts of information created by and consumed only by the plugin
(the settings for Yaib are handled by a service that could change how settings
 are stored at any time, so plugins should not make any assumptions about their
 settings apart from the `get`, `getMulti`, `set`, and `setMulti` apis.

For storing large amount of data or for exposing the data to external sources,
plugins should use the persistence layer provided by SQLAlchemy. See the
persistence section above and look at the example plugin for details
about how to correctly use SQLAlchemy to store relational data in a database
agnostic way.


### Plugin Examples
The best place to start when learning about Yaib plugins is the plugins
themselves. Yaib ships with a BasePlugin class that all plugins should
inherit from that stubs out all of the events Yaib can possibly send to
the plugins. There is also an ExamplePlugin that demonstrates some more
advanced plugin features like using the persistence module to store data
in a relational database.


### Publishing Plugins
If you have a plugin for yaib, feel free to add it to the wiki or email me if
you want it to become an official Yaib plugin.


### WARNING
BE CAREFUL WITH THIRD PARTY PLUGINS!
You should read *all* the code in any plugin you run - there is
absolutely no containment of what plugins can do; it would be
trivial to destroy all your data or attack your machine directly.
*You have been warned*.


## STRUCTURE
Yaib is broken into three distinct parts - yaib itself, modules, and
plugins. Each one provides a different set of functionality that, together,
makes up the entire yaib system.

#### Yaib
Yaib acts as the manager that glues all of the modules together, imports all the
plugins, and sets up both the plugin callbacks and the plugin commands.

#### Modules
Modules are non-optional services that encapsulate a set of core yaib
functionality like settings, persistence, admin management, and the underlying
server connection. Modules communicate with Yaib via pubsub and can be swapped
out for different implementations without changing Yaib or the plugins. For
example, the default settings module saves all the settings in a local file as a
JSON encoded string. Yaib uses the settings interface (and exposes it to the
plugins), but switching out the settings module for a different implementation
would allow the settings to exist in a database or online storage or anything
else without breaking anything. Both Yaib and the plugins can be completely
ignorant of the actual module implementation, making all of the code easier to
work on and reason about.

#### Plugins
Plugins, on the other hand, are completely optional extras (except core) that
add new functionality by adding callbacks for various events and by adding
commands for users and admins. Yaib manages loading all of the plugins, parsing
all of their commands, hooking up the correct callbacks, and exposing the
module interfaces as necessary (like settings and persistence).

Plugins enable a bot owner to pick and choose specific functionality
for their bot and make it extremely easy for developers to create chunks of
functionality without having to worry about anything else, letting Yaib handle
how connections work, how information gets stored, what makes an 'admin',
orchestrating the callbacks, and automatically building the help content for all
the commands, organized by plugins.

Check out the section on plugin development and the example plugins for more
information.

