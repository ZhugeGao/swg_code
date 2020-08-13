import csv

import pandas
import os
import pandasql as ps
from SWG_utils import add_previous_following

def read_extract(extract_path):  # could put in util
    df_extract = pandas.read_csv(
        extract_path, encoding='utf-8', header=0, keep_default_na=False)
    df_extract = df_extract.replace('nan', '') # in case there are 'nan'

    return df_extract


def read_formant(formant_file_path):
    df = pandas.read_csv(formant_file_path, header=0, encoding='utf-8', delimiter="\t", keep_default_na=False)
    return df


def move_formant_wav(formant_trans_id_list, original_path, new_path):
    for formant_id in formant_trans_id_list:
        wav_name = formant_id + '.wav'
        if not os.path.exists(new_path + wav_name):
            try:
                os.rename(original_path+wav_name, new_path+wav_name)
            except FileNotFoundError:
                print("file:", wav_name, "not found.")


def extract_rows_with_var_code(df_extract, var_code):
    df = df_extract[df_extract['var_code'].str.contains(var_code)]
    return df


date = '20200730'

speakers = ['panel']  # 'panel', 'trend', 'panel'
common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
for speaker_type in speakers:
    phone_name = 'SWG_' + speaker_type + '_' + 'phone' + '_' + date + '.csv'
    formant_name_extract = 'SWG_' + speaker_type + '_' + 'formant_raw' + '_' + date + '.csv'
    formant_output = 'SWG_' + speaker_type + '_' + 'formant' + '_' + date + 'noSocialInfo' +'.csv'
    phone_extract_path = common_path + phone_name
    formant_extract_path = common_path + formant_name_extract
    formant_path = common_path + 'done_'+ speaker_type +'/'
    formant_output_path = common_path + formant_output

    # # create formant_raw using phone extract
    # df_extract = read_extract(phone_extract_path)
    # # print(df_extract.columns)
    # # # # # print(df_extract['var_code'])
    # df = extract_rows_with_var_code(df_extract, "AIS")
    # # # print(df.columns)
    # df.to_csv(formant_extract_path, index=False)
    with open(formant_output_path, 'w', newline="") as f:
        csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(
            ['trans_id', 'time', 'F1Hz', 'F2Hz', 'zeroed_word_start_time', 'zeroed_word_end_time', 'normalized_time_word', 'word_start_time',
         'word_end_time', 'word_duration', 'word_SWG', 'seg_number', 'zeroed_seg_start_time', 'zeroed_seg_end_time', 'normalized_time_seg', 'seg_start_time',
         'seg_end_time', 'seg_duration', 'segment_SWG', 'diphthong_orthography', 'var_code',
         'word_German', 'word_lemma', 'word_stem', 'POS_tag'])
    f.close()
    #
    # # read formant_extract
    formant_extract = read_extract(formant_extract_path)
    # print(formant_extract.columns)
    formant_extract['word_duration'] = formant_extract['word_end_time'] - formant_extract['word_start_time']
    # print(formant_extract[['word_duration', 'word_end_time', 'word_start_time']])
    formant_extract['seg_duration'] = formant_extract['seg_end_time'] - formant_extract['seg_start_time']
    formant_extract = formant_extract[['trans_id', 'word_start_time', 'word_end_time', 'word_duration', 'word_SWG', 'seg_number',
       'seg_start_time', 'seg_end_time', 'seg_duration', 'segment_SWG', 'diphthong_orthography', 'var_code',
       'word_German', 'word_lemma', 'word_stem', 'POS_tag']]
    # # print(formant_extract.columns)
    # # # read formant
    formant_file_list = [file for file in os.listdir(formant_path) if file.endswith('.Formant')]
    formant_file_list = sorted(formant_file_list,
                       key=lambda x: (int(x.split('-')[0][1:]), int(x.split('-')[1]), int(x.split('-')[3]), int(x.split('_')[1][:-8])))
    for formant_file in formant_file_list:
        print(formant_file[:-8])
        formant_raw = read_formant(formant_path + formant_file)
        formant_raw['trans_id'] = formant_file[:-8]
        # print(formant_raw.columns)
        # list all the formant time, F1, F2 within that time frame
        formant = formant_raw[['trans_id', 'time(s)', 'F1(Hz)', 'F2(Hz)']]
        formant = formant.rename(columns={"time(s)": "time", "F1(Hz)": "F1Hz", "F2(Hz)": "F2Hz"})  # rename column for SQL
    #     print(formant.columns)
        formant_swg = formant_extract[formant_extract['trans_id'] == formant_file[:-8]]
        # formant_swg.index = pandas.IntervalIndex.from_arrays(formant_swg['seg_start_time'], formant_swg['seg_end_time'], closed='both')
        # print(formant_swg.index)
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
        df['zeroed_seg_start_time'] = 0.0
        df['zeroed_seg_end_time'] = df['time'] - df['seg_start_time']


        for i, group in df.groupby(['seg_start_time', 'seg_end_time']):
            step = float(1/(len(group)-1))
            # print(step)
            # print(len(group))
            # print(step*len(group))
            cnt = 0
            for row_index, row in group.iterrows():
                df.at[row_index, 'normalized_time_seg'] = round(cnt * step, 4)
                cnt += 1
        for i, group in df.groupby(['word_start_time', 'word_end_time']):
            step = float(1/(len(group)-1))
            # print(step)
            # print(len(group))
            # print(step*len(group))
            cnt = 0
            for row_index, row in group.iterrows():
                df.at[row_index, 'normalized_time_word'] = round(cnt * step, 4)
                cnt += 1
        # print(df['normalized_time_word'])
        # print(df.columns)
        df = df[['trans_id', 'time', 'F1Hz', 'F2Hz', 'zeroed_word_start_time', 'zeroed_word_end_time', 'normalized_time_word', 'word_start_time',
         'word_end_time', 'word_duration', 'word_SWG', 'seg_number', 'zeroed_seg_start_time', 'zeroed_seg_end_time', 'normalized_time_seg', 'seg_start_time',
         'seg_end_time', 'seg_duration', 'segment_SWG', 'diphthong_orthography', 'var_code',
         'word_German', 'word_lemma', 'word_stem', 'POS_tag']]

        df.to_csv(formant_output_path, mode='a', index=False, header=False)

    # formant_trans_id_list = list(formant_extract['trans_id'])
    # add_previous_following(formant_output_path, 'formant')
