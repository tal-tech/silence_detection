import pickle
import pandas as pd
import glob
#

c = 0
file_list = glob.glob('/workspace/projects_2020/godeye/silence/dada_test_data/3*.wav.pkl')
# file_list = glob.glob('/workspace/projects_2020/godeye/silence/dada_test_data/正常*.wav.pkl')
for idx, fp in enumerate(file_list):
    with open(fp, 'rb') as f:
        for this_json in pickle.load(f):

            if c == 0:
                df = pd.DataFrame(this_json['details'])
                df['silence'] = this_json['silence']
                df['voice'] = this_json['voice']
                df['noise'] = this_json['noise']
                try:
                    df['filename'] = this_json['filename']
                except:
                    df['filename'] = fp.split('/')[-1].replace('.pkl', '')
            else:
                df_new = pd.DataFrame(this_json['details'])
                df_new['silence'] = this_json['silence']
                df_new['voice'] = this_json['voice']
                df_new['noise'] = this_json['noise']
                try:
                    df_new['filename'] = this_json['filename']
                except:
                    df_new['filename'] = fp.split('/')[-1].replace('.pkl', '')
                df = pd.concat([df, df_new], axis=0)
            c += 1
            print(c)

# df.to_csv('正常50堂课.csv', index=False)
df.to_csv('测试{}堂课.csv'.format(c), index=False)
