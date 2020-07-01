"""
Author: Nianheng Wu
xjtuwunianheng@gmail.com, Eberhard Karls Universität Tübingen
"""
import math
import os
import errno
import csv
import textgrid
import traceback
import regex
from nltk import CoreNLPParser

from SWG_utils import compile_pattern, read_lex_table, word_filter


class Transform:

    def __init__(self, rootpath, outputpath, lex): # maps
        self.rootpath = rootpath
        self.outputpath = outputpath
        self.lex_table = lex

    def start(self):
        try:
            os.chdir(source_path)
        except FileNotFoundError:
            print(errno.EPERM)
        if not os.path.exists(output_path):
            self.create_a_csv()
        self.get_file_list()

    def get_file_list(self):
        file_list = [file for file in os.listdir(self.rootpath) if file.endswith('.TextGrid')]
        file_list = sorted(file_list, key=lambda x: int(x.split('_')[1][:-9]))
        self.read_from_textgrid(file_list)

    def read_from_textgrid (self, file_list):
        pos_tagger = CoreNLPParser('http://localhost:9002', tagtype='pos')
        print(file_list)
        variant_match = dict()
        for r in zip(self.lex_table['word_variant'], self.lex_table['word_standard'], self.lex_table['word_vars'],
                     self.lex_table['POS_tag']):
            # dict with variant as key.
            # if no match tag the thing
            v_pattern = compile_pattern(r[0])
            if v_pattern not in variant_match.keys():
                variant_match[v_pattern] = []
            else:
                print(v_pattern)
            variant_match[v_pattern].append(r)

        gehen_variants = set()
        locations = self.lex_table.loc[self.lex_table['word_lemma'] == 'gehen']
        for gehen_var in zip(locations['word_variant'], locations['word_vars']):
            if "SAF5" not in gehen_var[1]:
                g_pattern = compile_pattern(gehen_var[0])
                gehen_variants.add(g_pattern)
        # maybe I should just get it from the other table.
        for each_file_name in file_list:
            print("filename:", each_file_name)
            # outputs = []
            interval_num = 0
            file_path = source_path + each_file_name
            try:
                file_textgrid_obj = textgrid.TextGrid.fromFile(file_path)
            except UnicodeDecodeError:
                print(each_file_name + ': the encode is weird, not utf-8 or ansi')

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
                for i, each_word in enumerate(intervals_words): # this is different
                    # I don't even know what the data would look like. is it going to be in order?
                    # so I need to start over.
                    word_start_time = each_word.minTime
                    word_end_time = each_word.maxTime
                    word_mark = each_word.mark
                    if (each_file_name, str(count)) in symbol_map.keys():
                        # print(each_file_name)
                        value = symbol_map[(each_file_name, str(count))]
                        if value[0] == 'dash' and word_mark == value[1]:
                            word_mark = '-'+word_mark+'-'
                            print(word_mark)
                        elif value[0] == 'person' and word_mark == value[1]: # and other matched filtered regex
                            word_mark = '{removed}'
                        elif value[0] == 'other' and word_mark == value[1]:
                            word_mark = "'''removed'''"
                    else:
                        word_mark = self.recover(word_mark)
                    # ignore all the filter and other stuff...
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
                        # maybe here is the problem
                        if any("SAF5" in d for d in ddm_list):
                            # print(ddm) # right, this
                            for g_pattern in gehen_variants:
                                if g_pattern.search(word_mark) is not None:
                                    ddm = ddm.replace("SAF5d", "")
                                    ddm = ddm.replace("SAF5s", "")
                        pos_tag = " ".join(str(p) for p in pos_list)

                    try:
                        while (intervals_segments[interval_num].minTime >= word_start_time) & \
                                (intervals_segments[interval_num].maxTime <= word_end_time):
                            segment_start_time = intervals_segments[interval_num].minTime
                            segment_end_time = intervals_segments[interval_num].maxTime
                            segment_mark = intervals_segments[interval_num].mark
                            self.output_as_csv(each_file_name[:-9],
                                               word_start_time, word_end_time, word_mark, segment_start_time,
                                               segment_end_time, segment_mark, var_code, word_german, pos_tag)
                            # word_swg, segment_swg
                            interval_num += 1
                    except IndexError:
                        interval_num = 0
                    if word_mark != '<P>':
                        count += 1

            except AttributeError as e:
                print(each_file_name+': tier words is empty or does not exist ')
                traceback.print_tb(e.__traceback__)


    def recover(self, word_string):
        word_string = word_string.replace("aE", "ä")
        word_string = word_string.replace("oE", "ö")
        word_string = word_string.replace("uE", "ü")
        word_string = word_string.replace("sS", "ß")
        word_string = word_string.replace("AE", "Ä")
        word_string = word_string.replace("OE", "Ö")
        word_string = word_string.replace("UE", "Ü")

        word_string = word_string.replace("aA", "â")
        word_string = word_string.replace("AA", "Â")
        word_string = word_string.replace("aN", "ã")
        word_string = word_string.replace("AN", "Ã")
        word_string = word_string.replace("oY", "ôi")
        word_string = word_string.replace("OY", "Ôi")
        word_string = word_string.replace("eY", "êi")
        word_string = word_string.replace("EY", "Êi")
        return word_string

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




def read_record():
    the_symbol_map = {}
    with open(record_path) as record:
        record_reader = csv.reader(record)
        next(record_reader)
        for record_lines in record_reader:
            the_symbol_map[(record_lines[0], record_lines[1])] = (record_lines[3], record_lines[2])
    return the_symbol_map


if __name__ == '__main__':
    record_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/symbol_record.csv'
    source_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/done_panel/'
    speaker = 'panel'
    extract_type = 'phone'
    date = '20200701'
    types = 'noSocialInfo' + '.csv'
    output_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SWG_'+speaker+'_'+extract_type+'_'+date+types
    lex_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SG-LEX 21apr2020.csv'
    # done_path = ""

    symbol_map = read_record()
    # read lex table
    lex = read_lex_table(lex_path)
    transform = Transform(source_path, output_path, lex)
    transform.start()
