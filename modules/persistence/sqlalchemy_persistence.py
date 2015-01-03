from contextlib import contextmanager
from pubsub import pub

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr

# declarative base for sqlalchemy schema
Base = declarative_base()


class SqlAlchemyPersistence(object):
    """
    Default persistence module for YAIB.

    Uses sqlalchemy to expose schema creation and ORM
    (and eventually migrations) to plugins.

    Configuration:
        Requires a persistence.connection key in the configuration file
        which will be passed to the sqlalchemy create_engine function.
        http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#database-urls

    Usage:
        ```
        with persistence.getDbSession() as db_session:
            db_session.query(Thing).update({'x': 5})
        ```
    """

    def __init__(self, configuration):
        """Initialize the module"""
        self._configure(configuration)

        # set to true when persistence is set up
        # polite code should check if persistence.enabled is True before
        # trying to use sqlalchemy
        self.enabled = False

        # subscribe to events
        self.subscribeToEvents()

    def _configure(self, configuration):
        """Called on init with the bot configuration."""

        # require persistence and persistence.connection
        if (configuration.persistence is None or configuration.persistence.connection is None):
            logging.error(
                "Error - could not configure persistence layer."
            )
            return False

        # an Engine, which the Session will use for connection resources
        self.db_engine = create_engine(
                configuration.persistence.connection,
                echo=configuration.persistence.logging
            )

        # create a configured "Session" class
        self.session_class = sessionmaker(bind=self.db_engine)

        # set flag that persistence is active
        self.enabled = True

    def subscribeToEvents(self):
        pub.subscribe(self.pluginsLoaded, 'core:pluginsLoaded')

    def pluginsLoaded(self):
        """
        Called after everything has been initialized. Calls create_all on the
        base class metadata, creating any missing tables in the database.
        """
        Base.metadata.create_all(self.db_engine)

    @contextmanager
    def getDbSession(self):
        """Provide a transactional scope around a series of operations."""
        session = self.session_class()
        # give the new session to the caller
        try:
            yield session
            session.commit()
        # if any exceptions are raised, roll back the transaction and reraise
        except:
            session.rollback()
            raise
        # always close the sessions
        finally:
            session.close()


def getModelBase(prefix=''):
    """Returns a custom model base to use for sqlalchemy declarative model
    classes. Ensures the table has an integer primary key named 'id' and
    that the itablename is a lowercase version of the prefix class name to
    help prevent name collisions."""
    class CustomBase(object):
        id = Column(Integer, primary_key=True)
        @declared_attr
        def __tablename__(cls):
            return ('%s_%s' % (prefix, cls.__name__)).lower()
    return CustomBase
