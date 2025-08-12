"""helper methods for the swg project data processing"""
import datetime
import math
import re
from typing import List, Tuple

import pandas as pd
import regex
import os
import csv
import glob
import spacy
from ordered_set import OrderedSet
import textgrid
import pympi
import traceback

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
tags_to_type = {'[BEGIN-READING]': 'reading', '[BEGIN-WORD-LISTS]': 'word_lists', '[BEGIN-WORD-GAMES]': 'word_games'}

# three methods for inspecting TextGrid files

def find_special_character(path): # find the special characters in the TextGrid files
    tg_list = os.listdir(path)
    tg = filter(lambda tg: re.search(r'\.TextGrid', tg), tg_list)
    list_tg = list(tg)
    special = set()
    character_pattern = re.compile(r'[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî]')
    for tg in list_tg:
        try:
            file = open('{}/{}'.format(path, tg), "r")
            for line in file:
                for char in line:
                    if not re.search(character_pattern, char):
                        special.add(char)
            file.close()
        except FileNotFoundError:
            print(tg, "not found!")
            continue
    print(len(special))
    for char in list(special):
        print(char)
    # isalphanum() does not find the special characters


def find_skip_label(path):  # find the tags and check if they are valid and in pairs.
    tag_pattern = re.compile("\[[^\[\]]*\]")
    tags = list(tags_for_skipping.keys()) + list(tags_for_skipping.values())
    tag_pairs = list(tags_for_skipping.items())
    print("Checking tags in: ", path)
    tg_list = os.listdir(path)
    tg = filter(lambda tg: re.search(r'\.TextGrid', tg), tg_list)
    list_tg = list(tg) # sort the list
    for tg in list_tg:
        try:
            file = open('{}/{}'.format(path, tg), "r")
            tag_in_file = []
            for line in file:
                if "[BEGIN" in line or "[END" in line:
                    match = re.search(tag_pattern, line)
                    if match:
                        tag = match.group(0)  # get the [] tag
                        tag_in_file.append(tag)
                        if tag not in tags:
                            print("Incorrect tag：")
                            print(tg, ": " + line)
                    else:  # if there is no matching
                        print("Incorrect tag: ']' might be missing!")
                        print(tg, ": " + line)
                        print("")
            
            # Check tags in chronological order
            stack = []
            for i, tag in enumerate(tag_in_file):
                if tag in tags_for_skipping.keys():  # If it's a BEGIN tag
                    stack.append(tag)
                elif tag in tags_for_skipping.values():  # If it's an END tag
                    if not stack:
                        print(f"Unexpected END tag: {tag} at position {i}")
                        print(tg)
                    elif tags_for_skipping[stack[-1]] != tag:
                        print(f"Mismatched tags: Expected {tags_for_skipping[stack[-1]]}, but got {tag} at position {i}")
                        print(tg)
                    else:
                        stack.pop()
            
            if stack:
                print("Missing END tags:")
                print(tg)
                print(f"Tags in file: {tag_in_file}")
                print(f"Missing: {[tags_for_skipping[tag] for tag in stack]}")
            
            file.close()
        
        except FileNotFoundError:
            print(tg, "not found!")
            continue

def find_rel_label(path):
    tg_list = [p for p in os.listdir(path) if p.endswith('.TextGrid')] # sort the lists
    tag_pattern = re.compile("\[[^\[\]\d]*\]")
    for tg in tg_list:
        with open('{}/{}'.format(path, tg), "r") as file:
            tag_in_file = [] # dict tg: tags_list
            for line in file:
                match = re.findall(tag_pattern, line)
                if match:
                    tag_in_file.extend(match)
                elif "REL" in line or "ANT" in line:
                    print(tg)
                    print(line)
        # print(tag_in_file)

# csv methods for clauses and rel_clauses extract
def output_clauses_csv(extract_path, transcript_id, beg_hms, sym_seq, swg, var, pos, swg_vv, pos_vv, type_label, top_text):
    with open(extract_path, mode='a', newline="") as output_file:
        csv_writer = csv.writer(
            output_file,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([transcript_id, beg_hms, sym_seq, swg, var, pos, swg_vv, pos_vv, type_label, top_text])


def create_clauses_csv(extract_path):
    """
    If the csv file you want to output does not exist in your path, this function will create it.
    If the file already exists, it will be overwritten.
    """
    with open(extract_path, 'w', newline="") as create_the_csv:
        csv_writer = csv.writer(
            create_the_csv,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(
            ['trans_id', 'beg_hms', 'sym_seq', 'swg_clause', 'VAR', 'POS', 'swg_vv', 'pos_vv', 'speech_genre', 'swg_topic'])  # File_ID to Transcript_ID
    create_the_csv.close()


def create_target_pos_extract_csv(extract_path):
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
            ["trans_id", "before_clause", "before_clause_pos", "before_word", "before_word_pos", "target_word",
             "target_word_pos", "after_word", "after_word_pos", "after_clause", "after_clause_pos"])
    create_the_csv.close()

def output_target_pos_extract_csv(extract_path, trans_id, before_clause, before_clause_pos, before_word, before_word_pos, target_word,
                       target_word_pos, after_word, after_word_pos, after_clause, after_clause_pos):
    with open(extract_path, mode='a', newline="") as output_file:
        csv_writer = csv.writer(
            output_file,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([trans_id, before_clause, before_clause_pos, before_word, before_word_pos, target_word,
                       target_word_pos, after_word, after_word_pos, after_clause, after_clause_pos])

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

def get_variant_match(lex_table):
    variant_match = dict()
    for r in zip(lex_table['word_variant'], lex_table['word_standard'], lex_table['word_vars'], lex_table['POS_tag'],lex_table['word_lemma']):
        # dict with variant as key.
        # if no match tag the thing
        v_pattern = compile_pattern(r[0], r[2]) # variant pattern
        if v_pattern not in variant_match.keys():
            variant_match[v_pattern] = []
        variant_match[v_pattern].append(r)
    for w_var, w_val in variant_match.items():
        if len(w_val) > 1:
            print(w_var, w_val)
    return variant_match


def lemmatize_SWG(variant_match, word):
    nlp = spacy.load("de_core_news_sm")
    lemma_list = set()
    for p in variant_match.keys():  # p is the pattern
        if p.search(word) is not None:  # .lower()
            for values in variant_match[p]:
                w_lemma = values[4]  # word lemma
                # print("lemma: ", w_lemma)
                lemma_list.add(w_lemma)
    if not lemma_list:
        for processed_word in nlp(word):
            lemma_list.add(processed_word.lemma_)
            # print("lemmatizer lemma: ", processed_word.lemma_)
    return list(lemma_list)


def get_word_standard(variant_match, word):
    std_list = set()
    no_match = True

    for p in variant_match.keys():  # p is the pattern
        if p.search(word) is not None:  # .lower()
            no_match = False
            replace = True
            for values in variant_match[p]:
                if "*" in values[0] and "*" not in values[1]:
                    replace = False
                w_var = values[0].replace("*", "")  # word variant
                w_std = values[1].replace("*", "")  # word standard
                if std_list:
                    tmp_std = set()
                    while std_list:
                        s = std_list.pop()
                        if p.search(s) is not None:
                            if replace:
                                std = s.replace(w_var, w_std)
                            else:
                                std = values[1]
                            tmp_std.add(std)
                        else:
                            tmp_std.add(s)
                    std_list.update(tmp_std)
                else:
                    if replace:
                        std = word.replace(w_var, w_std)
                    else:
                        std = values[1]
                    std_list.add(std)

    if no_match:
        std_list.add(word)
    else:
        if len(std_list) > 1:
            print(word, "std: ", " ".join(std_list))
    return std_list


def ddm_tagger(variant_match, gehen_variants, pos_tagger, word):
    # regular ddm tagging
    std_list = set()
    ddm_list = OrderedSet()
    pos_list = set()
    no_match = True

    for p in variant_match.keys():  # p is the pattern
        if any("IRV" in d for d in ddm_list):
            # print(" ".join(ddm_list))
            break
        if p.search(word) is not None:  # .lower()
            no_match = False
            replace = True
            for values in variant_match[p]:
                if "*" in values[0] and "*" not in values[1]:
                    replace = False
                w_var = values[0].replace("*", "")  # word variant
                w_std = values[1].replace("*", "")  # word standard
                if std_list:
                    tmp_std = set()
                    while std_list:
                        s = std_list.pop()
                        if p.search(s) is not None:
                            if replace:
                                std = s.replace(w_var, w_std)
                            else:
                                std = values[1]
                            tmp_std.add(std)
                        else:
                            tmp_std.add(s)
                    std_list.update(tmp_std)
                else:
                    if replace:
                        std = word.replace(w_var, w_std)
                    else:
                        std = values[1]
                    std_list.add(std)
                if isinstance(values[2], float) and math.isnan(values[2]):  # check for empty var_code
                    # ddm_list.add(' ')  # do nothing
                    print(values)
                    print("empty var_code")
                elif values[2] not in ddm_list:
                    # TODO: check this
                    ddm_list.update(str(values[2]).split())  # split the var_code
                pos_list.add(values[3])
    if no_match:
        standard = word
        ddm = " "
        pos = pos_tagger.tag([word])[0][1]
    else:
        standard = " ".join(std_list)
        if len(std_list) > 1:
            print(word, "std: ", standard)
        ddm = " ".join(str(d) for d in ddm_list)
        # maybe here is the problem
        if any("SAF5" in d for d in ddm_list):
            # print(ddm) # right, this
            for g_pattern in gehen_variants:
                if g_pattern.search(word) is not None:
                    ddm = ddm.replace("SAF5d", "")
                    ddm = ddm.replace("SAF5s", "")
        pos = " ".join(str(p) for p in pos_list)
    return standard, ddm, pos


def tag_pos_for_word(word, variant_match, pos_tagger):
    pos_list = set()
    no_match = True

    for p in variant_match.keys():  # p is the pattern
        if p.search(word) is not None:  # .lower()
            no_match = False
            for values in variant_match[p]:
                pos_list.add(values[3])
    if no_match:
        pos = pos_tagger.tag([word])[0][1]
    else:
        pos = " ".join(str(p) for p in pos_list)
    return pos


def get_gehen_variants(lex_table):
    gehen_variants = set()
    locations = lex_table.loc[lex_table['word_lemma'] == 'gehen']
    # TODO: do the same for "stehen", condition would be exactly te same
    for gehen_var in zip(locations['word_variant'], locations['word_vars']):
        if "SAF5" not in gehen_var[1]:
            g_pattern = compile_pattern(gehen_var[0], gehen_var[1])
            gehen_variants.add(g_pattern)
    return gehen_variants


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
        lex = pd.read_excel(lex_table_path, engine='openpyxl', index_col=None, header=0)
    else:
        lex = pd.read_csv(lex_table_path, index_col=None, header=0)
    lex.dropna(axis='columns', how='all', inplace=True)
    return lex


# def skip_by_tags(outputs, type):
#     start_index = -1
#     end_index = -1
#     if type == 'r':
#         begin_label = "[BEGIN-READING]"
#         end_label = "[END-READING]"
#     elif type == 'wl':
#         begin_label = "[BEGIN-WORD-LISTS]"
#         end_label = "[END-WORD-LISTS]"
#     elif type == 'wg':
#         begin_label = "[BEGIN-WORD-GAMES]"
#         end_label = "[END-WORD-GAMES]"
#     for i, output in enumerate(outputs):
#         if begin_label in output[1] and start_index == -1:
#             start_index = i
#         if end_label in output[1] and end_index == -1:
#             end_index = i
#     if start_index != -1 and end_index != -1:
#         # print([output[1] for output in outputs[start_index: end_index + 1]])
#         # print(len([output[1] for output in outputs[start_index: end_index + 1]]))
#         modify_type = outputs[start_index:end_index + 1]
#         outputs = outputs[0:start_index] + outputs[end_index + 1:]
#         skip_by_tags(outputs, type)
#     if start_index == -1 and end_index != -1:
#         print(begin_label, "not found!")
#     if end_index == -1 and start_index != -1:
#         print(end_label, "not found!")
#
#     return outputs


def skip_by_tags(outputs, type): # TODO: rename the function to indicate that it's to get the type_label
    start_index = -1
    end_index = -1
    if type == 'r':
        begin_label = "[BEGIN-READING]"
        end_label = "[END-READING]"
        type_label = tags_to_type[begin_label]
    elif type == 'wl':
        begin_label = "[BEGIN-WORD-LISTS]"
        end_label = "[END-WORD-LISTS]"
        type_label = tags_to_type[begin_label]
    elif type == 'wg':
        begin_label = "[BEGIN-WORD-GAMES]"
        end_label = "[END-WORD-GAMES]"
        type_label = tags_to_type[begin_label]

    for i, output in enumerate(outputs):
        if begin_label in output[1] and start_index == -1:
            start_index = i
        if end_label in output[1] and end_index == -1:
            end_index = i

    if start_index != -1 and end_index != -1:
        # Change the second to last element in the outputs list to the corresponding type_label
        # print("before: ", outputs[start_index:end_index + 1])

        # last_output = outputs[start_index:end_index + 1][-1]
        for i in range(start_index, end_index):
            outputs[i][-2] = type_label
        outputs = outputs[:start_index] + outputs[start_index+1:end_index] + outputs[end_index+1:] # remove the first and last label
        # print("after: ", outputs[start_index:end_index + 1])
        # print("entire: ", outputs)
        # Recurse to handle other occurrences of [BEGIN] and [END]
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
    if ts < 0:
        ts = 0  # Handle negative case just in case

    # Separate the integer and fractional parts of the seconds
    fractional_seconds, integer_seconds = math.modf(ts)

    # Convert fractional seconds to microseconds
    microseconds = int(round(fractional_seconds * 1_000_000))

    remaining_seconds = int(integer_seconds)

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
    # The fourth argument to datetime.time is microseconds
    timestamp = datetime.time(hour, minute, second, microseconds).strftime('%H:%M:%S.%f')
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

def validate_textgrid_file(file_path: str) -> bool:
    """
    Validate TextGrid file format before attempting to parse.
    
    Args:
        file_path (str): Path to TextGrid file
        
    Returns:
        bool: True if file appears valid, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if not first_line == 'File type = "ooTextFile"':
                print(f"Invalid TextGrid header in {file_path}")
                return False
                
            second_line = f.readline().strip()
            if not second_line == 'Object class = "TextGrid"':
                print(f"Invalid TextGrid object class in {file_path}")
                return False
                
            return True
            
    except Exception as e:
        print(f"Error validating {file_path}: {str(e)}")
        return False

def validate_textgrid_content(file_path: str) -> bool:
    """
    Check if file has valid TextGrid content.
    
    Args:
        file_path (str): Path to TextGrid file
        
    Returns:
        bool: True if file has valid TextGrid format, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_lines = [next(f).strip() for _ in range(2)]
            return (first_lines[0] == 'File type = "ooTextFile"' and 
                   first_lines[1] == 'Object class = "TextGrid"')
    except Exception as e:
        print(f"Error validating {file_path}: {str(e)}")
        return False

def read_textgrid_and_match_tiers(file_path: str, overlap_threshold: float = 0.7) -> List[Tuple[str, str, float, float]]:
    """
    Read TextGrid file and match intervals between SWG and TOP tiers based on overlap.
    If no TOP tier exists, returns SWG intervals with empty TOP text.
    
    Args:
        file_path (str): Path to TextGrid file
        overlap_threshold (float): Minimum overlap required to match intervals (0-1)
    
    Returns:
        List[Tuple[str, str, float, float]]: List of matched intervals (swg_text, top_text, start_time, end_time)
    """
    # Validate file before processing
    if not validate_textgrid_file(file_path):
        print(f"Skipping invalid TextGrid file: {file_path}")
        return []
        
    try:
        # Try to read file with different encodings
        for encoding in ['utf-8', 'utf-16', 'latin1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    tg = textgrid.TextGrid.fromFile(file_path)
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading {file_path} with {encoding} encoding: {str(e)}")
                continue
        else:
            print(f"Could not read {file_path} with any supported encoding")
            return []

        swg_tier = None
        top_tier = None
        
        # Find SWG and TOP tiers
        for tier in tg.tiers:
            if tier.name == 'SWG':
                swg_tier = tier
            elif tier.name == 'TOP':
                top_tier = tier
            if swg_tier and top_tier:
                break
                
        if not swg_tier:
            print(f"No SWG tier found in {file_path}")
            return []
            
        matched_intervals = []
        
        if not top_tier:
            # If no TOP tier, just return SWG intervals with empty TOP text
            print(f"No TOP tier found in {file_path}, processing SWG tier only")
            for swg_interval in swg_tier:
                if not swg_interval.mark.strip():  # Skip empty intervals
                    continue
                matched_intervals.append((
                    swg_interval.mark,
                    "",  # Empty TOP text
                    swg_interval.minTime,
                    swg_interval.maxTime
                ))
            return matched_intervals

        # If we have both tiers, do the matching
        top_idx = 0
        top_len = len(top_tier)
        
        # For each SWG interval, find matching TOP interval
        for swg_interval in swg_tier:
            if not swg_interval.mark.strip():  # Skip empty intervals
                continue
                
            swg_start = swg_interval.minTime
            swg_end = swg_interval.maxTime
            swg_duration = swg_end - swg_start
            
            # Look for overlapping TOP interval
            while top_idx < top_len:
                top_interval = top_tier[top_idx]
                
                # If TOP interval is past current SWG interval, move to next SWG
                if top_interval.minTime > swg_end:
                    break
                    
                # Calculate overlap
                overlap_start = max(swg_start, top_interval.minTime)
                overlap_end = min(swg_end, top_interval.maxTime)
                
                if overlap_end > overlap_start:  # If there is overlap
                    overlap_duration = overlap_end - overlap_start
                    overlap_ratio = overlap_duration / swg_duration
                    
                    if overlap_ratio >= overlap_threshold:
                        matched_intervals.append((
                            swg_interval.mark,
                            top_interval.mark or "",  # Use empty string for empty marks
                            swg_start,
                            swg_end
                        ))
                        break
                
                # Move to next TOP interval if current one ends before SWG interval
                if top_interval.maxTime < swg_end:
                    top_idx += 1
                else:
                    break

        return matched_intervals

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        traceback.print_exc()
        return []

def clean_empty_column_rows(extract_path: str, column_name: str, output_path: str = None) -> pd.DataFrame:
    """
    Read an extract CSV and remove rows where specified column is empty.
    
    Args:
        extract_path (str): Path to the extract CSV file
        column_name (str): Name of the column to check for empty values
        output_path (str, optional): Path to save cleaned CSV. If None, returns DataFrame without saving
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with empty rows removed
        
    Example:
        # Remove rows where 'word_lemma' is empty
        clean_df = clean_empty_column_rows('path/to/extract.csv', 'word_lemma', 'path/to/output.csv')
    """
    try:
        # Read the CSV file
        df = pd.read_csv(extract_path, encoding='utf-8', keep_default_na=False)
        
        # Verify column exists
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in the extract")
            
        # Get initial row count
        initial_count = len(df)
        
        # Remove rows where the specified column is empty
        df = df[df[column_name].str.strip() != '']
        
        # Get number of rows removed
        removed_count = initial_count - len(df)
        
        print(f"Removed {removed_count} rows with empty values in column '{column_name}'")
        print(f"Remaining rows: {len(df)}")
        
        # Save to file if output path specified
        if output_path:
            df.to_csv(output_path, index=False)
            print(f"Saved cleaned extract to: {output_path}")
            
        return df
        
    except Exception as e:
        print(f"Error processing extract: {str(e)}")
        raise