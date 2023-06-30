import logging
from sleepy_dog.c_config import Config

g_logger = logging.getLogger(__name__)


def init_log():
    ch = logging.StreamHandler()
    # ch.setLevel(Config.LOG_LEVEL)
    formatter = logging.Formatter('%(asctime)s [%(thread)d] %(levelname)s %(name)s - %(message)s')
    ch.setFormatter(formatter)
    g_logger.setLevel(Config.LOG_LEVEL)
    g_logger.propagate = False
    g_logger.addHandler(ch)


init_log()

