#! /usr/bin/env python3
# -*- coding: UTF-8 -*-
import json
import time
import traceback
from queue import Queue
from threading import Thread

import requests
from kafka import KafkaProducer

from sleepy_dog.c_apollo import g_apollo
from sleepy_dog.c_config import Config
from sleepy_dog.logger import g_logger

tasks = Queue()


def send_data_flow(uid: str, arg: dict, response: dict, start_time: float):
    if Config.DEPLOY_ENV != 'local':
        # 数据回流示例
        tasks.put((uid, arg, response, start_time, time.time()))


def _send_mq(producer, kafka_topic, req_id, input_data, output_data, start_time, finish_time, apollo=g_apollo):
    try:
        r_time = time.mktime(time.strptime(input_data['timestamp'], "%Y-%m-%dT%H:%M:%S")) * 1000
        d = {
            "apiType": Config.API_TYPE,
            "bizType": Config.BIZ_TYPE,
            "requestId": req_id,
            "url": Config.APP_URL,
            "responseTime": int(finish_time * 1000),
            "sendTime": int(time.time() * 1000),
            "sourceInfos": [{
                "id": req_id,
                "sourceType": "String",
                "content": json.dumps(input_data, ensure_ascii=False),
            }],
            "sourceRemark": input_data,
            "data": output_data,
            "version": Config.VERSION,
            "code": output_data['code'],
            "msg": output_data['msg'],
            "errMsg": output_data['msg'],
            'errCode': output_data['code'],
            "requestTime": r_time,
            "appKey": input_data.get('appKey') or "123",
            'duration': int(finish_time * 1000) - int(start_time*1000)
        }
        msg = json.dumps(d, ensure_ascii=False)
        producer.send(kafka_topic, msg.encode('utf-8'))
    except Exception as e:
        g_logger.error("{} - data reflect back error:{}".format(req_id,
                                                                traceback.format_exception(type(e), e,
                                                                                           e.__traceback__)))


def send_mq(msgs: list):
    kafka_url = g_apollo.get_value(Config.APOLLO_KAFKA, namespace=Config.APOLLO_NAMESPACE)
    kafka_topic = g_apollo.get_value(Config.APOLLO_TOPIC, namespace=Config.APOLLO_NAMESPACE)
    mq_url = kafka_url.split(',')
    producer = KafkaProducer(bootstrap_servers=mq_url)
    for task in msgs:
        _send_mq(producer, kafka_topic, *task)
    producer.close()


def run_data_flow():
    while True:
        try:
            task = tasks.get()
            lst = [task]
            for _ in range(min(50, tasks.qsize())):
                lst.append(tasks.get())
            send_mq(lst)
        except Exception as e:
            g_logger.error(f"get dataflow error:{e}")


def send_count(req_id, duration, code):
    if not Config.COUNT_URL:
        g_logger.debug("no found count_url, return")
        return
    try:
        ret = requests.get(Config.COUNT_URL, params=dict(requestId=req_id, duration=duration,
                                                         code=code))
        g_logger.info("{} - return async time callback {}, {}".format(req_id, ret.status_code, ret.text))
    except Exception as e:
        g_logger.error("error to return callback:{}".format(e))


def get_internal_url(src_url, req_id, timeout=10):
    # 外网url转内网url
    if not Config.DATA_CHANGE_URL or src_url is None:
        return src_url
    d = {
        "urls": [src_url],
        "requestId": req_id,
        "sendTime": int(round(time.time() * 1000))
    }
    try:
        ret = requests.post(Config.DATA_CHANGE_URL, json=d, timeout=timeout)
        g_logger.debug("receive internal url:{}".format(ret.text))
        ret_json = ret.json()
        if ret_json['code'] == 2000000:
            dst_url = ret_json['resultBean'][0]['innerUrl']
        else:
            dst_url = src_url
    except Exception as e:
        g_logger.error("{} - error in change url:{}".format(req_id, e))
        dst_url = src_url
    return dst_url
