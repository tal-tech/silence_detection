#! /usr/bin/env python3
# -*- coding: UTF-8 -*-
import json
import traceback
import functools

import requests
from flask import Response

from sleepy_dog.logger import g_logger
from sleepy_dog.exception import err_code, Const, EvaEx


def make_response(msg, req_id, data=None):
    return Response(json.dumps({"msg": msg, "data": data, "code": err_code[msg][0],
                                "requestId": req_id}, ensure_ascii=False),
                    status=err_code[msg][1], content_type='application/json')


def make_callback(msg, req_id, data=None):
    return {"msg": msg, "data": data, "code": err_code[msg][0], "requestId": req_id}


def retry(try_times=3, redirect_exception=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*arg, **kwargs):
            for _ in range(try_times):
                try:
                    result = func(*arg, **kwargs)
                    return result
                except Exception as e:
                    g_logger.error("retry {}, {} error: {}".format(_, func, e))
                    if _+1 == try_times:
                        if redirect_exception:
                            raise redirect_exception()
                        else:
                            raise e
        return wrapper
    return decorator


def retry_not_raise(try_times=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*arg, **kwargs):
            for _ in range(try_times):
                try:
                    result = func(*arg, **kwargs)
                    return result
                except Exception as e:
                    g_logger.error("retry {}, {} error: {}".format(_, func, e))
        return wrapper
    return decorator


def traceback_info(e: Exception) -> bytes:
    return traceback.format_exception(type(e), e, e.__traceback__)


def try_post_json(url, js, idx=None) -> str or None:
    for _ in range(3):
        try:
            ret = requests.post(url, json=js, timeout=10)
            ret.raise_for_status()
            return ret.text
        except Exception as e:
            g_logger.error(f"{idx} - post json error: {url}, {e}")
    return None


def get_url_size(url, idx=None) -> int:
    for _ in range(3):
        try:
            ret = requests.head(url, timeout=10)
            return int(ret.headers['Content-Length'])
        except Exception as e:
            g_logger.error(f"{idx} - head url error:{e}")
    return 0


def http_download(url, file_path, uid=""):
    for _ in range(3):
        try:
            req = requests.get(url, stream=True, timeout=10)
            with open(file_path, 'wb') as f:
                for chunk in req.iter_content(chunk_size=200*1024):
                    f.write(chunk)
            return
        except Exception as e:
            g_logger.error(f"{uid} - download error: {e}")
    raise EvaEx(Const.DOWNLOAD_ERR)

