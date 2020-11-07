import collections
import csv
import math
import os
import re
import traceback
import pandas as pd
import textgrid
from nltk import CoreNLPParser
from ordered_set import OrderedSet

from SWG_utils import timestamp_convert, skip_word_list, skip_by_tags, compile_pattern, word_filter, read_lex_table

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
filter_list = [angle_brackets, person_name_l, person_name_r, hyphen, hyphen_2, hyphen_3, double_dash, dash_l, dash_r,
               dot_2, question_2,
               quo_2]
def create_word_csv(speaker_paths, word_extract_path, lex_table, filename_annotation_map, file_timeseg_map):
    variant_match = dict()
    pos_tagger = CoreNLPParser('http://localhost:9002', tagtype='pos')
    # create csv when there is no csv files
    if not os.path.exists(word_extract_path):  # if the csv does not exist, create the csv
        with open(word_extract_path, 'w', newline="") as word_extrac_csv:
            csv_writer = csv.writer(word_extrac_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['trans_id', 'beg_hms', 'sym_seq', 'Word_SWG', 'var_code', 'Word_German', 'POS_tag'])
        word_extrac_csv.close()
    for r in zip(lex_table['word_variant'], lex_table['word_standard'], lex_table['word_vars'], lex_table['POS_tag']):
        # dict with variant as key.
        # if no match tag the thing
        v_pattern = compile_pattern(r[0], r[2])
        if v_pattern not in variant_match.keys():
            variant_match[v_pattern] = []

        variant_match[v_pattern].append(r)
    for w_var, w_val in variant_match.items():
        if len(w_val) > 1:
            print(w_var, w_val)
    # check if the word's lemma is gehen. If it is, then don't tag the word as SAF5
    gehen_variants = set()
    locations = lex_table.loc[lex_table['word_lemma'] == 'gehen']
    for gehen_var in zip(locations['word_variant'], locations['word_vars']):
        if "SAF5" not in gehen_var[1]:
            g_pattern = compile_pattern(gehen_var[0], gehen_var[1])
            gehen_variants.add(g_pattern)

    # get speaker file names
    for speaker in speaker_paths:
        file_list = [file for file in os.listdir(speaker) if file.endswith('.TextGrid')]
        for file_name in file_list:
            outputs = []
            annotations = filename_annotation_map[file_name]
            time_seg_map = file_time_seg_map[file_name]
            # now time stamps and word_count
            for word_annotation in annotations:
                beg_hms = word_annotation[-1]
                word_annotation = word_annotation[:-1]
                original_segment = time_seg_map[beg_hms]
                pointer_orgseg = 0
                for i, w in enumerate(word_annotation):
                    if w:  # empty word check
                        # print(w)
                        sym_seq = None
                        for org_idx, t in enumerate(original_segment): # this is for the word count
                            if sym_seq is not None:
                                break
                            words = word_filter(t)
                            if words:
                                for word in words:  # word,word2 word word2 index?
                                    # if same words, take the later one? or there should be a check
                                    if (w == word) and (org_idx >= i) and (org_idx >= pointer_orgseg) and (sym_seq is None): # this is not good, need to clean this orginal segment again, make that into a helper method.
                                        sym_seq = org_idx+1
                                        # print(sym_seq)
                                        pointer_orgseg = org_idx
                        # check for var: REL
                        rel = False
                        if i+1 < len(word_annotation): # make sure next word exist
                            w_next = word_annotation[i+1]
                            if "[REL]" in w_next:
                                rel = True
                                if "wo" in w:
                                    rel_var = " RELd"
                                elif "als" in w or w.startswith("d") or w.startswith("wel") or w.startswith("jed"):
                                    rel_var = " RELs"
                                elif ("was" in w) or ("wie" in w) or ("wer" in w):
                                    rel_var = " RLOs"
                                else:
                                    rel_var = " UNK"
                        # regular ddm tagging
                        std_list = set()
                        ddm_list = set()
                        pos_list = set()
                        no_match = True

                        for p in variant_match.keys(): # could make it into a seperate method
                            if any("IRV" in d for d in ddm_list):
                                # print(" ".join(ddm_list))
                                break
                            if p.search(w) is not None:  # .lower()
                                no_match = False
                                replace = True
                                for values in variant_match[p]:
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
                                            std = w.replace(w_var, w_std)
                                        else:
                                            std = values[1]
                                        std_list.add(std)
                                    if isinstance(values[2], float) and math.isnan(values[2]): #check for empty var_code
                                        ddm_list.add(' ')  # do nothing
                                    else:
                                        ddm_list.add(values[2])  # should be set
                                    # another check for the lex table
                                    # or change the lex table method when reading just ignore the bad word_vars
                                    pos_list.add(values[3])

                        if no_match:
                            standard = w
                            ddm = " "
                            pos = pos_tagger.tag([w])[0][1]
                        else:
                            standard = " ".join(std_list)
                            if len(std_list) > 1:
                                print(w, "std: ", standard)
                            ddm = " ".join(str(d) for d in ddm_list)
                            # maybe here is the problem
                            if any("SAF5" in d for d in ddm_list):
                                # print(ddm) # right, this
                                for g_pattern in gehen_variants:
                                    if g_pattern.search(w) is not None:
                                        ddm = ddm.replace("SAF5d", "")
                                        ddm = ddm.replace("SAF5s", "")
                            pos = " ".join(str(p) for p in pos_list)
                        if rel:
                            ddm = ddm + rel_var
                            ddm = ddm.strip()
                    output = [file_name[file_name.rfind("_") + 1:-9], w, ddm, standard, pos, beg_hms, sym_seq]
                    # print(output)
                    outputs.append(output)

            outputs = skip_by_tags(outputs, 'r')
            outputs = skip_by_tags(outputs, 'wl')
            outputs = skip_by_tags(outputs, 'wg')
            word_list1_start = ["Finger", "Flüge", "Biene", "Hunger", "immer", "Äpfel", "Apfel", "Asche", "zum",
                                "waschen"]
            word_list1_end = ["laufen", "Frage", "Linde", "meist", "Haar", "Huhn", "Türe", "Kinder", "alle", "Gast"]
            word_list2_start = ["Flüge", "Fliege", "Söhne", "Sehne", "können", "kennen", "Türe", "Tiere", "vermissen",
                                "vermessen"]
            word_list2_end = ["heiter", "heute", "Feuer", "feiern", "Ofen", "oben", "Kreide", "Kreuze", "Magen",
                              "sagen"]
            ft_1_start = ["Vor", "Zeiten", "war", "ein", "König", "und", "eine", "Königin", "die", "sprachen"]
            ft_1_end = ["alte", "Frau", "mit", "einer", "Spindel", "und", "spann", "emsig", "ihren", "Flachs"]
            ft_2_start = ["Es", "war", "einmal", "eine", "alte", "Geiß", "die", "hatte", "sieben", "junge"]
            ft_2_end = ["er", "in", "seinen", "Rachen", "nur", "das", "jüngste", "fand", "er", "nicht"]
            ft_3_start = ["In", "den", "alten", "Zeiten", "wo", "das", "Wünschen", "noch", "geholfen", "hat"]
            ft_3_end = ["bei", "seinesgleichen", "und", "quakt", "und", "kann", "keines", "Menschen", "Geselle", "sein"]
            outputs = skip_word_list(outputs, word_list1_start, word_list1_end, 'wl')
            outputs = skip_word_list(outputs, word_list2_start, word_list2_end, 'wl')
            outputs = skip_word_list(outputs, ft_1_start, ft_1_end, 'ft')
            outputs = skip_word_list(outputs, ft_2_start, ft_2_end, 'ft')
            outputs = skip_word_list(outputs, ft_3_start, ft_3_end, 'ft')
            for output in outputs:
                append_to_word_extract(*output)


def read_tg_files(speaker_path): # read the words in filtered, return a counter and something more for the word extract
    """This method will read in all the annotations from speaker files, split in to list of words and filter out the
    unneeded words. It will return a word Counter for getting the frequency of words in lex table and a dictionay mapping
    from file name to list of annotations which is used to produce word extracts."""
    # SEPARATE function for this, and filter on the fly
    # word count could be numerate function +1

    annotations_list = []
    filename_annotation_map = dict()
    file_timeseg_map = dict()
    for speaker in speaker_path:
        file_list = [file for file in os.listdir(speaker) if file.endswith('.TextGrid')]
        for file_name in file_list:
            print(file_name)
            if file_name not in filename_annotation_map.keys():
                filename_annotation_map[file_name] = []
            else:
                print("Same speaker file！")  # probably should rephrase this.
            file_path = speaker + file_name
            try:
                file_textgrid_obj = textgrid.TextGrid.fromFile(file_path)
            except UnicodeDecodeError:
                print(file_name +': the encode is weird, not utf-8 or ansi')

            tier_list = file_textgrid_obj.tiers

            for each_tier in tier_list:
                if each_tier.name == 'SWG':  # read from swg tier
                    tier_swg = each_tier
                    intervals_swg = tier_swg.intervals
            try:
                time_segment = dict()
                for each_annotation in intervals_swg:
                    annotation_mark = each_annotation.mark
                    beg_hms = timestamp_convert(each_annotation.minTime)
                    # where is the filter
                    # dict: beg_hms: original segments
                    # list: filtered annotation + beg_hms
                    # search and label moving the index
                    if not annotation_mark.strip(): continue
                    word_annotations = []
                    punct = [',', '.', '!', '?']  # maybe just . ! ?
                    # word_raw_counter.update(annotation_mark.split())  # what is this for?
                    tokens = annotation_mark.split()
                    time_segment[beg_hms] = tokens
                    anno = anno_filter(tokens, hyphen_3)  # might have some impact. We'll see
                    # print(beg_hms)
                    # print(tokens)
                    for word_raw in anno:
                        word_nopunct = word_filter(word_raw)
                        if word_nopunct:
                            for word in word_nopunct:
                                # filter it again
                                if any(re.search(filter_pattern, word_raw) for filter_pattern in filter_list):
                                    continue
                                else:
                                    word_annotations.append(word)
                        else:
                            # print(word_nopunct)
                            continue
                    # test counter with beg_hms attached
                    annotations_list.append(word_annotations)
                    #print("beg hms?", word_annotations)
                    if word_annotations:  # checking empty list
                        word_annotations.append(beg_hms)
                        # print(word_annotations)
                        filename_annotation_map[file_name].append(word_annotations)
                file_timeseg_map[file_name] = time_segment
                # print(filename_annotation_map)
                # print(file_timeseg_map)
            except AttributeError as e:
                print(file_name +': tier words is empty or does not exist ')
                traceback.print_tb(e.__traceback__)
    # print(annotations_list)
    word_counter = create_word_counter(annotations_list)

    # # also wanted to experiment with raw word counter and see if the freq counts differ.
    return word_counter, filename_annotation_map, file_timeseg_map


def create_word_counter(list_annotations):
    word_counter = collections.Counter()
    for annotation in list_annotations:
        word_counter.update(annotation)
    return word_counter


def append_to_word_extract(transcript_id, word, DDM, std, pos, beg_hms, sym_seq):# should also clean this code a bit
    with open(word_extract_path, mode='a', newline="") as word_extract_output:
        csv_writer = csv.writer(word_extract_output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([transcript_id, beg_hms, sym_seq, word, DDM, std, pos])


def append_to_lex(word_stem, word_lemma, word_standard, word_variant, word_vars, word_english, POS, word_MHG, word_stem_freq, word_lemma_freq, word_standard_freq, word_variant_freq):
    with open(output_file_lex, mode='a', newline="") as lex_output: # path thing might not work though
        csv_writer = csv.writer(lex_output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(
            [word_stem, word_lemma, word_standard, word_variant, word_vars, word_english, POS, word_MHG, word_stem_freq, word_lemma_freq, word_standard_freq, word_variant_freq])


def get_count(pattern, word_counter):  # need to update for stem and lemmas. Do it here or else where?
    count = 0
    words = []
    for word in word_counter.keys():
        if pattern.search(word) is not None:
            count = count + word_counter[word]
            words.append(word)
    return (count, words)


def lex_table_fix(lex_table, counter, lex_output_path):  # need a better name for this method
    """this method will take the lex table and check if there are duplicated rows with different word_vars,
    pos tagging the word in word_standard and generating search patterns for DDM tagging."""

    v_dict = collections.OrderedDict()  # ordered output
    stem_c = dict()  # maybe there is a better data structure
    lemma_c = dict()
    standard_c = dict()
    variant_c = dict()
    dict_count_list = [stem_c, lemma_c, standard_c, variant_c]
    # check for
    with open(output_file_lex, 'w', newline="") as lex_csv:
        csv_writer = csv.writer(lex_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(['word_stem', 'word_lemma', 'word_standard', 'word_variant', 'word_vars', 'word_english',
                             'POS_tag', 'word_MHG', 'word_stem_freq', 'word_lemma_freq', 'word_standard_freq', 'word_variant_freq'])
    lex_csv.close()

    for r in zip(lex_table['word_stem'], lex_table['word_lemma'], lex_table['word_standard'], lex_table['word_variant'],
                 lex_table['word_vars'], lex_table['word_english'], lex_table['POS_tag'], lex_table['word_MHG']):# later there will not be a pos corr column!!! remember to change the code
        key = tuple(" " if isinstance(i, float) and math.isnan(i) else i for i in r[:4])  # key: word_stem, word_lemma, word_standard, word_variant
        value = tuple(" " if isinstance(i, float) and math.isnan(i) else i for i in r[4:])# value: word_vars, word_english, word_MHG
        # is there a way to avoid repeated tagging on the same standard words?
        # pre-prossessing the word_vars, checking for word_vars that does not end with 's' or 'd'
        skip = False
        word_vars = value[0].split()  # get rid of dangling whitespaces and multiple word_vars
        word_std = key[2]
        word_variant = key[3]
        if "*" in word_variant and "*" not in word_std:
            with open(date + "_*_check.txt", "a+") as file:
                print(key[3], key[2], value, file=file)
        elif "*" in word_std and "*" not in word_variant:
            with open(date + "_*_check.txt", "a+") as file:
                print(key[3], key[2], value, file=file)
        AIS_check_list = ["ei", "êi", "ôi"]
        if any(ais in key[3] for ais in AIS_check_list):
            if not any("AIS" in wv for wv in word_vars):
                with open(date+"_check_ais.txt", "a+") as file:
                    print(key[3], value, file=file)
        for wv in word_vars:
            if not (wv.endswith("s") or wv.endswith("d")):
                skip = True
                with open(date+"_wrong_word_vars_ds.txt", "a+") as file:
                    print(key[3], value, file=file)
        if skip:
            continue
        # update word_vars dictionary
        if key not in v_dict.keys():
            v_dict[key] = [value]
        else:  # if the key exist in dictionary.
            append = True
            for v in v_dict[key]:  # check each value to see if the value existed.
                if v[0] == value[0]:  # only check if the new word_vars is the same as the existing one.
                    append = False
                    print(key, value)
                    break
            if append:
                v_dict[key].append(value)

    for key in v_dict.keys():
        # unused variables
        variant = key[3]
        # write a function for the lower part with the four things as argument then use *key. to make things easier
        variant_pattern = compile_pattern(variant, v_dict[key][0])
        variant_count = get_count(variant_pattern, counter)  # later can be changed to new_count
        new_count = variant_count[0]  # later can be removed when the get count function no longer needs to return word
        for key_word, d in zip(list(key), dict_count_list):  # stem, lemma, standard, variant
            count_update(key_word, d, new_count)  # don't know how well this will work
    for k, v in v_dict.items():
        stem_freq = stem_c[k[0]]
        lemma_freq = lemma_c[k[1]]
        standard_freq = standard_c[k[2]]
        variant_freq = variant_c[k[3]]
        tags = [t[0] for t in v]
        DDM_tag = " ".join(set(" ".join(tags).split()))
        if not DDM_tag:
            DDM_tag = " "
        line = (*k, DDM_tag, *v[0][1:], stem_freq, lemma_freq, standard_freq, variant_freq)
        append_to_lex(*line)


def count_update(key_word, dictionary, new_count):
    if key_word not in dictionary.keys():
        dictionary[key_word] = new_count
    else:
        old_count = dictionary[key_word]
        dictionary[key_word] = old_count + new_count


def anno_filter(anno_raw, hyphen_3):
    if any(re.search(hyphen_3, wr) for wr in anno_raw): # when it switched to while it takes so long
        # update anno_raw
        idx = [i for i, wr in enumerate(anno_raw) if re.search(hyphen_3, wr)]
        # if there are sentences with multiple --- and that need to be taken into account
        i = idx[0]
        if 1 < i < len(anno_raw) - 2:
            s = OrderedSet(anno_raw[i - 2:i] + anno_raw[i + 1:i + 3])
            anno_raw = anno_raw[:i - 2] + list(s) + anno_raw[i + 3:]
        elif 0 < i < len(anno_raw) - 1:  # else
            s = OrderedSet([anno_raw[i - 1], anno_raw[i + 1]])
            anno_raw = anno_raw[:i - 1] + list(s) + anno_raw[i + 2:]
        else:  # no need to check
            return anno_raw

        if len(idx) > 1: # more than one ---, filter again (recursively)
            anno_filter(anno_raw, hyphen_3)
    return anno_raw


if __name__ == '__main__':
    working_directory = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    output_file_lex = working_directory+"SG-LEX 06nov2020.csv"
    input_file_lex = working_directory+"SG-LEX 06nov2020.xlsx"  # always use the newer version
    fix_lex = True
    run_extract = False

    all_speaker_paths = [working_directory + "recovery_1982/", working_directory + "recovery_2017/", working_directory + "trend_tg/",
                         working_directory + "twin_tg/"]  # , working_directory+"style_tg/"
    # do not use this, use the dictionary values in the
    extract_type = 'words'
    date = '20201103'
    types = 'noSocialInfo'+'.csv'
    speaker_tg_path_dict = {working_directory+'SWG_twin_'+extract_type+'_'+date+types: [working_directory+'twin_tg/']}
    # working_directory+'SWG_trend_'+extract_type+'_'+date+types: [working_directory+'trend_tg/']
    # working_directory+'SWG_panel_'+extract_type+'_'+date+types:[working_directory+'recovery_1982/', working_directory+'recovery_2017/'], working_directory+'SWG_twin_'+extract_type+'_'+date+types:[working_directory+'twin_tg/']
    # working_directory + 'SWG_style_' + extract_type + '_' + date + types: [working_directory + 'style_tg/']
    # put the lex table fix together and the speaker files and word extracts together
    if fix_lex:
        word_counter, file_words_map, file_time_seg_map = read_tg_files(all_speaker_paths)
        lex = read_lex_table(input_file_lex)
        lex_table_fix(lex, word_counter, output_file_lex)

    if run_extract:
        for speaker_path in speaker_tg_path_dict.keys():  # speaker should be refactored to extract
            word_extract_path = speaker_path  # maybe pass this as argument?, change it to a path
            _, file_words_map, file_time_seg_map = read_tg_files(speaker_tg_path_dict[speaker_path])
            fix_lexed = read_lex_table(output_file_lex)
            create_word_csv(speaker_tg_path_dict[speaker_path], word_extract_path, fix_lexed, file_words_map, file_time_seg_map)
