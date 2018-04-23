import logging
import logging.handlers

# Logging configuration
loggerFileName = '.jira.log'
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# Get logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Stream Handler
streamHand = logging.StreamHandler()
streamHand.setLevel(logging.INFO)
streamHand.setFormatter(formatter)
logger.addHandler(streamHand)

# File handler
fileHand = logging.handlers.RotatingFileHandler(loggerFileName, maxBytes=(10 * 1024 * 1024), backupCount=0)
fileHand.setLevel(logging.DEBUG)
fileHand.setFormatter(formatter)
logger.addHandler(fileHand)