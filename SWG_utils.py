"""helper methods for the swg project data processing"""
import datetime
import re
import pandas as pd
import regex


def add_previous_following(extract_path, extract_type):
    df_extract = read_extract(extract_path)
    # rename the columns
    df_extract['previous_word'] = ''
    df_extract['following_word'] = ''
    df_extract['previous_seg'] = ''
    df_extract['following_seg'] = ''
    if extract_type == 'phone':
        df_extract = df_extract[['trans_id', 'word_start_time', 'word_end_time', 'word_SWG', 'previous_word','following_word',
           'seg_number', 'seg_start_time', 'seg_end_time', 'segment_SWG',
           'diphthong_orthography', 'previous_seg', 'following_seg', 'var_code', 'word_German', 'word_lemma', 'word_stem', 'POS_tag']]
    if extract_type == 'formant':
        df_extract = df_extract[['trans_id', 'time', 'F1(Hz)', 'F2(Hz)', 'zeroed_word_start_time', 'zeroed_word_end_time', 'normalized_time_word', 'word_start_time',
          'word_end_time', 'word_duration', 'word_SWG', 'previous_word', 'following_word', 'seg_number', 'zeroed_seg_start_time', 'zeroed_seg_end_time', 'normalized_time_seg', 'seg_start_time',
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

            if "_" not in df_extract.iloc[i - 1]['segment_SWG']:
                previous_seg = df_extract.iloc[i - 1]['segment_SWG']

            if last_time != current_time: # time interval changed
                if "<" not in last_word:
                    previous_word = last_word
                else:
                    previous_word = "#"
                last_time = current_time
                last_word = current_word

        if i + 1 < len(df_extract):
            # print("after", df_extract.iloc[i+1]['segment_SWG'])
            if "_" not in df_extract.iloc[i + 1]['segment_SWG']:
                following_seg = df_extract.iloc[i + 1]['segment_SWG']
        else:
            following_word = "#"
            following_seg = "#"
        if next_word_index < len(df_extract):
            following_time = df_extract.iloc[next_word_index]['word_start_time']
            while following_time == current_time and next_word_index < len(df_extract)-1:
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


def read_extract(extract_path):  # could put in util
    df_extract = pd.read_csv(
        extract_path, encoding='utf-8', header=0, keep_default_na=False)
    df_extract = df_extract.replace('nan', '') # in case there are 'nan'

    return df_extract


def compile_pattern(word_pattern, ):  # pattern is lowercase
    pattern = word_pattern.strip()
    pattern = pattern.replace("\ufeff", "")
    pattern = pattern.replace("???", "")
    pattern = pattern.replace(" ","")
    pattern = pattern.replace("xxx","")
    if pattern.startswith("*"):
        pattern = '.*' + pattern[1:]
    else:
        pattern = "^" + pattern
    if pattern.endswith("*"):
        pattern = pattern[:-1] + '.*'
    else:
        pattern = pattern + "$"
    pattern = pattern.replace("[ge]", "[ge?]")
    pattern = pattern.replace("[", "\[")  # escape this special symbol for matching
    pattern = pattern.replace("]", "\]")
    # replace all ge to ge? is a bad idea... so maybe do something special with the saf5
    # saf5 # maybe generate doch dieser neue line/pattern for the [ge] words
    # compile variant into pattern
    compiled_pattern = regex.compile(pattern)
    # what about re?
    return compiled_pattern


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
        print([output[1] for output in outputs[start_index: end_index+1]])
        print(len([output[1] for output in outputs[start_index: end_index+1]]))
        outputs = outputs[0:start_index] + outputs[end_index+1:]
        skip_by_tags(outputs, type)
    if start_index == -1 and end_index != -1:
        print(begin_label, "not found!")
    if end_index == -1 and start_index != -1:
        print(end_label, "not found!")

    return outputs


def skip_word_list(outputs, word_list_start, word_list_end, type): # what does output look like
    start_index = -1
    end_index = -1
    for i, output in enumerate(outputs):
        if output[1] in word_list_start:  # or output[4] in word_list_end
            s_idx = word_list_start.index(output[1])
            output_list_start = [output[1] for output in outputs[i-s_idx:i-s_idx+10]]
            #print(output_list_start)
            match_boolean_start = []
            if type == 'wl':
                match_boolean_start = [True for x in output_list_start if x in word_list_start]  # order does not matter
            elif type =='ft':
                match_boolean_start = [True for i, x in enumerate(output_list_start) if x in word_list_start[i-1:i+2]]
                # the order matters and when filler words are missing, it need to be matched between a small range.
            if sum(match_boolean_start) > 5 and start_index == -1:
                #print(match_boolean_start)
                #print(sum(match_boolean_start))
                start_index = i-s_idx
        if output[1] in word_list_end:  # or output[4] in word_list_end
            e_idx = word_list_end.index(output[1])
            output_list_end = [output[1] for output in outputs[i-e_idx:i-e_idx+10]]
            #print(output_list_end)
            match_boolean_end =[]
            if type == 'wl':
                match_boolean_end = [True for x in output_list_end if x in word_list_end]
            elif type == 'ft':
                match_boolean_end = [True for i, x in enumerate(output_list_end) if x in word_list_end[i-1:i+2]] # range matchint
                # maybe also combine the files for one speaker in one output and then process it for Bertha
                # Alfried
            if sum(match_boolean_end) > 5:
                #print(match_boolean_end)
                #print(sum(match_boolean_end))
                end_index = i-e_idx+9
    print([output[1] for output in outputs[start_index: end_index+1]])
    print(len([output[1] for output in outputs[start_index: end_index+1]]))
    print(len(outputs))
    if start_index != -1 and end_index != -1:
        outputs = outputs[0:start_index] + outputs[end_index+1:]
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
    timestamp = datetime.time(hour, minute, second, ms).strftime('%H:%M:%S.%f')[:-3]
    # print(timestamp)
    return timestamp


def word_filter(word_raw):
    """takes in words from annotations, get rid of extra puncturation and seperate them."""
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
    filter_list = [person_name_l, person_name_r, hyphen, hyphen_2, double_dash, dash_l, dash_r, dot_2, question_2,
                   quo_2]
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
                        if w is not '':
                            tmp.append(w)
        else:
            word_nopunct.append(word)
    return word_nopunct