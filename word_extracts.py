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

from SWG_utils import timestamp_convert, skip_word_list, skip_by_tags, compile_pattern


def create_word_csv(speaker_paths, word_extract_path, lex_table, filename_annotation_map):
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
        v_pattern = compile_pattern(r[0])
        if v_pattern not in variant_match.keys():
            variant_match[v_pattern] = []
        else:
            print(v_pattern)
        variant_match[v_pattern].append(r)
    # check if the word's lemma is gehen. If it is, then don't tag the word as SAF5
    gehen_variants = set()
    for gehen_row in lex_table.loc[lex_table['word_lemma'] == 'gehen']['word_variant']:
        g_pattern = compile_pattern(gehen_row)
        gehen_variants.add(g_pattern)

    # get speaker file names
    for speaker in speaker_paths:
        file_list = [file for file in os.listdir(speaker) if file.endswith('.TextGrid')]
        for file_name in file_list:
            outputs = []
            annotations = filename_annotation_map[file_name]
            # now time stamps and word_count
            for word_annotation in annotations:

                for i, w in enumerate(word_annotation):
                    if w:  # empty word check
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
                                elif "was" in w or "wie" in w:
                                    rel_var = " RLOs"
                                else:
                                    rel_var = " UNK"
                        # regular ddm tagging
                        std_list = set()
                        ddm_list = set()
                        pos_list = set()
                        no_match = True

                        for p in variant_match.keys(): # could make it into a seperate method
                            if p.search(w) is not None:  # .lower()
                                no_match = False
                                for values in variant_match[p]:
                                    swg = values[0].replace("*", "")
                                    # rum[ge]draat
                                    if "ge" in swg and "ge" not in w:
                                        swg = swg.replace("ge", "g") # for gespielt gspielt
                                    # another ge exception for word_lemma gehen
                                    std = values[1].replace("*", "")
                                    std_list.add(std)
                                    if isinstance(values[2], float) and math.isnan(values[2]): #check for empty var_code
                                        pass  # do nothing
                                    else:
                                        ddm_list.add(values[2]) # should be set
                                    # another check for the lex table
                                    # or change the lex table method when reading just ignore the bad word_vars
                                    pos_list.add(values[3])
                        if no_match:
                            standard = w
                            ddm = ""
                            pos = pos_tagger.tag([w])[0][1]
                        else:
                            standard = " ".join(std_list)
                            ddm = " ".join(str(d) for d in ddm_list)
                            if any("SAF5" in d for d in ddm_list):
                                print(ddm) # right, this
                                for g_pattern in gehen_variants:
                                    if g_pattern.search(w) is not None:
                                        ddm = ddm.replace("SAF5d","")
                                        ddm = ddm.replace("SAF5s","")
                            pos = " ".join(str(p) for p in pos_list)
                        if rel:
                            ddm = ddm + rel_var
                        ddm = ddm.strip()
                    outputs.append([file_name[file_name.rfind("_") + 1:-9], w, ddm, standard, pos])
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
    filter_list = [person_name_l, person_name_r, hyphen, hyphen_2, double_dash, dash_l, dash_r, dot_2, question_2, quo_2]

    annotations_list = []
    filename_annotation_map = dict()
    for speaker in speaker_path:
        file_list = [file for file in os.listdir(speaker) if file.endswith('.TextGrid')]
        for file_name in file_list:
            #print(file_name)
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
                    anno = anno_filter(tokens, hyphen_3)
                    # or should I just
                    for word_raw in anno:
                        # I need to test the filters
                        # I wonder the effect of these
                        word_raw = word_raw.replace(":", "")
                        word_raw = word_raw.replace('"', '')
                        word_raw = word_raw.replace('…', '')

                        if any(re.search(filter_pattern, word_raw) for filter_pattern in filter_list):
                            continue
                        word_nopunct = []
                        tmp = []
                        tmp.append(word_raw)
                        while tmp:
                            word = tmp.pop(0)
                            # later maybe think of a more elegant way of doing this
                            if any(char in punct for char in word):
                                for p in punct:
                                    if p in word:
                                        for w in word.split(p):
                                            if w is not '':
                                                tmp.append(w)
                            else:
                                word_nopunct.append(word)
                        for word in word_nopunct:
                            # filter it again
                            if any(re.search(filter_pattern, word_raw) for filter_pattern in filter_list):
                                continue
                            else:
                                word_annotations.append(word)
                    annotations_list.append(word_annotations)
                    if word_annotations:  # checking empty list
                        filename_annotation_map[file_name].append(word_annotations)

            except AttributeError as e:
                print(file_name +': tier words is empty or does not exist ')
                traceback.print_tb(e.__traceback__)
    word_counter = create_word_counter(annotations_list)
    # also wanted to experiment with raw word counter and see if the freq counts differ.
    return word_counter, filename_annotation_map


def create_word_counter(list_annotations):
    word_counter = collections.Counter()
    for annotation in list_annotations:
        word_counter.update(annotation)
    return word_counter


def append_to_word_extract(transcript_id,beg_hms, sym_seq, word, DDM, std, pos):# should also clean this code a bit
    with open(word_extract_path, mode='a', newline="") as word_extract_output:
        csv_writer = csv.writer(word_extract_output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([transcript_id, beg_hms, sym_seq, word, DDM, std, pos])


def append_to_lex(word_stem, word_lemma, word_standard, word_variant, word_vars, word_english, POS, word_MHG, word_stem_freq, word_lemma_freq, word_standard_freq, word_variant_freq):
    with open(output_path_lex, mode='a', newline="") as lex_output: # path thing might not work though
        csv_writer = csv.writer(lex_output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(
            [word_stem, word_lemma, word_standard, word_variant, word_vars, word_english, POS, word_MHG, word_stem_freq, word_lemma_freq, word_standard_freq, word_variant_freq])





def get_count(pattern, word_counter): # need to update for stem and lemmas. Do it here or else where?
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

    v_dict= collections.OrderedDict()  # ordered output
    stem_c = dict()  # maybe there is a better data structure
    lemma_c = dict()
    standard_c = dict()
    variant_c = dict()
    dict_count_list = [stem_c, lemma_c, standard_c, variant_c]
    pos_tagger = CoreNLPParser('http://localhost:9002', tagtype='pos')
    # check for
    with open(output_path_lex, 'w', newline="") as lex_csv:
        csv_writer = csv.writer(lex_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(['word_stem', 'word_lemma', 'word_standard', 'word_variant', 'word_vars', 'word_english',
                             'POS_tag', 'word_MHG', 'word_stem_freq', 'word_lemma_freq', 'word_standard_freq', 'word_variant_freq'])
    lex_csv.close()
    for r in zip(lex_table['word_stem'], lex_table['word_lemma'], lex_table['word_standard'], lex_table['word_variant'],
                 lex_table['word_vars'], lex_table['word_english'], lex_table['POS_tag'], lex_table['word_MHG']):# later there will not be a pos corr column!!! remember to change the code
        key = tuple("" if isinstance(i, float) and math.isnan(i) else i for i in r[:4])  # key: word_stem, word_lemma, word_standard, word_variant
        value = tuple("" if isinstance(i, float) and math.isnan(i) else i for i in r[4:])# value: word_vars, word_english, word_MHG
        # is there a way to avoid repeated tagging on the same standard words?
        # pre-prossessing the word_vars, checking for word_vars that does not end with 's' or 'd'
        word_vars = value[0].split()  # get rid of dangling whitespaces and multiple word_vars
        for wv in word_vars:
            if not (wv.endswith("s") or wv.endswith("d")):
                skip = True
                with open(date+"_wrong_word_vars.txt", "a+") as file:
                    print(key, value, file=file)
                continue

        # update word_vars dictionary
        if key not in v_dict.keys():
            v_dict[key] = [value]
        else: # if the key exist in dictionary.
            append = True
            for v in v_dict[key]: # check each value to see if the value existed.
                if v[0] == value[0]:  # only check if the new word_vars is the same as the existing one.
                    append = False
                    print(key, value)
                    break
            if append:
                v_dict[key].append(value)

    for key in v_dict.keys():
        # unused variables
        stem = key[0]
        lemma = key[1]
        standard = key[2]
        variant = key[3]
        # write a function for the lower part with the four things as argument then use *key. to make things easier
        variant_pattern = compile_pattern(variant)
        variant_count = get_count(variant_pattern, counter)  # later can be changed to new_count
        #raw_count = get_count(variant_pattern, raw_counter)
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
        line = (*k, DDM_tag, *v[0][1:], stem_freq, lemma_freq, standard_freq, variant_freq)
        append_to_lex(*line)
        # now  I need the counts, which I got from a counter


def count_update(key_word, dictionary, new_count):
    if key_word not in dictionary.keys():
        dictionary[key_word] = new_count
    else:
        old_count = dictionary[key_word]
        dictionary[key_word] = old_count + new_count


def read_lex_table(lex_table_path):
    if lex_table_path.endswith(".xlsx"):
        lex = pd.read_excel(lex_table_path, index_col=None, header=0)
    else:
        lex = pd.read_csv(lex_table_path, index_col=None, header=0)
    lex.dropna(axis='columns', how='all', inplace=True)
    print(lex.columns)
    # lex.drop(['word_POS'], axis=1, inplace=True)
    # print(lex.columns)
    return lex


def anno_filter(anno_raw, hyphen_3):
    #if "[REL]" in anno_raw:
        #print(anno_raw)
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
    output_path_lex = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SG-LEX 04mar2020.csv"
    lex_input_path_xlsx = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SG-LEX 04mar2020.xlsx" # always use the newer version
    lex_fix = False
    extract = True
    common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    all_speaker_paths = [common_path+"recovery_1982/", common_path+"recovery_2017/", common_path+"trend_tg/",
                         common_path+"twin_tg/"]
    extract_type = 'words'
    date = '20200408'
    type = 'noSocialInfo'+'.csv'
    speaker_tg_path = {common_path+'SWG_panel_'+extract_type+'_'+date+type:[common_path+'recovery_1982/', common_path+'recovery_2017/']
        , common_path+'SWG_trend_'+extract_type+'_'+date+type:[common_path+'trend_tg/'],
                  common_path+'SWG_twin_'+extract_type+'_'+date+type:[common_path+'twin_tg/']}
    # thinking about automating the entire process, using if and other stuff
    # put the lex table fix together and the speaker files and word extracts together
    if lex_fix:
        word_counter, file_words_map = read_tg_files(all_speaker_paths)
        lex = read_lex_table(lex_input_path_xlsx)
        lex_table_fix(lex, word_counter, output_path_lex)
    if extract:
        for speaker_path in speaker_tg_path.keys(): # speaker should be refactored to extract
            word_extract_path = speaker_path # maybe pass this as argument?, change it to a path
            _, file_words_map = read_tg_files(speaker_tg_path[speaker_path])
            lex_fixed = read_lex_table(output_path_lex)
            create_word_csv(speaker_tg_path[speaker_path], word_extract_path, lex_fixed, file_words_map)
            # ddm tags printed between word skipping
            # OUTPUT PATH NOT CORRECT