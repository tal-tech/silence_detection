from src.silence_utils import *
from src.load_model import GFCC_Trainset, DataLoader, device
from src.post_process import post_process_func
from src.config import gfcc_cfg
import os


def get_frame_results(wav_segment_list, batch_size=15, max_sequence_length=30000, n_jobs=10, my_model=None):

    # print(121321)
    start_time = time.time()
    ####################################
    l = len(wav_segment_list)
    # print('这个音频的段数:', l)
    wav_segment = np.concatenate(wav_segment_list, axis=0)

    input_params = [wav_segment, gfcc_cfg, int(max_sequence_length * l), max_sequence_length]
    # print('输出特征时，单段最大长度:', max_sequence_length)

    feature_df_list_ori = convert_raw_feature(input_params)
    arr_60k_list = [feature_df_list_ori[1][i * max_sequence_length: (i + 1) * max_sequence_length] for i in range(l)] # 60k signal.
    feature_df_list = [feature_df_list_ori[0].iloc[i * max_sequence_length: (i + 1) * max_sequence_length] for i in range(l)] # features.

    del feature_df_list_ori
    del wav_segment
    # print('分段后的长度:', [i.shape for i in feature_df_list])
    # start_time_2 = time.time()

    # print(time.time() - start_time)
    gfcc_input_set = GFCC_Trainset(x_df_list=feature_df_list, max_sequence_length=max_sequence_length)
    valloader = DataLoader(gfcc_input_set, batch_size=batch_size, shuffle=False)
    valid_iter = valloader
    # logging.info('start predicting')

    prediction_each_batch = []

    for eval_x in valid_iter:
        # print('predict...')
        prediction = my_model(eval_x.float().to(device))
        prediction = prediction.cpu().detach().numpy()
        prediction_each_batch.append(prediction)
        # print(prediction.shape)

    prediction = np.concatenate(prediction_each_batch, axis=0)
    prediction = np.argmax(prediction, axis=2)

    del prediction_each_batch

    prediction_list = [prediction[i, :] for i in range(prediction.shape[0])]
    # print('预测时间', time.time() - start_time_2)

    return arr_60k_list, prediction_list
    # return [], []


def to_post_process(wav_segment_list, arr_60k_list, prediction_list, n_jobs=10):
    post_process_list = []
    # logging.info('start post process')

    for idx, _ in enumerate(wav_segment_list):
        post_process_list.append(post_process_func(arr_60k_list[idx], prediction_list[idx]))

    post_result_list = [i[0] for i in post_process_list]

    return post_result_list


# batch_size = 15
# 03:28:40,352 -- # 03:29:07,942
# 平均27/15秒 每10分钟.

