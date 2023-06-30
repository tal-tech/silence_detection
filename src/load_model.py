import torch
import torch.nn as nn

from torch.utils.data import Dataset, DataLoader
# from sklearn.metrics import classification_report
# from file_utils import get_file_list
import os
import pandas as pd
import numpy as np
# os.environ["CUDA_VISIBLE_DEVICES"] = "5"
device = torch.device('cuda')
USE_GPU = True

# import logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s'
# )


def default_loader(x_df, max_sequence_length=30000):
    # print(x_df.shape)
    x_df = preprocess_concat(x_df)
    # print(x_df.shape)
    x_data = np.array(x_df)
    x_data_padding = np.zeros([max_sequence_length, 156])
    # print(x_data.shape)
    # print(x_data_padding.shape)

    x_data_padding[:x_data.shape[0], :] = x_data

    # print(x_data.shape)

    # 如果对当前样本标准化
    if not np.all(np.std(x_data_padding, axis=0) == 0):
        x_data_padding = (x_data_padding - np.mean(x_data_padding, axis=0))/np.std(x_data_padding, axis=0)  # 有些人声音大，有些人小。
    else:
        x_data_padding = np.zeros_like(x_data_padding) - 1
    # print(x_data_padding.shape) 
    return x_data_padding


def preprocess_concat(x_df_input):
    x_df = x_df_input.copy()
    x_df = x_df.reset_index(drop=True)
    # 输入是 #timestamp * #feature_dim 的df，这次是要和前一帧、后一帧concat到一起
    # 所以就是上移补最后一位和下移补第一位就好
    # 上移，拼接之后是下一时刻的
    x_df_up = pd.concat([x_df.iloc[1:, :], x_df.iloc[-1:, :]], axis=0).reset_index(drop=True)
    # print(x_df_up)
    # 下移，拼接之后是上一时刻的
    x_df_down = pd.concat([x_df.iloc[:1, :], x_df.iloc[:-1, :]], axis=0).reset_index(drop=True)
    # print(x_df_down)
    # print(x_df)
    return pd.concat([x_df_down, x_df, x_df_up], axis=1).reset_index(drop=True)


class GFCC_Trainset(Dataset):
    # 出来的时候会自动变成tensor.
    def __init__(self, loader=default_loader, x_df_list=None, max_sequence_length=30000):
        # 定义好 image 的路径
        self.x_file_list = x_df_list
        self.loader = loader
        self.max_sequence_length = max_sequence_length

    def __getitem__(self, index):
        fn_x = self.x_file_list[index]
        x_tensor = self.loader(fn_x, self.max_sequence_length)
        return x_tensor

    def __len__(self):
        return len(self.x_file_list)


CONFIG = dict()
CONFIG["embed_dim"] = 156  # 输入dim, 如果是20个gfcc * 4 * 3则是240
CONFIG["hidden_size"] = 32
CONFIG["layer_num"] = 3
CONFIG["dropout"] = 0.2
CONFIG["kernel_size"] = 5
CONFIG["learning_rate"] = 1e-5
CONFIG["num_labels"] = 3
CONFIG['batch_size'] = 16
CONFIG['save_path'] = './model/best_checkpoint_{}_{}_{}.pth.tar'.format(
    CONFIG["layer_num"], CONFIG["learning_rate"], CONFIG["hidden_size"])

best_eval_loss = 9999
early_stop_count = 0
break_flag = 0


class RCNNNet(nn.Module):
    def __init__(self, CONFIG):
        super(RCNNNet, self).__init__()

        self.lstm = nn.LSTM(CONFIG["embed_dim"], CONFIG["hidden_size"], CONFIG["layer_num"],
                            bidirectional=True, batch_first=True, dropout=CONFIG["dropout"])
        self.maxpool = nn.MaxPool1d(CONFIG["kernel_size"], padding=0)
        self.fc = nn.Linear(12, CONFIG["num_labels"])
        self.softmax = nn.Softmax(dim=2)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.maxpool(out)
        out = self.fc(out)
        out = self.softmax(out)
        return out


def load_my_model():
    my_model = RCNNNet(CONFIG)
    if torch.cuda.is_available() and USE_GPU:
        net = my_model.cuda(device)

    saved_model_path = CONFIG['save_path']
    my_model.load_state_dict(torch.load(saved_model_path))

    my_model.eval()
    return my_model
