import glob
import librosa
import numpy as np
from src.frame_results import get_frame_results, to_post_process
from src.batch_output_and_merge import get_batch_each_second_results, batch_get_stats_and_details, get_batch_60ms_results
# import logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s'
# )

MAX_BATCH_SIZE = 16
SAMPLE_RATE = 16000
import pickle
import time

# TODO: 解决音频过长的问题


def get_pieces_of_whole_class(whole_class_wav, unit_length=300):
    # 对一堂课进行音频切片,最后一片不是
    piece_len = unit_length * SAMPLE_RATE
    sr = SAMPLE_RATE
    # print(unit_length)

    file_len = whole_class_wav.shape[0] / SAMPLE_RATE  # 1824
    time_now = 0
    final_pieces = []
    while file_len > time_now:
        tmp_piece = whole_class_wav[sr * time_now: sr * (time_now + unit_length)]

        tmp_piece_padding = np.zeros((piece_len,))
        tmp_piece_padding[:tmp_piece.shape[0]] = tmp_piece

        stop_point = tmp_piece.shape[0] / SAMPLE_RATE
        final_pieces.append((tmp_piece_padding, stop_point))

        # print(whole_class_wav[sr * time_now: sr * (time_now + 600)].shape)
        time_now += unit_length
    return final_pieces
    # 如果有1824s, 则应当被切为4段.


def get_detailed_batch_results(pieces_in_one_batch, stop_point_one_batch, output_mode='1s', batch_size=15, max_sequence_length=30000, n_jobs=10, my_model=None, unit_length=700):

    # print('get frame results')
    arr_60k_list, prediction_list = get_frame_results(pieces_in_one_batch, batch_size=batch_size, max_sequence_length=max_sequence_length, n_jobs=n_jobs, my_model=my_model)
    # start_time = time.time()
    detailed_results = to_post_process(pieces_in_one_batch, arr_60k_list, prediction_list, n_jobs=n_jobs)
    # 对细粒度输出的结果做不同粗粒度的输出.
    if output_mode == '1s':
        batch_each_second_results = get_batch_each_second_results(detailed_results, stop_point_one_batch, unit_length=unit_length)
        final_batch_seconds_results = batch_get_stats_and_details(batch_each_second_results)
        # print('后处理时间:', time.time() - start_time)

        return final_batch_seconds_results

    elif output_mode == '60ms':
        batch_60ms_results = get_batch_60ms_results(detailed_results, stop_point_one_batch, unit_length=unit_length)
        final_batch_60ms_results = batch_get_stats_and_details(batch_60ms_results)
        # assert len(final_batch_60ms_results) == file_idx
        return final_batch_60ms_results


def get_silence_from_file_list(input_wav, batch_size=15, max_sequence_length=60000, my_model=None, output_mode='1s'):
    '''

    :param wav_list: 文件列表，文件会以10分钟切片为单位，按batch分批输入，输出为所有文件的结果.
    :param max_sequence_length: 默认每10ms一段，例如=60000 则是600s长度. 即unit_length=600
    :param n_jobs: 并行抽取特征的进程数, 按需求来.
    :return:
    '''
    unit_length = int(max_sequence_length/100)

    # 读课
    this_whole_class_wav, _ = librosa.load(input_wav, sr=SAMPLE_RATE)
    # print('音频原始大小', this_whole_class_wav.shape)
    # 抽取片段
    pieces_in_one_batch = get_pieces_of_whole_class(this_whole_class_wav, unit_length=unit_length)

    stop_point_one_batch = [i[1] for i in pieces_in_one_batch]
    pieces_in_one_batch = [i[0] for i in pieces_in_one_batch]

    # print('#' * 20, '开始进入detail处理')

    batch_results = get_detailed_batch_results(pieces_in_one_batch, stop_point_one_batch, output_mode=output_mode,
                                               batch_size=batch_size, max_sequence_length=max_sequence_length,
                                               my_model=my_model, unit_length=unit_length)

    batch_results = batch_results[0]
    # 格式转换
    formatted_results = {}
    formatted_results['silence_length'] = batch_results['silence_length']
    formatted_results['voice_length'] = batch_results['voice_length']
    formatted_results['noise_length'] = batch_results['noise_length']
    formatted_results['silence_rate'] = batch_results['silence_rate']
    formatted_results['voice_rate'] = batch_results['voice_rate']
    formatted_results['noise_rate'] = batch_results['noise_rate']
    formatted_results['details'] = []
    for r in batch_results['details']:
        formatted_results['details'].append({'piece_type': r['piece_type'], 'piece_length': r['piece_length'],
                                             'piece_start_time': r['piece_detail_range'][0],
                                             'piece_end_time': r['piece_detail_range'][1]
                                             })

    return formatted_results 


if __name__ == '__main__':

    # logging.info('logging task start')
    wav_dir = '/share/hy/godeye/dada_audio_wav/'
    wav_list = glob.glob(wav_dir + '*.wav')  # 实际的输入.
    result = get_silence_from_file_list(wav_list)

    # print(final_batch_60ms_results[-1])
    # logging.info('all finished')


# 1. continuous 完成.
# 2. while batch 拆开
# 3. 朝游给的音频.


