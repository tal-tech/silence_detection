from src.long_wav_process import get_silence_from_file_list
import glob
from src.load_model import load_my_model
import time

if __name__ == '__main__':

    wav_dir = './wav_data/'
    wav_list = glob.glob(wav_dir + '*.wav')  # 实际的输入.
    my_model = load_my_model()
    # print(wav_list[0])
    for w in wav_list:
        start_time = time.time()
        result = get_silence_from_file_list(w, batch_size=15, max_sequence_length=24000,
                                            my_model=my_model, output_mode='1s') # 或='60ms'

        print(time.time() - start_time)
        print(result)

