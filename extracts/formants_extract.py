import csv

import pandas as pd
import os
import pandasql as ps


def read_extract(extract_path):  # could put in util
    df_extract = pd.read_csv(
        extract_path, encoding='utf-8', header=0, keep_default_na=False)
    df_extract = df_extract.replace('nan', '')  # in case there are 'nan'

    return df_extract


def read_formant(formant_file_path):
    df = pd.read_csv(formant_file_path, header=0, encoding='utf-8', delimiter="\t", keep_default_na=False)
    return df


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


def create_formants_extract(formant_data_path, phones_extract_path, formants_raw_extract_path,
                            formants_extract_output_path, target_var_code):
    # create formant_raw using phone extract
    df_extract = read_extract(phones_extract_path)
    df = extract_rows_with_var_code(df_extract, target_var_code)
    # # print(df.columns)
    df.to_csv(formants_raw_extract_path, index=False)
    with open(formants_extract_output_path, 'w', newline="") as f:
        csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(
            ['trans_id', 'time', 'F1Hz', 'F2Hz', 'zeroed_word_start_time', 'zeroed_word_end_time',
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
    formant_file_list = [file for file in os.listdir(formant_data_path) if file.endswith('.Formant')]
    formant_file_list = sorted(formant_file_list,
                               key=lambda x: (int(x.split('-')[0][1:]), int(x.split('-')[1]), int(x.split('-')[3]),
                                              int(x.split('_')[1][:-8])))
    for formant_file in formant_file_list:
        print(formant_file[:-8])
        formant_raw = read_formant(formant_data_path + formant_file)
        formant_raw['trans_id'] = formant_file[:-8]
        # print(formant_raw.columns)
        # list all the formant time, F1, F2 within that time frame
        formant = formant_raw[['trans_id', 'time(s)', 'F1(Hz)', 'F2(Hz)']]
        formant = formant.rename(
            columns={"time(s)": "time", "F1(Hz)": "F1Hz", "F2(Hz)": "F2Hz"})  # rename column for SQL
        formant_swg = formant_extract[
            formant_extract['trans_id'] == formant_file[:-8]]  # or split . and take the first part

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

        df = df[['trans_id', 'time', 'F1Hz', 'F2Hz', 'zeroed_word_start_time', 'zeroed_word_end_time',
                 'normalized_time_word', 'word_start_time',
                 'word_end_time', 'word_duration', 'word_SWG', 'seg_number', 'zeroed_time_seg', 'normalized_time_seg',
                 'seg_start_time',
                 'seg_end_time', 'seg_duration', 'segment_SWG', 'diphthong_orthography', 'var_code',
                 'word_German', 'word_lemma', 'word_stem', 'POS_tag']]

        df.to_csv(formants_extract_output_path, mode='a', index=False, header=False)
