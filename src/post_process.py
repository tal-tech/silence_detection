# from sklearn.metrics import classification_report
# import pandas as pd
# import glob
import numpy as np
# import librosa
import os
# M_THRES_UPPER = 0
# STD_THRES_UPPER = 0.5
# STD_THRES_LOWER = 0.05
# FRAME_THRES_LOWER = 30
M_THRES_UPPER = -0.1
STD_THRES_UPPER = 0.5
STD_THRES_LOWER = 0.15
FRAME_THRES_LOWER = 28


def rule_based_post_process(this_piece, signal_60k):
    # 判定一个片段是否需要做后处理
    # this_piece: 当前噪声的一些信息. 主要用的是piece_detail_range 字段
    # signal_60k: x(处理后)
    '''
    {'piece_id': 1,
     'piece_type_en': 'silence',
     'piece_type': 0,
     'piece_detail_range': [60, 89],
     'piece_length': 29
     }

    '''
    # return: to_change: True: 变成2. False: 继续0
    this_m, this_std = np.mean(
        signal_60k[this_piece['piece_detail_range'][0]: this_piece['piece_detail_range'][1]]
    ), np.std(
        signal_60k[this_piece['piece_detail_range'][0]: this_piece['piece_detail_range'][1]]
    )
    this_frame_num = this_piece['piece_length']

    # print(this_m, this_std, this_frame_num)
    if (this_m < M_THRES_UPPER) and (this_std > STD_THRES_LOWER) and (this_std < STD_THRES_UPPER) and (
            this_frame_num > FRAME_THRES_LOWER):
        return True
    return False


def get_piece_json(y_array):
    type_map = {
        1: 'voice',
        0: 'silence',
        2: 'noise',
    }

    json_list = []
    start_index = 0
    end_index = 1  # 不包含自己。1 ~ 60000（根据实际情况而定）

    piece_num = 0

    y_array = np.array(y_array.tolist() + [-1])

    for i in range(len(y_array) - 1):
        # i 最大是59998
        if y_array[i] == y_array[i + 1]:
            end_index += 1
        else:
            json_list.append({
                'piece_id': piece_num,
                'piece_type_en': type_map[y_array[i]],
                'piece_type': int(y_array[i]),
                'piece_detail_range': [start_index, end_index],
                'piece_length': end_index - start_index,
            })
            piece_num += 1
            # 准备下一段
            start_index = i + 1
            end_index = i + 2
    return json_list


def get_60k_after_change(original_label_y, piece_json_this_class):
    # original_label_y: 原本的y_label_list. 也就是this_file_y_label
    output_label_y = original_label_y.copy()
    for this_piece in piece_json_this_class:
        output_label_y[this_piece['piece_detail_range'][0]: this_piece['piece_detail_range'][1]] = this_piece['piece_type']
    return output_label_y


def post_process_func(signal_60k, this_file_y_label):
    '''

    :param signal_60k: 60k长度的片段
    :param this_file_y_label: 模型预测值
    :return: y_label_after_change: 输出最终结果.
    '''
    # 处理原始信号
    signal_60k = np.abs(signal_60k)
    if not np.all((signal_60k - np.mean(signal_60k)) == 0):
        signal_60k = (signal_60k - np.mean(signal_60k)) / np.std(signal_60k)

    # 整理预测结果
    piece_json_this_class = get_piece_json(this_file_y_label)

    for piece_idx in range(len(piece_json_this_class)):
        this_piece = piece_json_this_class[piece_idx]
        # 只看静默
        if this_piece['piece_type'] != 0:
            continue
        to_change = rule_based_post_process(this_piece, signal_60k)
        if to_change:
            piece_json_this_class[piece_idx]['piece_type'] = 2

    y_label_after_change = get_60k_after_change(original_label_y=this_file_y_label,
                                                piece_json_this_class=piece_json_this_class)
    return y_label_after_change, os.getpid()

