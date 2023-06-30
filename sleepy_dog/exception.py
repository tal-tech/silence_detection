import traceback


class EvaEx(Exception):
    def __init__(self, msg):
        self.msg = msg


def traceback_info(e: Exception):
    return traceback.format_exception(type(e), e, e.__traceback__)


class Const:
    SUCCESS = "success"
    MISSING = "parameter error"
    TYPE_ERR = 'file type error'
    FILE_LIMIT = 'file size limited'
    DOWNLOAD_ERR = 'download fail'
    VIDEO_LENGTH = 'file length limited'
    INTERNAL_ERR = 'internal error'
    PROCESS_ERR = 'process error'


err_code = {
    Const.SUCCESS: (20000, 200),
    Const.MISSING: (3003004000, 400),
    Const.TYPE_ERR: (3003004001, 400),
    Const.FILE_LIMIT: (3003004002, 400),
    Const.DOWNLOAD_ERR: (3003004003, 400),
    Const.VIDEO_LENGTH: (3003004004, 400),
    Const.INTERNAL_ERR: (3003005000, 500),
    Const.PROCESS_ERR: (3003005001, 500),
}
