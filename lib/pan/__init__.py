__version__ = '0.2.0'

# Add additional debug levels for logging
import logging
DEBUG2 = 9
DEBUG3 = 8
logging.addLevelName(DEBUG2, "DEBUG2")
logging.addLevelName(DEBUG3, "DEBUG3")


def debug2(self, msg, *args, **kwargs):
    if self.isEnabledFor(DEBUG2):
        self._log(DEBUG2, msg, args, **kwargs)

logging.Logger.debug2 = debug2


def debug3(self, msg, *args, **kwargs):
    if self.isEnabledFor(DEBUG3):
        self._log(DEBUG3, msg, args, **kwargs)

logging.Logger.debug3 = debug3
