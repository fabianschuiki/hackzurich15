#!/usr/bin/env python2
from log import new_logger
import logging

logger = new_logger('tester',logging.DEBUG)

logger.debug("helpful trace")
logger.info("nice info")
logger.warning("don't worry, be happy")
logger.error("Truly sorry :(")
logger.critical("Terrible Failure :'(")
logger.fatal("FAIL xD")