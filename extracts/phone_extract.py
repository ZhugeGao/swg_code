"""
Author: Nianheng Wu, Zhuge Gao
xjtuwunianheng@gmail.com, Eberhard Karls Universität Tübingen
zhuge.gao@student.uni-tuebingen.de
"""
import math
import os
import csv
import string

import textgrid
import traceback
import re
from nltk import CoreNLPParser
import pandas as pd
from SWG_utils import compile_pattern, read_lex_table, word_filter, add_previous_following


class Transform:

    def __init__(self, rootpath, outputpath, lex):  # maps
        self.rootpath = rootpath
        self.outputpath = outputpath
        self.lex_table = lex
        self.tags = {'[BEGIN-READING]': '[END-READING]', '[BEGIN-WORD-LISTS]': '[END-WORD-LISTS]',
                     '[BEGIN-WORD-GAMES]': '[END-WORD-GAMES]'}

    def start(self):
        try:
            os.chdir(self.rootpath)
        except FileNotFoundError:
            print("Path not found:", self.rootpath)
        if not os.path.exists(output_path):
            self.create_a_csv()
        self.get_file_list()

    def get_file_list(self):
        file_list = [file for file in os.listdir(self.rootpath) if file.endswith('.TextGrid')]
        file_list = sorted(file_list, key=lambda x: (int(x.split('-')[0][1:]), int(x.split('-')[3]), int(x.split('_')[1][:-9]))) # sort by speaker id and the split number
        self.read_from_textgrid(file_list)

    def read_from_textgrid (self, file_list):
        pos_tagger = CoreNLPParser('http://localhost:9002', tagtype='pos')
        table = str.maketrans(dict.fromkeys(string.punctuation.replace("[\\]","")))
        variant_match = dict()
        for r in zip(self.lex_table['word_variant'], self.lex_table['word_standard'], self.lex_table['word_vars'],
                     self.lex_table['POS_tag'], self.lex_table['word_lemma'], self.lex_table['word_stem']):
            # dict with variant as key.
            # if no match tag the thing
            v_pattern = compile_pattern(r[0], r[2])
            if v_pattern not in variant_match.keys():
                variant_match[v_pattern] = []
            # else:
            #     print(v_pattern)
            variant_match[v_pattern].append(r)

        gehen_variants = set()
        locations = self.lex_table.loc[self.lex_table['word_lemma'] == 'gehen']
        for gehen_var in zip(locations['word_variant'], locations['word_vars']):
            if "SAF5" not in gehen_var[1]:
                g_pattern = compile_pattern(gehen_var[0], gehen_var[1])
                gehen_variants.add(g_pattern)

        words_h = []
        skip_begin = False
        skip_begin_tag = ""
        skip_end_file = ""
        for each_file_name in file_list:
            original_words = read_txt(self.rootpath, each_file_name)
            context = []
            rel = False

            tag_pattern = re.compile("\[[^\[\]]*\]")
            # collect all the tags
            tags = []
            for i, ow in enumerate(original_words):
                find_tag = re.search(tag_pattern, ow)
                # there could be more than one [REL] tag in there.  S016-17-I-1-Manni_692. ['der', '[REL]', 'halt', 'e', 'groß---', '-eh-', 'dessen', '[REL', 'Garten', 'groß']
                if find_tag:
                    tag = find_tag.group(0)
                    tags.append(tag)
                    # print(tag)
                elif "[" in ow or "]" in ow:
                    print("incorrect tag in:", each_file_name)
                    print(ow)
                    print(original_words)
            if tags:
                for tag in tags:
                    if tag == '[REL]':
                        rel = True
                        context.append(original_words[i-1].translate(table))
                    elif tag in self.tags.keys():
                        print(each_file_name)
                        print("Skipping:", tag)
                        skip_begin = True
                        skip_begin_tag = tag
                    elif tag in self.tags.values():
                        if tag == self.tags[skip_begin_tag]:
                            print(each_file_name)
                            print("Skipping:", tag)
                            skip_begin = False  # this will not skip the file which contains the end tag
                            skip_end_file = each_file_name  # skip the file that contains the end tag
                        else:
                            print("Wrong end tag:", tag)
                    # maybe should skip before the Aligner. Just have one that operates on TextGrid and WAV then no skipping in extract
            if skip_begin:
                print("Skipping:", original_words)
                continue
            if each_file_name == skip_end_file:  #
                print("Skipping:", original_words)
                continue
            # print("filename:", each_file_name)
            interval_num = 0

            file_path = self.rootpath + each_file_name
            try:
                file_textgrid_obj = textgrid.TextGrid.fromFile(file_path)
            except ValueError:
                print(each_file_name +'value error has occured')
                os.rename(self.rootpath + +each_file_name, working_directory + 'valueError/' + each_file_name)
                continue
            tier_list = file_textgrid_obj.tiers

            for each_tier in tier_list:
                if each_tier.name == 'words':
                    tier_words = each_tier
                    intervals_words = tier_words.intervals
                elif each_tier.name == 'segments':
                    tier_segments = each_tier
                    intervals_segments = tier_segments.intervals

            count = 0
            current_minTime = 0
            seg_num = 1
            diphthong_num = 0
            diphthong_dict = {'a͜i': {'ua', 'ai', 'êi', 'ei', 'âi', 'aî', 'ãi'}, 'a͜u': {'au', 'âu'}, 'ɔ͜y': {'ôi', 'eu', 'äu', 'oi', 'êu', 'eü', 'oî'}}
            # print(each_file_name)
            try:
                for i, each_word in enumerate(intervals_words):
                    add_rel = False

                    word_start_time = each_word.minTime
                    word_end_time = each_word.maxTime
                    word_mark = each_word.mark
                    if word_mark not in original_words and "<" not in word_mark:
                        match = [ow.translate(table) for ow in original_words if word_mark == clean_word(ow)]
                        if not match:
                            words_h.append((word_mark, original_words, each_file_name))
                            continue  # some words just turned to h. for unknown reason
                            # investigate
                        else:
                            word_mark = match[0].replace("[ge]", "")
                    if rel:
                        if word_mark == context[0] or word_mark == clean_word(context[0]):
                            add_rel = True  # maybe not do it here is better
                            rel = False  # avoid
                            if "wo" in word_mark:
                                rel_var = " RELd"
                            elif "als" in word_mark or word_mark.startswith("d") or word_mark.startswith("wel") or word_mark.startswith("jed"):
                                rel_var = " RELs"
                            elif ("was" in word_mark) or ("wie" in word_mark) or ("wer" in word_mark):
                                rel_var = " RLOs"
                            else:
                                rel_var = " UNK"

                    std_list = set()
                    ddm_list = set()
                    pos_list = set()
                    lemma_list = set()
                    stem_list = set()
                    no_match = True

                    for p in variant_match.keys():
                        if p.search(word_mark) is not None:
                            if any("IRV" in d for d in ddm_list):
                                # print(" ".join(ddm_list))
                                break
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
                                        std = word_mark.replace(w_var, w_std)
                                    else:
                                        std = values[1]
                                    std_list.add(std)
                                lemma = values[4]
                                stem = values[5]
                                lemma_list.add(lemma)
                                stem_list.add(stem)
                                # if "SAF5" in values[2]:
                                #     print(word_mark)
                                #     if "ge"
                                if isinstance(values[2], float) and math.isnan(values[2]):  # check for empty var_code
                                    ddm_list.add(' ')  # do nothing
                                else:
                                    ddm_list.add(values[2])  # should be set
                                pos_list.add(values[3])
                    if no_match:
                        word_german = word_mark
                        var_code = " "
                        pos_tag = pos_tagger.tag([word_german])[0][1]
                        word_lemma = word_german
                        word_stem = " "
                    else:
                        var_code = " ".join(str(d) for d in ddm_list)
                        if any("SAF5" in d for d in ddm_list):
                            for g_pattern in gehen_variants:
                                if g_pattern.search(word_mark) is not None:
                                    var_code = var_code.replace("SAF5d", "")
                                    var_code = var_code.replace("SAF5s", "")
                        word_german = " ".join(std_list)
                        if len(std_list) > 1:
                            print(word_mark, "std: ", word_german)
                        word_lemma = " ".join(lemma_list)
                        word_stem = " ".join(stem_list)
                        pos_tag = " ".join(str(p) for p in pos_list)
                    if add_rel:
                        var_code = var_code + rel_var
                        var_code = var_code.strip()
                    try:
                        vowel_orthography = find_two_vowel(word_mark)
                        while (intervals_segments[interval_num].minTime >= word_start_time) & \
                                (intervals_segments[interval_num].maxTime <= word_end_time):
                            segment_start_time = intervals_segments[interval_num].minTime
                            segment_end_time = intervals_segments[interval_num].maxTime
                            segment_mark = intervals_segments[interval_num].mark

                            diphthong_orthography = " "
                            if len(segment_mark) == 3 and "_" not in segment_mark and "ː" not in segment_mark:
                                # print(segment_mark)
                                # print(word_mark)
                                if vowel_orthography[diphthong_num].lower() in diphthong_dict[segment_mark]:
                                    diphthong_orthography = vowel_orthography[diphthong_num]
                                elif any(vow_bigram.lower() in diphthong_dict[segment_mark] for vow_bigram in vowel_orthography):
                                    for vow_bigram in vowel_orthography:
                                        if vow_bigram.lower() in diphthong_dict[segment_mark]:
                                            diphthong_orthography = vow_bigram
                                else:
                                    print(vowel_orthography)
                                    print(vowel_orthography[diphthong_num])
                                    print(word_mark)
                                    print(segment_mark)
                                diphthong_num += 1
                            if word_start_time > current_minTime:
                                seg_num = 1
                                diphthong_num = 0
                                current_minTime = word_start_time

                            output_flag = False
                            if word_mark not in original_words:
                                match_ow = [ow for ow in original_words if word_mark == clean_word(ow)]
                                if match_ow:
                                    word_original = match_ow[0]
                                    if word_filter(word_original)[0]:
                                        output_flag = True
                            else:
                                output_flag = True
                            if var_code.strip():  # quick fix
                                output_flag = True
                            if output_flag:
                                self.output_as_csv(each_file_name[:-9], word_start_time, word_end_time, word_mark,
                                                   seg_num, segment_start_time, segment_end_time, segment_mark,
                                                   diphthong_orthography, var_code, word_german, word_lemma, word_stem,
                                                   pos_tag)
                            else:
                                if "<" not in word_mark:
                                    print("not a word: ", each_file_name[:-9], word_start_time, word_end_time, word_mark, var_code, word_german)
                            seg_num += 1
                            interval_num += 1
                    except IndexError:
                        interval_num = 0
                    if word_mark != '<P>':
                        count += 1

            except AttributeError as e:
                print(each_file_name+': tier words is empty or does not exist ')
                traceback.print_tb(e.__traceback__)
        with open('words_tran_error.txt', mode='w', newline="\n") as f:
            for item in words_h:
                f.write(str(item) + "\n")

    def output_as_csv (self, trans_id, word_start_time, word_end_time, word_swg, seg_number, segment_start_time, segment_end_time, segment_swg, diphthong_orthography, var_code, word_german, word_lemma, word_stem, pos_tag):
        with open(output_path, mode = 'a', newline="") as output_file:
            csv_writer = csv.writer(output_file, delimiter=',', quotechar ='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow([trans_id, word_start_time, word_end_time, word_swg, seg_number,
                                 segment_start_time, segment_end_time, segment_swg, diphthong_orthography, var_code, word_german, word_lemma, word_stem, pos_tag]) # change the field

    def create_a_csv (self):
        """
        If the csv file you want to output does not exist in your path, this function will create it.
        """
        with open (output_path, 'w', newline="") as create_the_csv:
            csv_writer = csv.writer(create_the_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['trans_id', 'word_start_time', 'word_end_time', 'word_SWG', 'seg_number', 'seg_start_time', 'seg_end_time', 'segment_SWG', 'diphthong_orthography', 'var_code', 'word_German', 'word_lemma', 'word_stem', 'POS_tag'])
        create_the_csv.close()


def read_txt(source_path, file_name):
    with open(source_path+file_name[:-9]+'.txt', 'r', newline="") as f:
        phrases = f.read().split()
    return phrases


def clean_word(word):
    word = word.replace("#", "")
    word = word.replace('ê', 'e')
    word = word.replace('ã', 'a')
    word = word.replace('â', 'a')
    word = word.replace('ô', 'o')
    word = word.replace('ß', 'ss')
    word = word.replace('ä', 'ae')
    word = word.replace('ö', 'oe')
    word = word.replace('ü', 'ue')
    word = word.replace('-', '')
    word = word.replace('!', '')
    word = word.replace('?', '')
    word = word.replace(',', '')
    word = word.replace('.', '')
    word = word.replace('"', '')
    word = word.replace("'", '')
    word = word.replace('{', '')
    word = word.replace('}', '')
    word = re.sub("[\[].*?[\]]", "", word)

    return word


def find_two_vowel(word):
    vowel = is_vowel(word)
    two_vowels = []
    for i, vow_tup in enumerate(zip(vowel[:-1], vowel[1:])):
        if vow_tup == (True, True):
            two_vowels.append(word[i:i+2])
    return two_vowels


def is_vowel(word):
    tokens = list(word.lower())
    vowel = ['a', 'e', 'i', 'o', 'u', 'ä', 'ö', 'ü', 'û', 'ô',  'ĩ', 'â', 'õ', 'ẽ', 'ã', 'ê', 'à', 'é', 'ë', 'î']
    vowel_boolean = [True if t in vowel else False for t in tokens]
    return vowel_boolean


if __name__ == '__main__':
    working_directory = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    speaker_done_path = {'panel': [working_directory + 'done_panel/1982/', working_directory + 'done_panel/2017/'], 'twin': [working_directory + 'done_twin/']}
    # speaker_done_path = {'twin': [working_directory + 'test/']}
    # 'trend': [working_directory + 'done_trend/']
    # 'panel': [working_directory + 'done_panel/1982/', working_directory + 'done_panel/2017/']
    speaker_list = ['panel', 'twin']
    extract_type = 'phone'
    date = '20201107'
    types = 'noSocialInfo' + '.csv'
    lex_path = working_directory + 'SG-LEX 06nov2020.csv'
    lex = read_lex_table(lex_path)
    for speaker in speaker_list:
        output_path = working_directory + 'SWG_'+speaker+'_'+extract_type+'_'+date+types
        for source_path in speaker_done_path[speaker]:
            transform = Transform(source_path, output_path, lex)
            transform.start()
        add_previous_following(output_path, extract_type)