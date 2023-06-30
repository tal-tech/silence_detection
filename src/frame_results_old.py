from src.silence_utils import *
from src.load_model import GFCC_Trainset, DataLoader, device
from src.post_process import post_process_func
from src.config import gfcc_cfg
import os


def get_frame_results(wav_segment_list, batch_size=15, max_sequence_length=30000, n_jobs=10, my_model=None):
    feature_result = []
    ###########################################################
    # 多进程，会爆内存，需要调试
    # p = multiprocessing.Pool(processes=n_jobs, maxtasksperchild=1)
    #
    # for idx, wav_segment in enumerate(wav_segment_list):
    #     # logging.info('start feature extract from audio')
    #     feature_result.append(p.apply_async(convert_raw_feature, args=(wav_segment, gfcc_cfg, idx, max_sequence_length)))
    #
    # p.close()
    # p.join()
    #
    # feature_df_list = []
    # for i in feature_result:
    #     feature_df_list.append(i.get())
    # arr_60k_list = [i[2] for i in feature_df_list] # 60k signal.
    # feature_df_list = [i[0] for i in feature_df_list] # features.
    # child_pid = [i[3] for i in feature_df_list]
    # # for i in child_pid:
    # #     try:
    # #         os.kill(i, 0)
    # #     except:
    # #         pass
    # #
    ##############################

    # logging.info('start feature extract from audio')
    ##############################
    # 用 map_async
    # p = multiprocessing.Pool(processes=n_jobs, maxtasksperchild=1)
    # input_params = []
    # for idx, wav_segment in enumerate(wav_segment_list):
    #     input_params.append([wav_segment, gfcc_cfg, idx, max_sequence_length])
    #
    # feature_result = p.map_async(convert_raw_feature, input_params, chunksize=1)
    # del wav_segment_list
    #
    # p.close()
    # p.join()
    # feature_df_list = feature_result.get()
    # # for i in feature_result:
    # #     feature_df_list.append(i.get())
    # del p
    print(121321)
    start_time = time.time()
    ####################################
    # 测试不用多进程，长片段输入的结果:
    l = len(wav_segment_list)
    wav_segment = np.concatenate(wav_segment_list, axis=0)
    idx=0
    input_params = [wav_segment, gfcc_cfg, idx, int(max_sequence_length * l)]
    print(max_sequence_length)

    feature_df_list_ori = convert_raw_feature(input_params)
    arr_60k_list = [feature_df_list_ori[1][i * max_sequence_length: (i + 1) * max_sequence_length] for i in range(l)] # 60k signal.
    feature_df_list = [feature_df_list_ori[0].iloc[i * max_sequence_length: (i + 1) * max_sequence_length] for i in range(l)] # features.
    # print([i.shape for i in feature_df_list])
    print(time.time() - start_time)
    ####################################
    # p = multiprocessing.Pool(processes=n_jobs, maxtasksperchild=1)
    # for idx, wav_segment in enumerate(wav_segment_list):
    #     input_params.append([wav_segment, gfcc_cfg, idx, max_sequence_length])
    # # del wav_segment
    # del wav_segment_list
    # feature_result = p.map_async(convert_raw_feature, input_params, chunksize=1)
    # p.close()
    # p.join()

    # arr_60k_list = [i[1] for i in feature_df_list] # 60k signal.
    # feature_df_list = [i[0] for i in feature_df_list] # features.
    # child_pid = [i[3] for i in feature_df_list]


    ##############################
    # 循环，不会爆内存

    # for idx, wav_segment in enumerate(wav_segment_list):
    #     logging.info('start feature extract from audio')
    #     feature_result.append(convert_raw_feature(wav_segment, gfcc_cfg, idx, max_sequence_length=max_sequence_length))
    #
    # child_pid = [i[3] for i in feature_result]
    # arr_60k_list = [i[2] for i in feature_result] # 60k signal.
    # feature_df_list = [i[0] for i in feature_result] # features.

    ###############################
    gfcc_input_set = GFCC_Trainset(x_df_list=feature_df_list, max_sequence_length=max_sequence_length)
    valloader = DataLoader(gfcc_input_set, batch_size=batch_size, shuffle=False, num_workers=0)
    valid_iter = valloader
    # logging.info('start predicting')
    print('predict...')

    for eval_x in valid_iter:
        print('predict...')
        prediction = my_model(eval_x.float().to(device))
        # prediction = prediction.cpu().detach().numpy()
        # eval_y_flatten = eval_y.cpu().detach().numpy().flatten()

        # print(prediction)
        # print(prediction.shape)

    # prediction = np.argmax(prediction, axis=2)
    # prediction_list = [prediction[i, :] for i in range(prediction.shape[0])]
    # return arr_60k_list, prediction_list
    return [], []


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

