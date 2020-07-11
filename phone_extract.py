"""
Author: Nianheng Wu
xjtuwunianheng@gmail.com, Eberhard Karls Universität Tübingen
"""
import math
import os
import errno
import csv
import string

import textgrid
import traceback
import re
from nltk import CoreNLPParser
import pandas as pd
from SWG_utils import compile_pattern, read_lex_table, word_filter


class Transform:

    def __init__(self, rootpath, outputpath, lex): # maps
        self.rootpath = rootpath
        self.outputpath = outputpath
        self.lex_table = lex
        self.tags = {'[BEGIN-READING]': '[END-READING]', '[BEGIN-WORD-LISTS]': '[END-WORD-LISTS]',
                     '[BEGIN-WORD-GAMES]': '[END-WORD-GAMES]'}

    def start(self):
        try:
            os.chdir(self.rootpath)
        except FileNotFoundError:
            print(errno.EPERM)
        if not os.path.exists(output_path):
            self.create_a_csv()
        self.get_file_list()

    def get_file_list(self):
        file_list = [file for file in os.listdir(self.rootpath) if file.endswith('.TextGrid')]
        file_list = sorted(file_list, key=lambda x: (int(x.split('-')[0][1:]), int(x.split('-')[3]), int(x.split('_')[1][:-9]))) # sort by speaker id and the split number
        self.read_from_textgrid(file_list)

    def read_from_textgrid (self, file_list):
        pos_tagger = CoreNLPParser('http://localhost:9002', tagtype='pos')
        table = str.maketrans(dict.fromkeys(string.punctuation))
        variant_match = dict()
        for r in zip(self.lex_table['word_variant'], self.lex_table['word_standard'], self.lex_table['word_vars'],
                     self.lex_table['POS_tag']):
            # dict with variant as key.
            # if no match tag the thing
            v_pattern = compile_pattern(r[0])
            if v_pattern not in variant_match.keys():
                variant_match[v_pattern] = []
            # else:
            #     print(v_pattern)
            variant_match[v_pattern].append(r)

        gehen_variants = set()
        locations = self.lex_table.loc[self.lex_table['word_lemma'] == 'gehen']
        for gehen_var in zip(locations['word_variant'], locations['word_vars']):
            if "SAF5" not in gehen_var[1]:
                g_pattern = compile_pattern(gehen_var[0])
                gehen_variants.add(g_pattern)

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
                    print("missed tag in:", each_file_name)
                    print(ow)
                    print(original_words)
            if tags:
                for tag in tags:
                    if tag == '[REL]':
                        rel = True
                        context.append(original_words[i-1].translate(table))
                        if len(original_words) > i+1:
                            context.append(original_words[i+1].translate(table))
                    elif tag in self.tags.keys():
                        pass
                        # skip. save the tag and it's context?
            # print("filename:", each_file_name)
            interval_num = 0
            file_path = self.rootpath + each_file_name
            try:
                file_textgrid_obj = textgrid.TextGrid.fromFile(file_path)
            except ValueError:
                print(each_file_name +'value error has occured')
                os.rename(self.rootpath+ each_file_name, common_path + each_file_name)
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

            try:
                for i, each_word in enumerate(intervals_words):
                    add_rel = False
                    word_start_time = each_word.minTime
                    word_end_time = each_word.maxTime
                    word_mark = each_word.mark
                    if word_mark not in original_words and "<" not in word_mark:
                        match = [ow.translate(table) for ow in original_words if word_mark == clean_word(ow)]
                        if not match:
                            continue  # some words just turned to h. for unknown reason
                            # print(word_mark)
                            # print(original_words)
                            # print(each_file_name)
                        else:
                            word_mark = match[0]
                    if rel:
                        if word_mark == context[0] or word_mark == clean_word(context[0]):
                            if len(context) > 1 and (intervals_words[i+1].mark.translate(table) != context[1] or intervals_words[i+1].mark.translate(table) != clean_word(context[1])):
                                print(context)
                                # print(intervals_words[i+1].mark)
                                print(word_mark)
                            else:
                                add_rel = True # maybe not do it here is better
                                if "wo" in word_mark:
                                    rel_var = " RELd"
                                elif "als" in word_mark or word_mark.startswith("d") or word_mark.startswith("wel") or word_mark.startswith("jed"):
                                    rel_var = " RELs"
                                elif ("was" in word_mark) or ("wie" in word_mark) or ("wer" in word_mark):
                                    rel_var = " RLOs"
                                else:
                                    rel_var = " UNK"
                        else:
                            print(context)
                            # print(intervals_words[i+1].mark)
                            print(word_mark)
                    # # if (each_file_name, str(count)) in symbol_map.keys():
                    # #     # print(each_file_name)
                    # #     # there will be no symbol map
                    # #     value = symbol_map[(each_file_name, str(count))]
                    # #     if value[0] == 'dash' and word_mark == value[1]:
                    # #         word_mark = '-'+word_mark+'-'
                    # #         print(word_mark)
                    # #     elif value[0] == 'person' and word_mark == value[1]: # and other matched filtered regex
                    # #         word_mark = '{removed}'
                    # #     elif value[0] == 'other' and word_mark == value[1]:
                    # #         word_mark = "'''removed'''"
                    # #     double_dash = regex.compile("-[a-zA-ZäöüÄÖÜß]+-")
                    # #     half_word = regex.compile("[a-zA-ZäöüÄÖÜß]+---")
                    # #     person_name = regex.compile("{[a-zA-ZäöüÄÖÜß]+}")
                    # #     other_name = regex.compile("'''[a-zA-ZäöüÄÖÜß]+'''")
                    # # else:
                    # #     pass
                    #     # this is where you get the recovered words from the txt
                    # # ignore all the filter and other stuff...
                    std_list = set()
                    ddm_list = set()
                    pos_list = set()
                    no_match = True
                    # words = word_filter(word_mark)
                    for p in variant_match.keys():
                        if p.search(word_mark) is not None:
                            if any("IRV" in d for d in ddm_list):
                                # print(" ".join(ddm_list))
                                break
                            no_match = False
                            for values in variant_match[p]:
                                std = values[1].replace("*", "")
                                std_list.add(std)
                                if isinstance(values[2], float) and math.isnan(values[2]):  # check for empty var_code
                                    ddm_list.add(' ')  # do nothing
                                else:
                                    ddm_list.add(values[2])  # should be set
                                pos_list.add(values[3])
                    if no_match:
                        word_german = word_mark
                        var_code = " "
                        pos_tag = pos_tagger.tag([word_german])[0][1]
                    else:
                        word_german = " ".join(std_list)
                        var_code = " ".join(str(d) for d in ddm_list)
                        if any("SAF5" in d for d in ddm_list):
                            # print(ddm) # right, this
                            for g_pattern in gehen_variants:
                                if g_pattern.search(word_mark) is not None:
                                    var_code = var_code.replace("SAF5d", "")
                                    var_code = var_code.replace("SAF5s", "")
                        pos_tag = " ".join(str(p) for p in pos_list)
                    if add_rel:
                        var_code = var_code + rel_var
                        var_code = var_code.strip()
                    try:
                        while (intervals_segments[interval_num].minTime >= word_start_time) & \
                                (intervals_segments[interval_num].maxTime <= word_end_time):
                            segment_start_time = intervals_segments[interval_num].minTime
                            segment_end_time = intervals_segments[interval_num].maxTime
                            segment_mark = intervals_segments[interval_num].mark
                            self.output_as_csv(each_file_name[:-9],
                                               word_start_time, word_end_time, word_mark, segment_start_time,
                                               segment_end_time, segment_mark, var_code, word_german, pos_tag)
                            interval_num += 1
                    except IndexError:
                        interval_num = 0
                    if word_mark != '<P>':
                        count += 1

            except AttributeError as e:
                print(each_file_name+': tier words is empty or does not exist ')
                traceback.print_tb(e.__traceback__)

    def output_as_csv (self, trans_id, word_start_time, word_end_time, word_swg, segment_start_time, segment_end_time, segment_swg, var_code, word_german, pos_tag):
        with open(output_path, mode = 'a', newline="") as output_file:
            csv_writer = csv.writer(output_file, delimiter=',', quotechar ='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow([trans_id, word_start_time, word_end_time, word_swg,
                                 segment_start_time, segment_end_time, segment_swg, var_code, word_german, pos_tag]) # change the field

    def create_a_csv (self):
        """
        If the csv file you want to output does not exist in your path, this function will create it.
        """
        with open (output_path, 'w', newline="") as create_the_csv:
            csv_writer = csv.writer(create_the_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['trans_id', 'word_start_time', 'word_end_time', 'word_SWG', 'seg_start_time', 'seg_end_time', 'segment_SWG', 'var_code', 'word_German', 'POS_tag'])
        create_the_csv.close()


def read_txt(source_path, file_name):
    # phrase_dict = dict()
    # file_list = [file for file in os.listdir(source_path) if file.endswith('.txt') and file_name in file]
    # file_list = sorted(file_list, key=lambda x: int(x.split('_')[1][:-4]))
    # print(file_list)
    # for file in file_list:
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


if __name__ == '__main__':
    common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    speaker_donepath = {'panel':[common_path + 'done_panel/1982/', common_path + 'done_panel/2017/']}
    speaker = 'panel'
    extract_type = 'phone'
    date = '20200707'
    types = 'noSocialInfo' + '.csv'
    output_path = common_path + 'SWG_'+speaker+'_'+extract_type+'_'+date+types
    lex_path = common_path + 'SG-LEX 21apr2020.csv'

    # read lex table
    lex = read_lex_table(lex_path)
    for source_path in speaker_donepath[speaker]:
        transform = Transform(source_path, output_path, lex)
        transform.start()
