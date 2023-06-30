import functools
import os
import shutil
import time
import uuid
from multiprocessing.pool import ThreadPool

from sleepy_dog.c_config import Config
from sleepy_dog.logger import g_logger
from sleepy_dog.utility import EvaEx, Const, http_download, traceback_info, \
    make_callback, try_post_json, err_code
from sleepy_dog.ffmpeg_util import run_ffmpeg, get_media_duration
from sleepy_dog.c_data_backflow import get_internal_url
from src.load_model import load_my_model
from src.long_wav_process import get_silence_from_file_list
from src.merge_result_utils import merge_result
from sleepy_dog.c_data_backflow import send_count


model = load_my_model()
tp = ThreadPool(1)


def run_in_pool(pool: ThreadPool):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = pool.apply_async(func, args=args)
            return result.get()
        return wrapper
    return decorator


class Pipeline:
    def __init__(self, input_dict):
        self.input_dict = input_dict
        self.output_dict = {}
        self.uid = input_dict['requestId']
        self.video_file = os.path.join(Config.TMP_FOLDER, self.uid)
        self.change_file = os.path.join(Config.TMP_FOLDER, uuid.uuid4().hex+'.wav')
        self.audio_file = []
        self.duration = 0

    def run(self):
        try:
            self._download()
            self._trans_format()
            self._ai()
            self._callback()
        except EvaEx as e:
            g_logger.error(f"{self.uid} - eva error: {e}")
            self._callback(e.msg)
        except Exception as e:
            g_logger.error(f"{self.uid} - unknown error: {traceback_info(e)}")
            self._callback(Const.INTERNAL_ERR)

    def _download(self):
        g_logger.debug(f"{self.uid} - download {self.input_dict['video_url']}, callback:{self.input_dict['callback']}")
        self.internal_url = get_internal_url(self.input_dict['video_url'], self.uid)
        if self.internal_url != self.input_dict['video_url']:
            self.input_dict['internal_url'] = self.internal_url
        http_download(self.internal_url, self.video_file, self.uid)
        if not os.path.exists(self.video_file):
            raise EvaEx(Const.DOWNLOAD_ERR)

    def _trans_format(self):
        run_ffmpeg(self.video_file, self.change_file, "-vn", ar=16000, ac=1, f='wav')
        if not os.path.exists(self.change_file) or not os.path.getsize(self.change_file):
            raise EvaEx(Const.TYPE_ERR)
        self.duration = int(get_media_duration(self.change_file))
        g_logger.debug(f'{self.uid} - duration: {self.duration}')
        for i in range(0, self.duration, Config.PIECE_LENGTH):
            end_time = min(i+Config.PIECE_LENGTH, self.duration)
            audio_name = os.path.join(Config.TMP_FOLDER, uuid.uuid4().hex+'.wav')
            run_ffmpeg(self.change_file, audio_name, "-vn", ar=16000, ac=1, f='wav', ss=i, to=end_time)
            self.audio_file.append(audio_name)
        self._remove_file()

    def _remove_file(self):
        if os.path.exists(self.video_file):
            os.remove(self.video_file)
        if os.path.exists(self.change_file):
            os.remove(self.change_file)

    @run_in_pool(tp)
    def _ai(self):
        g_logger.debug(f'{self.uid} - ai')
        try:
            arr = []
            for idx, item in enumerate(self.audio_file):
                g_logger.debug(f"{self.uid} - piece {idx} run")
                ret = get_silence_from_file_list(item, batch_size=15, max_sequence_length=24000,
                                                 my_model=model, output_mode='1s')
                arr.append(ret)
            self.output_dict = merge_result(arr, piece_default_length=Config.PIECE_LENGTH)
        except Exception as e:
            g_logger.error(f"{self.uid} - algorithm error: {traceback_info(e)}")
            raise EvaEx(Const.PROCESS_ERR)

    def _callback(self, status=Const.SUCCESS):
        g_logger.info(f"{self.uid} - callback:{status}")
        self._remove_file()
        for item in self.audio_file:
            if os.path.exists(item):
                os.remove(item)
        if status == Const.SUCCESS:
            ret_data = make_callback(Const.SUCCESS, self.uid, self.output_dict)
        else:
            ret_data = make_callback(status, self.uid)
        g_logger.debug(f"{self.uid} - return data: {ret_data}")
        ret = try_post_json(self.input_dict['callback'], ret_data, self.uid)
        if ret:
            g_logger.info("{} - callback return:{}".format(self.uid, ret))
        else:
            g_logger.error(f"alertcode:910010001, alerturl:{Config.APP_URL}, alertmsg:SilenceError 回调失败 id:{self.uid}"
                           f"url: {self.input_dict['callback']}")
        send_count(self.uid, int(self.duration), err_code[status][0])


if __name__ == '__main__':
    p = Pipeline({"requestId": "123", "callback": "http://39.105.66.41:8085/recv-json",
                  "video_url": "http://dadastatic.oss-cn-hangzhou.aliyuncs.com/20200704/30358992/30358992_s_s_1593839520000.aac?OSSAccessKeyId=LTAI4GCmpHgXXvKR7do24hFF&Expires=2468579075&Signature=8IA1mgnrdshGEJoDMWcRMoxETCw%3D"})
    print(p.run())
