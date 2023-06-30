import os
import subprocess
from sleepy_dog.logger import g_logger
from sleepy_dog.exception import EvaEx, Const


def get_ffmpeg_type(file_path: str, arg: str) -> str or None:
    # 获得流媒体文件属性，出错返回None或者抛出错误
    # 需要系统安装ffmpeg
    ret = None
    if os.path.exists(file_path) is False:
        g_logger.error(f"get_media_duration error, file not exist!")
        raise EvaEx(Const.DOWNLOAD_ERR)

    try:
        command = "ffprobe -v error -show_entries format=%s -of default=noprint_wrappers=1:nokey=1 %s" % (arg, file_path)
        s = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        out, error = s.communicate()
        if out is None or out == '':
            return ret
        ret = str(out, 'utf-8').strip('\n')
    except Exception as e:
        g_logger.error(f"get media {arg} error: {e}, file_size :{os.path.getsize(file_path)}")
        raise EvaEx(Const.TYPE_ERR)
    return ret


def get_media_duration(file_path: str) -> float:
    try:
        return float(get_ffmpeg_type(file_path, 'duration'))
    except:
        raise EvaEx(Const.TYPE_ERR)


def get_media_type(file_path: str) -> str or None:
    return get_ffmpeg_type(file_path, 'format_name')


def is_video(file_path: str) -> bool:
    tmp = str(get_media_type(file_path)).lower()
    for item in ('mp4', '3gp', 'avi', 'm4v', 'mkv', 'mov', 'wmv', 'mpeg', 'webm', 'flv', 'asf'):
        if item in tmp:
            return True
    return False


def is_audio(file_path: str) -> bool:
    tmp = str(get_media_type(file_path)).lower()
    for item in ('midi', 'mp3', 'wav', 'm4a', 'amr', 'ogg', 'flac'):
        if item in tmp:
            return True
    return False


def is_media(file_path: str) -> bool:
    tmp = str(get_media_type(file_path)).lower()
    for item in ('midi', 'mp3', 'wav', 'm4a', 'amr', 'ogg', 'flac',
                 'mp4', '3gp', 'avi', 'm4v', 'mkv', 'mov', 'wmv', 'mpeg', 'webm', 'flv', 'asf'):
        if item in tmp:
            return True
    return False


def run_ffmpeg(src_file, dst_file, *args, **kwargs):
    tmp = []
    for k, v in kwargs.items():
        tmp.append(f"-{k} {v}")
    addition_cmd = f"{' '.join(args)} {' '.join(tmp)}"
    cmd = f"ffmpeg -y -i {src_file} {addition_cmd} {dst_file}"
    g_logger.debug(f"run ffmpeg {cmd}")
    s = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    out, error = s.communicate()
    return out, error
