#! /usr/bin/env python3
# -*- coding: UTF-8 -*-
import os
import socket
from sleepy_dog.logger import g_logger
from sleepy_dog.c_config import Config
import py_eureka_client.eureka_client as eureka_client
import signal
import time
from threading import Thread

SERVER_PORT = Config.PORT
HEART_BEAT_INTERVAL = 3
app_name = Config.EUREKA_APP_NAME
RETRY = True


def _eureka_register():
    try:
        if eureka_client.get_discovery_client() is not None:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        hostname = socket.gethostname()
        server_host = '-'.join(hostname.split('-')[:-2])
        g_logger.info("eureka get hostname: {}, server host: {}".format(hostname, server_host))
        instance_id = "{}:{}:{}".format(hostname, app_name.lower(), SERVER_PORT)
        eureka_client.init(eureka_server=Config.EUREKA_URL,
                           app_name=app_name,
                           instance_id=instance_id,
                           instance_port=SERVER_PORT,
                           instance_host=server_host,
                           renewal_interval_in_secs=HEART_BEAT_INTERVAL,
                           duration_in_secs=10,
                           # 调用其他服务时的高可用策略，可选，默认为随机
                           ha_strategy=eureka_client.HA_STRATEGY_RANDOM)
    except Exception as e:
        g_logger.error('Init eureka server wrong, the error message is {}, the EUREKA_SERVER is {}'.format(e, os.environ.get("EUREKA_URL")))


def eureka_stop(*args, **kargs):
    g_logger.info("eureka stop")
    eureka_client.stop()
    global RETRY
    RETRY = False


def eureka_register():
    def h():
        while RETRY:
            _eureka_register()
            time.sleep(HEART_BEAT_INTERVAL)

    t = Thread(target=h)
    t.start()
