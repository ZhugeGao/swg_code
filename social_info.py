import pandas as pd
import os
import re


def add_file_id_col(speaker_file_path, tg_path, date):
    """This script read in the speaker file, and all the corresponding TextGrids and automatically create a new speaker file with
    The actual TextGrids names in the first column, which can be used to add social information to the words or phrases file"""
    # unicode support?
    df = pd.read_csv(speaker_file_path, header=0)
    df.rename(columns={'trans_id': 'File_ID'}, inplace=True)
    tg_list = os.listdir(tg_path)
    tg = filter(lambda tg: re.search(r'\.TextGrid', tg), tg_list)
    list_tg = list(tg)
    list_tg = [tg.replace('.TextGrid', '') for tg in list_tg]
    df_tg = pd.DataFrame({'trans_id': list_tg})

    df_tg['File_ID'] = ''
    for index, row in df_tg.iterrows():
        row['File_ID'] = re.sub(r'-\d-', '-n-', row['trans_id'])
    df_m = pd.merge(df_tg, df, on='File_ID', how='outer')
    df_m = df_m.drop('File_ID', axis=1)
    df_m.to_csv(
        '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SWG_'+speaker_type + '_speakers_'+date+'.csv',
        index=False)


def sort_social_col(speaker_file_path):  # , col_name
    df = pd.read_csv(speaker_file_path, header=0)
    df = df.sort_values(by=['trans_id'])
    df.to_csv('/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SWG_style_speakers_09mar2020.csv', index=False)
    print(df)


# def ge_g():
#     # read all the csv in the directory
#     path = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/ddm_csv/"
#     file_list = [file for file in os.listdir(path) if file.endswith('.csv')]
#     for ddm in file_list:
#         print(ddm)
#         df = pd.read_csv(path+ddm, header=None)
#         df = df.dropna(axis='index', how='any')
#         for index, row in df.iterrows():
#             #if "[ge]" in row[0]:
#             row[1] = re.sub(r'ge', 'ge?', row[1], count=1)
#         df.to_csv(path+ddm, index=False, header=False)


if __name__ == '__main__':
    speaker_types = ['twin', 'trend', 'panel']
    date = "24apr2020"
    for speaker_type in speaker_types:
        speaker_file_path = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SWG_"+ speaker_type +"_speakers_"+date+".csv"
        tg_path = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/" + speaker_type+"_tg/" # use a dictionary or something

        add_file_id_col(speaker_file_path, tg_path, date)
