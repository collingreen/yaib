from base_settings import BaseSettings
import os
import json
import logging


class JsonSettings(BaseSettings):
    """
    A simple settings module that saves all settings
    in a local json formatted file.

    TODO: needs tests
    - no settings
    - no permission
    - non-serializeable settings
    - cannot store settings, try a local file?
    - invalid settings, dont overwrite
    """

    settings_file = None

    def _configure(self, configuration):
        super(JsonSettings, self)._configure(configuration)

        settings_file = 'settings.json'
        if (hasattr(configuration, 'settings_file') and
                configuration.settings_file):
            settings_file = configuration.settings_file
            logging.info(
                "Using settings file from config: %s" % settings_file
            )

        # check if file exists
        if not os.path.exists(settings_file):
            logging.error(
                "Could not find settings file %s. Creating it." % settings_file
            )

        self.settings_file = settings_file

    def saveSettings(self):
        logging.debug("Saving settings")
        # TODO: catch and handle all the many possible errors here
        try:
            with open(self.settings_file, 'wb') as f:
                f.write(json.dumps(self._settings))
            return True
        except Exception, e:
            logging.error("Exception while saving settings: %s" % repr(e))

        super(JsonSettings, self).saveSettings()

    def loadSettings(self):
        # TODO: catch and handle all the many possible errors here

        success = False
        try:
            with open(self.settings_file, 'rb') as f:
                self._settings = json.loads(f.read())
            success = True
        except IOError:
            # TODO
            pass
        except ValueError, TypeError:
            logging.error("Invalid settings file. Starting a new one.")
            # TODO: create duplicate of old settings before using new
        except Exception, e:
            logging.error(
                "Unknown error while loading settings file: %s" % repr(e)
                )
            # TODO: create duplicate of old settings before using new

        super(JsonSettings, self).loadSettings()
        return success

