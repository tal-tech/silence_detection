import numpy as np


def get_second_result(single_result, cut_point=None):
    # 60000 -> 600 * 100
    single_result_mat = np.reshape(single_result, (-1, 100))
    larger_part_1 = np.sum(single_result_mat == 1, axis=1) >= 25
    larger_part_2 = np.sum(single_result_mat == 2, axis=1) >= 75
    larger_part_0 = np.sum(single_result_mat == 0, axis=1) >= 25

    # 优先级:
    final_result = np.zeros(single_result_mat.shape[0])

    final_result[larger_part_2] = 2
    final_result[larger_part_0] = 0
    final_result[larger_part_1] = 1

    if cut_point is None:
        return final_result
    else:  # 切掉多余的部分
        final_result = final_result[:int(cut_point)]
        return final_result


def get_batch_each_second_results(detailed_results, detailed_stop_points, unit_length=700):
    second_level_each_class = []

    same_class_tmp = []
    for idx, stop_point in enumerate(detailed_stop_points):
        # 如果等于600, 则都归到一起
        if stop_point == unit_length:
            final_result = get_second_result(detailed_results[idx])
            same_class_tmp.append(final_result)
        else:
            final_result = get_second_result(detailed_results[idx], cut_point=stop_point)
            same_class_tmp.append(final_result)
            same_class_tmp = np.concatenate(same_class_tmp, axis=0)
            second_level_each_class.append(same_class_tmp)
            same_class_tmp = []
    if len(second_level_each_class) < 1:
        same_class_tmp = np.concatenate(same_class_tmp, axis=0)
        second_level_each_class.append(same_class_tmp)
    return second_level_each_class


def get_piece_json(y_array):
    json_list = []
    start_index = 0
    end_index = 1  # 不包含自己。1 ~ 60000（根据实际情况而定）

    piece_num = 0

    y_array = np.array(list(y_array) + [-1])

    for i in range(len(y_array) - 1):
        # i 最大是600
        if y_array[i] == y_array[i + 1]:
            end_index += 1
        else:
            json_list.append({
                'piece_type': int(y_array[i]),
                'piece_detail_range': [start_index, end_index],
                'piece_length': end_index - start_index,
            })
            piece_num += 1
            # 准备下一段
            start_index = i + 1
            end_index = i + 2

    for i in range(len(json_list) - 3):
        if (json_list[i]['piece_type'] == 1) and (json_list[i + 1]['piece_type'] == 2) and (
                json_list[i + 2]['piece_type'] == 1):
            json_list[i + 1]['piece_type'] = 1

    return json_list


def merge_result(result_before_merge):
    # 对相同的片段进行合并
    output_result_json = []
    voice_json_tmp = []
    json_idx = 0
    for i in range(len(result_before_merge) - 1):

        # 不是人声: 直接存起来
        if result_before_merge[i]['piece_type'] != 1:
            output_result_json.append(result_before_merge[i])

        # 是人声. 下一个还是人声
        elif (result_before_merge[i]['piece_type'] == 1) and (result_before_merge[i + 1]['piece_type'] == 1):
            voice_json_tmp.append(result_before_merge[i])

        # 是人声，下一个不是人声: 到目前为止的所有人声都存起来
        else:
            voice_json_tmp.append(result_before_merge[i])
            tmp = {
                'piece_type': 1,
                'piece_detail_range': [voice_json_tmp[0]['piece_detail_range'][0],
                                       voice_json_tmp[-1]['piece_detail_range'][-1]],
                'piece_length': sum([i['piece_length'] for i in voice_json_tmp]),
            }
            output_result_json.append(tmp)
            voice_json_tmp = []
    output_result_json.append(result_before_merge[len(result_before_merge) - 1])
    return output_result_json


# 输入 batch_each_second_results 输出占比统计

def batch_get_stats_and_details(batch_each_second_results):
    results = []
    for single_result in batch_each_second_results:
        merged_result = merge_result(get_piece_json(single_result))
        total_len = sum([i['piece_length'] for i in merged_result])

        results.append(
            {'silence_rate': sum([i['piece_length'] for i in merged_result if i['piece_type'] == 0]) / total_len,
             'voice_rate': sum([i['piece_length'] for i in merged_result if i['piece_type'] == 1]) / total_len,
             'noise_rate': sum([i['piece_length'] for i in merged_result if i['piece_type'] == 2]) / total_len,
             'silence_length': sum([i['piece_length'] for i in merged_result if i['piece_type'] == 0]),
             'voice_length': sum([i['piece_length'] for i in merged_result if i['piece_type'] == 1]),
             'noise_length': sum([i['piece_length'] for i in merged_result if i['piece_type'] == 2]),
             'details': merged_result}
        )
    return results


# 输出60ms粒度的
def get_batch_60ms_results(detailed_results, detailed_stop_points, unit_length=700):
    ms_level_each_class = []

    same_class_tmp = []
    for idx, stop_point in enumerate(detailed_stop_points):
        # 如果等于600, 则都归到一起
        final_result = detailed_results[idx]
        if stop_point == unit_length:
            same_class_tmp.append(final_result)
        else:
            final_result = final_result[:int(100 * stop_point)]
            same_class_tmp.append(final_result)
            same_class_tmp = np.concatenate(same_class_tmp, axis=0)
            ms_level_each_class.append(same_class_tmp)
            same_class_tmp = []
    if len(ms_level_each_class) < 1:
        same_class_tmp = np.concatenate(same_class_tmp, axis=0)
        ms_level_each_class.append(same_class_tmp)
    ms_level_each_class = [continuous_silence(i) for i in ms_level_each_class]

    return ms_level_each_class


# 60ms的要有滑窗.
def continuous_silence(y_array, window_size=6):
    # 输入是y序列，0=静默，1=人声，2=噪声
    # 从头开始滑窗，滑窗范围window_size. 注意滑窗一个单位长度代表真实音频10ms.
    # 滑窗范围内全都不是1则返回静默，否则返回人声.
    y_array = np.array(y_array)
    y_array_output = np.copy(y_array)

    # label不需要归成0/1了
    # y_array_output[y_array_output != 1] = 0

    ret_result = []
    for i in range(y_array_output.shape[0] - window_size - 1):

        if np.any(y_array_output[i: i + window_size] == 1):
            ret_result.append(1)
        elif np.any(y_array_output[i: i + window_size] == 2):
            ret_result.append(2)
        else:
            ret_result.append(0)

    ret_result = np.array(ret_result)
    ret_result = np.concatenate([ret_result, y_array_output[-(window_size + 1):]], axis=0)
    return ret_result
