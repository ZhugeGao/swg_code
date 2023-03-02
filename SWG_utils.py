"""helper methods for the swg project data processing"""
import datetime
import re
import pandas as pd
import regex
import os
import csv

# Global variables

double_dash = re.compile(r'^-[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî?]+-[,.!?]*$')
dash_l = re.compile(r'^-[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî]+-?[,.!?]*$')
dash_r = re.compile(r'^-?[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî]+-[,.!?]*$')
person_name_l = re.compile(r'{[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî\-?]*}?')
person_name_r = re.compile(r'{?[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî\-?]*}')
hyphen_2 = re.compile(r'-{2,}')
hyphen_3 = re.compile(r'^-{3}')
hyphen = re.compile(r'^-$')
dot_2 = re.compile(r'\.{2,3}')
quo_2 = re.compile(r'^\d?"{2,}$')
question_2 = re.compile(r'\?{2,}')
angle_brackets = re.compile(r'^<[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî?]+>[,.!?]*$')
filter_list = [angle_brackets, person_name_l, person_name_r, hyphen, hyphen_2, hyphen_3, double_dash, dash_l,
               dash_r, dot_2, question_2,
               quo_2]

# tags for skipping the reading, word lists and word games parts
tags_for_skipping = {'[BEGIN-READING]': '[END-READING]', '[BEGIN-WORD-LISTS]': '[END-WORD-LISTS]',
                     '[BEGIN-WORD-GAMES]': '[END-WORD-GAMES]'}

# csv methods for clauses and rel_clauses extract
def output_clauses_csv(extract_path, transcript_id, beg_hms, sym_seq, swg, var, pos):
    with open(extract_path, mode='a', newline="") as output_file:
        csv_writer = csv.writer(
            output_file,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([transcript_id, beg_hms, sym_seq, swg, var, pos])


def create_clauses_csv(extract_path):
    """
    If the csv file you want to output does not exist in your path, this function will create it.
    """
    with open(extract_path, 'w', newline="") as create_the_csv:
        csv_writer = csv.writer(
            create_the_csv,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(
            ['trans_id', 'beg_hms', 'sym_seq', 'SWG', 'VAR', 'POS'])  # File_ID to Transcript_ID
    create_the_csv.close()


def add_file_id_col(speaker_type, tg_path_list, speaker_file_date):
    """This script read in the speaker file, and all the corresponding TextGrids and automatically create a new speaker file with
    The actual TextGrids names in the first column, which can be used to add social information to the words or phrases file"""
    # unicode support?
    speaker_file_path = 'SWG_' + speaker_type + '_speakers_' + speaker_file_date + '.csv'
    df = pd.read_csv(speaker_file_path, header=0, encoding='utf-8-sig')
    df.rename(columns={'trans_id': 'File_ID'}, inplace=True)
    tg_list = []
    for tg_path in tg_path_list:
        tg_list += os.listdir(tg_path)
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
        '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SWG_' + speaker_type + '_speakers_' + speaker_file_date + '.csv',
        index=False)


def add_previous_following(extract_path, extract_type):
    # TODO: write documentation for this method.
    # what does this do?
    df_extract = read_extract(extract_path)
    # rename the columns
    df_extract['previous_word'] = ''
    df_extract['following_word'] = ''
    df_extract['previous_seg'] = ''
    df_extract['following_seg'] = ''
    if extract_type == 'phone':
        df_extract = df_extract[
            ['trans_id', 'word_start_time', 'word_end_time', 'word_SWG', 'previous_word', 'following_word',
             'seg_number', 'seg_start_time', 'seg_end_time', 'segment_SWG',
             'diphthong_orthography', 'previous_seg', 'following_seg', 'var_code', 'word_German', 'word_lemma',
             'word_stem', 'POS_tag']]
    if extract_type == 'formant':
        df_extract = df_extract[
            ['trans_id', 'time', 'F1(Hz)', 'F2(Hz)', 'zeroed_word_start_time', 'zeroed_word_end_time',
             'normalized_time_word', 'word_start_time',
             'word_end_time', 'word_duration', 'word_SWG', 'previous_word', 'following_word', 'seg_number',
             'zeroed_seg_start_time', 'zeroed_seg_end_time', 'normalized_time_seg', 'seg_start_time',
             'seg_end_time', 'seg_duration', 'segment_SWG', 'diphthong_orthography', 'previous_seg',
             'following_seg', 'var_code', 'word_German', 'word_lemma', 'word_stem', 'POS_tag']]
    previous_word = "#"
    following_word = "#"
    last_time = None
    last_word = "<P>"
    next_word_index = 0
    for i, rows in df_extract.iterrows():
        # print(rows['trans_id'])
        previous_seg = "#"
        following_seg = "#"
        current_time = rows['word_start_time']
        current_word = rows['word_SWG']
        # print("current", rows['segment_SWG'])
        # print("cw", current_word)
        if i != 0:  # there is a previous
            # print("previous", df_extract.iloc[i-1]['segment_SWG'])
            if last_time != current_time:  # time interval changed, word changed
                if "<" not in last_word:
                    previous_word = last_word
                else:
                    previous_word = "#"
                last_time = current_time
                last_word = current_word
            else:
                if "_" not in df_extract.iloc[i - 1]['segment_SWG']:
                    previous_seg = df_extract.iloc[i - 1]['segment_SWG']

        if i + 1 < len(df_extract):
            next_row_time = following_time = df_extract.iloc[i + 1]['word_start_time']
            # print("after", df_extract.iloc[i+1]['segment_SWG'])
            if next_row_time == current_time:  # same word
                if "_" not in df_extract.iloc[i + 1]['segment_SWG']:
                    following_seg = df_extract.iloc[i + 1]['segment_SWG']
        else:
            following_word = "#"

        if next_word_index < len(df_extract):
            following_time = df_extract.iloc[next_word_index]['word_start_time']
            while following_time == current_time and next_word_index < len(df_extract) - 1:
                next_word_index += 1
                following_time = df_extract.iloc[next_word_index]['word_start_time']
                # print(next_word_index)
                # print(following_time)
            next_word = df_extract.iloc[next_word_index]['word_SWG']
            if "<" not in next_word:
                following_word = next_word
            else:
                following_word = "#"

        df_extract.at[i, 'previous_seg'] = previous_seg
        df_extract.at[i, 'following_seg'] = following_seg
        df_extract.at[i, 'previous_word'] = previous_word
        df_extract.at[i, 'following_word'] = following_word

    df_extract.to_csv(extract_path, mode='w', index=False, header=True)


def compile_pattern(word_pattern, var_code):  # pattern is lowercase
    pattern = word_pattern.strip()
    pattern = pattern.replace("\ufeff", "")
    pattern = pattern.replace("???", "")
    pattern = pattern.replace(" ", "")
    pattern = pattern.replace("xxx", "")
    if pattern.startswith("*"):
        pattern = '.*' + pattern[1:]
    else:
        pattern = "^" + pattern
    if pattern.endswith("*"):
        pattern = pattern[:-1] + '.*'
    else:
        pattern = pattern + "$"
    pattern = pattern.replace("[ge]", "[ge?]")
    if "SAF5" in var_code:
        pattern = pattern.replace("ge", "ge?")
    pattern = pattern.replace("[", "\[")  # escape this special symbol for matching
    pattern = pattern.replace("]", "\]")
    compiled_pattern = regex.compile(pattern)

    return compiled_pattern


def ge_g():  # SAF5
    path = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SG-LEX 21apr2020_.csv"
    df = read_extract(path)
    df = df.dropna(axis='index', how='any')
    for index, row in df.iterrows():
        if "SAF5" in row['word_vars']:
            df.at[index, 'word_variant'] = re.sub(r'ge', 'ge?', row['word_variant'], count=1)
    df.to_csv(path, index=False, header=True)


def read_extract(extract_path):  # could put in util
    df_extract = pd.read_csv(
        extract_path, encoding='utf-8', header=0, keep_default_na=False)
    df_extract = df_extract.replace('nan', '')  # in case there are 'nan'

    return df_extract


def read_lex_table(lex_table_path):
    if lex_table_path.endswith(".xlsx"):
        lex = pd.read_excel(lex_table_path, index_col=None, header=0)
    else:
        lex = pd.read_csv(lex_table_path, index_col=None, header=0)
    lex.dropna(axis='columns', how='all', inplace=True)
    return lex


def skip_by_tags(outputs, type):
    start_index = -1
    end_index = -1
    if type == 'r':
        begin_label = "[BEGIN-READING]"
        end_label = "[END-READING]"
    elif type == 'wl':
        begin_label = "[BEGIN-WORD-LISTS]"
        end_label = "[END-WORD-LISTS]"
    elif type == 'wg':
        begin_label = "[BEGIN-WORD-GAMES]"
        end_label = "[END-WORD-GAMES]"
    for i, output in enumerate(outputs):
        if begin_label in output[1] and start_index == -1:
            start_index = i
        if end_label in output[1] and end_index == -1:
            end_index = i
    if start_index != -1 and end_index != -1:
        print([output[1] for output in outputs[start_index: end_index + 1]])
        print(len([output[1] for output in outputs[start_index: end_index + 1]]))
        outputs = outputs[0:start_index] + outputs[end_index + 1:]
        skip_by_tags(outputs, type)
    if start_index == -1 and end_index != -1:
        print(begin_label, "not found!")
    if end_index == -1 and start_index != -1:
        print(end_label, "not found!")

    return outputs


def skip_word_list(outputs, word_list_start, word_list_end, type):  # what does output look like
    start_index = -1
    end_index = -1
    for i, output in enumerate(outputs):
        if output[1] in word_list_start:  # or output[4] in word_list_end
            s_idx = word_list_start.index(output[1])
            output_list_start = [output[1] for output in outputs[i - s_idx:i - s_idx + 10]]
            # print(output_list_start)
            match_boolean_start = []
            if type == 'wl':
                match_boolean_start = [True for x in output_list_start if x in word_list_start]  # order does not matter
            elif type == 'ft':
                match_boolean_start = [True for i, x in enumerate(output_list_start) if
                                       x in word_list_start[i - 1:i + 2]]
                # the order matters and when filler words are missing, it need to be matched between a small range.
            if sum(match_boolean_start) > 5 and start_index == -1:
                # print(match_boolean_start)
                # print(sum(match_boolean_start))
                start_index = i - s_idx
        if output[1] in word_list_end:  # or output[4] in word_list_end
            e_idx = word_list_end.index(output[1])
            output_list_end = [output[1] for output in outputs[i - e_idx:i - e_idx + 10]]
            # print(output_list_end)
            match_boolean_end = []
            if type == 'wl':
                match_boolean_end = [True for x in output_list_end if x in word_list_end]
            elif type == 'ft':
                match_boolean_end = [True for i, x in enumerate(output_list_end) if
                                     x in word_list_end[i - 1:i + 2]]  # range matchint
                # maybe also combine the files for one speaker in one output and then process it for Bertha
                # Alfried
            if sum(match_boolean_end) > 5:
                # print(match_boolean_end)
                # print(sum(match_boolean_end))
                end_index = i - e_idx + 9
    print([output[1] for output in outputs[start_index: end_index + 1]])
    print(len([output[1] for output in outputs[start_index: end_index + 1]]))
    print(len(outputs))
    if start_index != -1 and end_index != -1:
        outputs = outputs[0:start_index] + outputs[end_index + 1:]
    print(len(outputs))
    return outputs


def timestamp_convert(ts):
    ts_list = str(ts).split('.')
    remaining_seconds = int(ts_list[0])
    ms = int(ts_list[1])
    hour = 0
    minute = 0
    if remaining_seconds >= 3600:
        hour = remaining_seconds // 3600
        remaining_seconds = remaining_seconds - (hour * 3600)
    if remaining_seconds >= 60:
        minute = remaining_seconds // 60
        remaining_seconds = remaining_seconds - (minute * 60)
    second = remaining_seconds
    # could try gmtime or other python time function
    timestamp = datetime.time(hour, minute, second, ms).strftime('%H:%M:%S.%f')  # [:-3] if use this, the clauses extract would not work.
    # print(timestamp)
    return timestamp



def word_filter(word_raw):
    """takes in words from annotations, get rid of extra puncturation and seperate them."""
    # TODO: these regex patterns have duplicates in the words_extract.py script

    punct = [',', '.', '!', '?']
    word_raw = word_raw.replace(":", "")
    word_raw = word_raw.replace('"', '')
    word_raw = word_raw.replace('…', '')  # there is such symbols?

    if any(re.search(filter_pattern, word_raw) for filter_pattern in filter_list):
        return ['']  # why do i put it here, can I put it outside? or should I use a empty check.co
    word_nopunct = []
    tmp = []
    tmp.append(word_raw)
    while tmp:
        word = tmp.pop(0)
        # later maybe think of a more elegant way of doing this
        if any(char in punct for char in word):
            for p in punct:
                if p in word:
                    for w in word.split(p):  # why not just get the, no wait it needs to be separated
                        if w != '':
                            tmp.append(w)
        else:
            word_nopunct.append(word)
    return word_nopunct
