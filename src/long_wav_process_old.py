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


# TODO: 解决音频过长的问题


def get_pieces_of_whole_class(whole_class_wav, unit_length=300):
    # 对一堂课进行音频切片,最后一片不是
    piece_len = unit_length * SAMPLE_RATE
    sr = SAMPLE_RATE
    print(unit_length)

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


def get_detailed_batch_results(pieces_in_one_batch, stop_point_one_batch, output_mode='1s', batch_size=15, max_sequence_length=30000, n_jobs=10, my_model=None):
    # print(len(pieces_in_one_batch))
    # print(stop_point_one_batch) # 有这个就行，后面不管出什么结果，都可以和这个每一条的位置对齐.
    arr_60k_list, prediction_list = get_frame_results(pieces_in_one_batch, batch_size=batch_size, max_sequence_length=max_sequence_length, n_jobs=n_jobs, my_model=my_model)
    # detailed_results = to_post_process(pieces_in_one_batch, arr_60k_list, prediction_list, n_jobs=n_jobs)
    # import pickle

    # with open('detailed_results_3_class_thres_3.pkl', 'wb') as f:
    #     pickle.dump(detailed_results, f)

    # 对细粒度输出的结果做不同粗粒度的输出.
    if output_mode == '1s':
        batch_each_second_results = get_batch_each_second_results(detailed_results, stop_point_one_batch)
        final_batch_seconds_results = batch_get_stats_and_details(batch_each_second_results)
        # print(final_batch_seconds_results) # 秒级的结果
        # assert len(final_batch_seconds_results) == file_idx
        return final_batch_seconds_results

    elif output_mode == '60ms':
        batch_60ms_results = get_batch_60ms_results(detailed_results, stop_point_one_batch)
        final_batch_60ms_results = batch_get_stats_and_details(batch_60ms_results)
        # assert len(final_batch_60ms_results) == file_idx
        return final_batch_60ms_results


def get_silence_from_file_list(wav_list, batch_size=15, max_sequence_length=30000, n_jobs=10, my_model=None):
    '''

    :param wav_list: 文件列表，文件会以10分钟切片为单位，按batch分批输入，输出为所有文件的结果.
    :param max_sequence_length: 默认每10ms一段，例如=30000 则是300s长度. 即unit_length=300
    :param n_jobs: 并行抽取特征的进程数, 按需求来.
    :return:
    '''
    unit_length = int(max_sequence_length/100)
    # print(unit_length)
    # 读取一共处理多少文件.
    total_files = len(wav_list)
    # 从0开始处理
    file_idx = 0
    # 记录最终结果
    all_wav_results = []
    # 记录上一个batch处理到第几个文件了.
    last_batch_file_index = 0
    # 记录batch到第几个了.
    batch_num = 0
    # 开始处理
    while file_idx < total_files:
        # 存储一个batch的音频片段，取决于MAX_BATCH_SIZE
        pieces_in_one_batch = []
        pieces_batch_total = 0
        # logging.info('start a new batch {}'.format(batch_num))

        while file_idx < total_files:
            # 读一堂课
            this_whole_class_wav, _ = librosa.load(wav_list[file_idx], sr=SAMPLE_RATE)
            file_len = this_whole_class_wav.shape[0] / SAMPLE_RATE  # 1800s左右.

            # 这堂课将有多少片段.
            num_pieces_this_class = np.ceil(file_len / unit_length).astype(np.int)
            # print(num_pieces_this_class)
            # 片段数量加进去.
            pieces_batch_total += num_pieces_this_class
            if pieces_batch_total > batch_size: # 只跑一次预测.
                print(file_idx, last_batch_file_index) # file_idx应该等于已经处理过的音频数量.

                break
            pieces_of_this_class = get_pieces_of_whole_class(this_whole_class_wav, unit_length=unit_length)
            pieces_in_one_batch.extend(pieces_of_this_class)
            file_idx += 1

        stop_point_one_batch = [i[1] for i in pieces_in_one_batch]
        pieces_in_one_batch = [i[0] for i in pieces_in_one_batch]

        # print(pieces_in_one_batch)
        print('#' * 30)
        # print(len(pieces_in_one_batch))

        batch_results = get_detailed_batch_results(pieces_in_one_batch, stop_point_one_batch, output_mode='11s', batch_size=batch_size, max_sequence_length=max_sequence_length, n_jobs=n_jobs, my_model=my_model)
        # batch_num += 1
        # # all_wav_results.extend(batch_results)
        # del pieces_of_this_class
        # del pieces_in_one_batch
        #
        # # 每个加上名字.
        # for idx, this_w in enumerate(wav_list[last_batch_file_index: file_idx]):
        #     try:
        #         batch_results[idx]['filename'] = this_w
        #     except:
        #         batch_results[idx]['filename'] = 'error'
        # # with open('/workspace/projects_2020/godeye/silence/dada_test_data/{}.pkl'.format(wav_list[file_idx - 1].split('/')[-1]), 'wb') as f:
        # #     pickle.dump(batch_results, f)
        # last_batch_file_index = file_idx
    return all_wav_results


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


