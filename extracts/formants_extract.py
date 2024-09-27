import csv

import numpy as np
import pandas as pd
import os
import pandasql as ps
from tqdm import tqdm
from utils.file_utils import read_file


# need add searching not just based on var_code but also based on phone.

def read_extract(extract_path):  # could put in util
    df_extract = read_file(extract_path, encoding='utf-8', header=0, keep_default_na=False)
    df_extract = df_extract.replace('nan', '')  # in case there are 'nan'

    return df_extract


def read_formant(formant_file_path):
    return read_file(formant_file_path, header=0, encoding='utf-8', delimiter="\t", keep_default_na=False)


def move_formant_wav(formant_trans_id_list, original_path, new_path):
    for formant_id in formant_trans_id_list:
        wav_name = formant_id + '.wav'
        if not os.path.exists(new_path + wav_name):
            try:
                os.rename(original_path + wav_name, new_path + wav_name)
            except FileNotFoundError:
                print("file:", wav_name, "not found.")


def extract_rows_with_var_code(df_extract, var_code):
    df = df_extract[df_extract['var_code'].str.contains(var_code)]
    return df

def extract_rows_with_phones(df_extract, phones):
    # Extract rows where 'segment_SWG' contains any of the phones from the list
    # Create a boolean mask for matching rows in 'segment_SWG' column
    segments_mask_list = df_extract['segment_SWG'].isin(phones) # True if the segment contains any of the phones in the list
    # Create a boolean mask for matching rows in 'word_SWG' column
    word_SWG_mask = df_extract['word_SWG'].isin(df_extract.loc[segments_mask_list, 'word_SWG'])
    # Combine the masks to get the final mask for desired rows
    final_mask = segments_mask_list | word_SWG_mask
    # Extract the desired rows
    df = df_extract[final_mask]

    return df

def create_raw_formants_extract(phones_extract_path, formants_raw_extract_path, target_to_extract, target_is_var_code=True):
    # create formant_raw using phone extract
    df_extract = read_extract(phones_extract_path)

    if target_is_var_code:
        df = extract_rows_with_var_code(df_extract, target_to_extract)
    else:
        df = extract_rows_with_phones(df_extract, target_to_extract)
    df.to_csv(formants_raw_extract_path, index=False)
def create_formants_extract(formant_data_paths, phones_extract_path, formants_raw_extract_path,
                            formants_extract_output_path):
    # create the csv, if the file already exists, it will be overwritten
    with open(formants_extract_output_path, 'w', newline="") as f:
        csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(
            ['trans_id', 'time', 'F1Hz', 'F2Hz', 'F3Hz', 'F4Hz', 'zeroed_word_start_time', 'zeroed_word_end_time',
             'normalized_time_word', 'word_start_time',
             'word_end_time', 'word_duration', 'word_SWG', 'seg_number', 'zeroed_time_seg', 'normalized_time_seg',
             'seg_start_time',
             'seg_end_time', 'seg_duration', 'segment_SWG', 'diphthong_orthography', 'var_code',
             'word_German', 'word_lemma', 'word_stem', 'POS_tag'])
    f.close()
    # read formant_extract
    formant_extract = read_extract(formants_raw_extract_path)
    formant_extract['word_duration'] = formant_extract['word_end_time'] - formant_extract['word_start_time']
    formant_extract['seg_duration'] = formant_extract['seg_end_time'] - formant_extract['seg_start_time']
    formant_extract = formant_extract[
        ['trans_id', 'word_start_time', 'word_end_time', 'word_duration', 'word_SWG', 'seg_number',
         'seg_start_time', 'seg_end_time', 'seg_duration', 'segment_SWG', 'diphthong_orthography', 'var_code',
         'word_German', 'word_lemma', 'word_stem', 'POS_tag']]
    # read formant
    # formant_file_list = [file for file in os.listdir(formant_data_path) if file.endswith('.Formant')]
    # formant_file_list = sorted(formant_file_list,
    #                            key=lambda x: (int(x.split('-')[0][1:]), int(x.split('-')[1]), int(x.split('-')[3]),
    #                                           int(x.split('_')[1][:-8])))

    formant_file_list = []
    for path in formant_data_paths:
        formant_file_list.extend([os.path.join(path, file) for file in os.listdir(path) if file.endswith('.Formant')])
    # sort the formant_file_list
    if 'panel' in phones_extract_path:
        formant_file_list = sorted(formant_file_list, key=lambda path: (
            int(path.split('/')[-2]),  # Sort based on '1982', '2017', etc.
            int(path.split('S')[1].split('-')[0]),  # Sort based on '007', '008', etc.
            int(path.split('-')[3]),  # Sort based on '-1-', '-2-', etc.
            int(path.split('_')[-1][:-8])  # Sort based on '_1', '_2', etc.
        ))
    else:
        formant_file_list = sorted(formant_file_list, key=lambda path: (
            int(path.split('S')[1].split('-')[0]),  # Sort based on '007', '008', etc.
            int(path.split('-')[1]),  # Sort based on '-82-', '-17-', etc.
            int(path.split('-')[3]),  # Sort based on '-1-', '-2-', etc.
            int(path.split('_')[-1][:-8])  # Sort based on '_1', '_2', etc.
        ))


    for formant_file in formant_file_list:
        print(formant_file.split('/')[-1][:-8]) # the trans_id
        formant_raw = read_formant(formant_file) # TODO: is this the right path?
        formant_raw['trans_id'] = formant_file.split('/')[-1][:-8]
        # print(formant_raw['trans_id'].head(10))

        # list all the formant time, F1, F2, F3 and F4 within that time frame
        formant = formant_raw[['trans_id', 'time(s)', 'F1(Hz)', 'F2(Hz)', 'F3(Hz)', 'F4(Hz)']]
        formant = formant.rename(
            columns={"time(s)": "time", "F1(Hz)": "F1Hz", "F2(Hz)": "F2Hz", "F3(Hz)": "F3Hz", "F4(Hz)": "F4Hz"})  # rename column for SQL
        # print(formant.columns)
        formant_swg = formant_extract[
            formant_extract['trans_id'] == formant_file.split('/')[-1][:-8]]  # or split . and take the first part
        # print(formant_swg.columns)
        # sql code snippet
        # TODO: write a brief description of this
        sqlcode = '''
        select *
        from formant
        inner join formant_swg on formant.trans_id=formant_swg.trans_id
        where formant.time >= formant_swg.seg_start_time and formant.time <= formant_swg.seg_end_time
        '''
        # group by formant.trans_id


        newdf = ps.sqldf(sqlcode, locals())
        df = newdf.loc[:, ~newdf.columns.duplicated()]
        df['normalized_time_word'] = ''
        df['normalized_time_seg'] = ''
        df['zeroed_word_start_time'] = 0.0
        df['zeroed_word_end_time'] = df['time'] - df['word_start_time']
        df['zeroed_time_seg'] = df['time'] - df['seg_start_time']

        for i, group in df.groupby(['seg_start_time', 'seg_end_time']):  # new seg unique id. group by 'trans_id'
            step = float(1 / (len(group) - 1))
            cnt = 0
            for row_index, row in group.iterrows():
                df.at[row_index, 'normalized_time_seg'] = round(cnt * step, 4)
                cnt += 1

        for i, group in df.groupby(['word_start_time', 'word_end_time']):
            step = float(1 / (len(group) - 1))
            cnt = 0
            for row_index, row in group.iterrows():
                df.at[row_index, 'normalized_time_word'] = round(cnt * step, 4)
                cnt += 1
        df = df[['trans_id', 'time', 'F1Hz', 'F2Hz', 'F3Hz', 'F4Hz', 'zeroed_word_start_time', 'zeroed_word_end_time',
                 'normalized_time_word', 'word_start_time',
                 'word_end_time', 'word_duration', 'word_SWG', 'seg_number', 'zeroed_time_seg', 'normalized_time_seg',
                 'seg_start_time',
                 'seg_end_time', 'seg_duration', 'segment_SWG', 'diphthong_orthography', 'var_code',
                 'word_German', 'word_lemma', 'word_stem', 'POS_tag']]

        uni_ID = df['trans_id'].unique()

        # Add new columns
        df['AR_start_seg'] = False  # a new column, boolean array, used to mark the start time? of the segment
        df['normalized_time_seg'] = np.nan  # new column, empty.
        df['zeroed_time_seg'] = np.nan  # new column, empty.

        # drop = ["zeroed_seg_start_time", "zeroed_seg_end_time"]
        # twn_formants = twn_formants.drop(drop, axis=1)

        col_order = ["trans_id", "time", "F1Hz", "F2Hz", "F3Hz", "F4Hz", "zeroed_word_start_time",
                     "zeroed_word_end_time",
                     "normalized_time_word", "word_start_time", "word_end_time", "word_duration", "word_SWG",
                     "seg_number",
                     "AR_start_seg", "zeroed_time_seg", "normalized_time_seg", "seg_start_time", "seg_end_time",
                     "seg_duration",
                     "segment_SWG", "diphthong_orthography", "var_code", "word_German", "word_lemma", "word_stem",
                     "POS_tag"]

        print("postprocessing formant extracts...")
        for iid in tqdm(range(len(uni_ID))):
            if iid % 500 == 0:
                print(round(iid / len(uni_ID), 2))

            wo = df['trans_id'] == uni_ID[iid]  # the index/position of unique files

            df.at[
                min(np.where(wo)[0]), 'AR_start_seg'] = True  # set the value to true for the first segment of each file
            df.loc[wo, 'normalized_time_seg'] = np.linspace(0, 1, num=sum(
                wo))  # normalized time: for all the segments in one file, start from 0 to 1.
            df.loc[wo, 'zeroed_time_seg'] = df.loc[wo, 'time'] - min(df.loc[wo, 'time'])  # zeroed time: time minus the start time. Difference between the current time and the start time of the file.

        formants = df.loc[:, col_order] # TODO

        formants.to_csv(formants_extract_output_path, mode='a', index=False, header=False)
