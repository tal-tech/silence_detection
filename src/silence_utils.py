import librosa
import pandas as pd
# from spafe.utils import vis
import time
import numpy as np
import os
from tqdm import tqdm
import multiprocessing
# import logging
import copy
from spafe.features.gfcc import gfcc

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s'
# )

# print('包加载完成')


# def get_gfcc_feature_from_mat_by_time(t, gfcc_mat, feature_type_list=['average', 'min', 'max', 'std']):
#     # 输入时间t固定是0-60000内的一个点
#     # 输入的gfcc_mat是抽取的gfcc特征, 10分钟的一般长度在 299950-300050之间
#     # 输出长度是(gfcc_mat.shape[1] * #gfcc_mat,) 的array
#     # 默认是(80,)
#     # 当前10毫秒的summary
#
#     '''
#
#     这个函数很慢，要优化.
#     :param t:
#     :param gfcc_mat:
#     :param feature_type_list:
#     :return:
#     '''
#     feature_list = []
#
#     if t % 10000 == 0:
#         print(t)
#
#     this_gfcc_segment = gfcc_mat[t * 2: (t + 1) * 2, :]
#     if this_gfcc_segment.shape[0] == 2:
#         for f_type in feature_type_list:
#             feature_list.append(gfcc_process(this_gfcc_segment, f_type))
#     else:
#         this_gfcc_segment = np.zeros_like(gfcc_mat[0 * 2: (0 + 1) * 2, :])
#         for f_type in feature_type_list:
#             feature_list.append(gfcc_process(this_gfcc_segment, f_type))
#
#     return np.concatenate(feature_list)
#
#
# def gfcc_process(gfcc_segment, process_type):
#     '''
#     gfcc_segment: 2d array, gfccs[1] contains x components of gfcc.
#     process_type: average, min, max, std.
#     '''
#     if process_type == 'average':
#         return np.mean(gfcc_segment, axis=0)
#     elif process_type == 'min':
#         return np.min(gfcc_segment, axis=0)
#     elif process_type == 'max':
#         return np.max(gfcc_segment, axis=0)
#     elif process_type == 'std':
#         return np.std(gfcc_segment, axis=0)


def get_gfcc_from_wav(sig, fs, gfcc_cfg=None):
    # print(1)
    # gfcc_cfg = copy.deepcopy(gfcc_cfg)
    # print(sig.shape)
    # gfcc_cfg['sig'] = sig
    # print(gfcc_cfg['sig'])
    # gfcc_cfg['fs'] = fs
    gfccs = gfcc(sig=sig, fs=fs, **gfcc_cfg)
    # print(2)
    # print(gfccs.shape)
    return gfccs, os.getpid()


def convert_raw_feature(input_params):
    # sig, fs = librosa.load(wav_path, sr=16000)
    fs = 16000
    # print(fs)
    wav_segment, gfcc_cfg, total_max_sequence_length, max_sequence_length = input_params
    # print('整个音频原始大小:', wav_segment.shape)

    gfccs, pid = get_gfcc_from_wav(wav_segment, fs, gfcc_cfg)
    raw_sig_60k = get_feature_from_arr_by_time(wav_segment, max_sequence_length=total_max_sequence_length)
    # raw_sig_60k: len=240k
    gfcc_features_list = []
    # print('确认特征形状:', gfccs.shape)
    trial_mat_all = np.zeros((np.int(np.ceil(gfccs.shape[0]/max_sequence_length) * max_sequence_length), 13))
    trial_mat_all[:gfccs.shape[0], :] = gfccs
    gfccs = trial_mat_all
    trial_mat = gfccs.reshape(-1, 2, 13)

    gfcc_features_list = np.concatenate(
        [trial_mat.mean(axis=1), trial_mat.min(axis=1), trial_mat.max(axis=1), trial_mat.std(axis=1)], axis=1)

    gfcc_df = pd.DataFrame(gfcc_features_list)
    # print('gfcc 特征大小:', gfcc_df.shape)
    return gfcc_df, raw_sig_60k


def get_feature_from_arr_by_time(sig_arr, max_sequence_length=30000): # 24w
    # 输入原始信号
    # 输出分段max signal.
    # a = time.time()
    # print(sig_arr.shape)
    # print(max_sequence_length)
    feature_list = sig_arr.reshape(-1, 160).max(axis=1)
    # print('160特征耗时:', time.time() - a)
    return np.array(feature_list)
