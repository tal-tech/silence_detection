

input_demo = [{'silence_length': 935, 'voice_length': 1344, 'noise_length': 10, 'silence_rate': 0.40847531673219745, 'voice_rate': 0.5871559633027523, 'noise_rate': 0.00436871996505024,
               'details': [{'piece_type': 1, 'piece_length': 1, 'piece_start_time': 0, 'piece_end_time': 1},
                           {'piece_type': 0, 'piece_length': 1, 'piece_start_time': 1, 'piece_end_time': 2}]
               },
              {'silence_length': 935, 'voice_length': 1344, 'noise_length': 10, 'silence_rate': 0.40847531673219745, 'voice_rate': 0.5871559633027523, 'noise_rate': 0.00436871996505024,
               'details': [{'piece_type': 1, 'piece_length': 1, 'piece_start_time': 0, 'piece_end_time': 1},
                           {'piece_type': 0, 'piece_length': 1, 'piece_start_time': 1, 'piece_end_time': 2}]
              }, # 第二段输入
              {'silence_length': 935, 'voice_length': 1344, 'noise_length': 10, 'silence_rate': 0.40847531673219745, 'voice_rate': 0.5871559633027523, 'noise_rate': 0.00436871996505024,
               'details': [{'piece_type': 1, 'piece_length': 1, 'piece_start_time': 0, 'piece_end_time': 1},
                           {'piece_type': 0, 'piece_length': 1, 'piece_start_time': 1, 'piece_end_time': 2}]
               },
              {'silence_length': 935, 'voice_length': 1344, 'noise_length': 10, 'silence_rate': 0.40847531673219745, 'voice_rate': 0.5871559633027523, 'noise_rate': 0.00436871996505024,
               'details': [{'piece_type': 1, 'piece_length': 1, 'piece_start_time': 0, 'piece_end_time': 1},
                           {'piece_type': 0, 'piece_length': 1, 'piece_start_time': 1, 'piece_end_time': 2}]
              },
              ]


def merge_result(piece_results_list, piece_default_length=3600):
    '''

    :param piece_results_list: 输入片段结果
    :param piece_default_length: 每x秒切割为一个片段
    :return:
    '''
    if len(piece_results_list) == 1:
        return piece_results_list[0]
    merged_result = {}

    # 总长度是每个片段的数字之和.
    total_length = sum([sum([i['silence_length'], i['voice_length'], i['noise_length']]) for i in piece_results_list])
    total_silence_length = sum([i['silence_length'] for i in piece_results_list])
    total_noise_length = sum([i['noise_length'] for i in piece_results_list])
    total_voice_length = sum([i['voice_length'] for i in piece_results_list])

    merged_result['silence_length'] = total_silence_length
    merged_result['noise_length'] = total_noise_length
    merged_result['voice_length'] = total_voice_length

    merged_result['silence_rate'] = total_silence_length / total_length
    merged_result['voice_rate'] = total_voice_length / total_length
    merged_result['noise_rate'] = total_noise_length / total_length

    # details 从第二段开始，后面要依次增加前面的总长度.
    merged_result['details'] = []
    for idx, i in enumerate(piece_results_list):
        # 把第一个音频片段结果拿出来，是一个list
        tmp_piece = i['details']
        for t in range(len(tmp_piece)):
            # 每个位置加上偏移总量
            tmp_piece[t]['piece_start_time'] += idx * piece_default_length
            tmp_piece[t]['piece_end_time'] += idx * piece_default_length
        merged_result['details'].extend(tmp_piece)

    return merged_result


if __name__ == '__main__':
    print(merge_result(input_demo, piece_default_length=3600))
