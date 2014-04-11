import logging

from settings import get_gae_debug

def get_log_level():
    isDebugEnabled =  get_gae_debug()

    if isDebugEnabled:
        return logging.DEBUG
    return logging.INFO

LOG_DEFAULT_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_LEVEL = get_log_level()

def configureLogger(location='imagina.imagina.root', level=LOG_LEVEL, format=LOG_DEFAULT_FORMAT):
    logger = logging.getLogger(location)
    logger.setLevel(level)
    #ch = logging.StreamHandler()
    #ch.setLevel(logging.DEBUG)
    #formatter = logging.Formatter(format)
    #ch.setFormatter(formatter)
    #logger.addHandler(ch)
    return logger
# cmplex example d = { 'clientip' : '192.168.0.1', 'user' : 'fbloggs' }
# a2.log(lvl, 'A message at %s level with %d %s', lvlname, 2, 'parameters')
# debug('Protocol problem: %s', 'connection reset', extra=d)