# recover, segment remove it.q
import os
import re
import math
import textgrid
import traceback
import string
import pandas as pd

from SWG_utils import compile_pattern, timestamp_convert, output_clauses_csv, create_clauses_csv, get_gehen_variants


def read_lex_table(lex_table_path):  # TODO: is this necessary? at all? check the other available read_lex_table method
    if lex_table_path.endswith(".xlsx"):
        lex = pd.read_excel(lex_table_path, index_col=None, header=0)
    else:
        lex = pd.read_csv(lex_table_path, index_col=None, header=0)
    lex.dropna(axis='columns', how='all', inplace=True)
    print(lex.columns)
    # lex.drop(['word_POS'], axis=1, inplace=True)
    # print(lex.columns)
    return lex

    # TODO : check how much is overlapped with clauses extract and see if we can merge some functionalities.


def create_rel_clauses_extract(extract_path, tg_path, lex_table, pos_tagger):
    if not os.path.exists(extract_path):  # if the csv does not exist, create the csv
        create_clauses_csv()
    TextGrid_file_list = [file for file in os.listdir(tg_path) if file.endswith('.TextGrid')]
    variant_match = dict()
    for r in zip(lex_table['word_variant'], lex_table['word_standard'], lex_table['word_vars'],
                 lex_table['POS_tag']):
        # dict with variant as key.
        # if no match tag the thing
        v_pattern = compile_pattern(r[0], r[2])
        if v_pattern not in variant_match.keys():
            variant_match[v_pattern] = []
        else:
            print(v_pattern)  # add it? no
        variant_match[v_pattern].append(r)
    gehen_variants = get_gehen_variants(lex_table)
    # for gehen_row in lex_table.loc[lex_table['word_lemma'] == 'gehen']['word_variant']:
    #     # check the word_vars
    #     if not any("SAF5" in wv for wv in lex_table.loc[lex_table['word_variant'] == gehen_row]['word_vars']):
    #         g_pattern = compile_pattern(gehen_row)
    #         gehen_variants.add(g_pattern)
    for each_file_name in TextGrid_file_list:
        # now combine the files of the same speakers
        print(each_file_name)
        interval_num = 0
        file_path = tg_path + each_file_name
        try:
            file_textgrid_obj = textgrid.TextGrid.fromFile(file_path)
        except UnicodeDecodeError:
            print(
                each_file_name +
                ': the encode is weird, not utf-8 or ansi')

        tier_list = file_textgrid_obj.tiers

        for each_tier in tier_list:
            if each_tier.name == 'SWG':  # read from swg tier
                tier_swg = each_tier
                intervals_swg = tier_swg.intervals

        try:
            clauses = []
            clause_annotation = []
            time_segment = dict()
            skip = False
            begin_tag = ''
            for each_annotation in intervals_swg:
                annotation_mark = each_annotation.mark
                beg_hms = timestamp_convert(each_annotation.minTime)
                if not annotation_mark.strip(): continue
                punct = [',', '.', '!', '?']  # maybe just . ! ?
                tokens = annotation_mark.split()
                time_segment[beg_hms] = tokens
                for token in tokens:
                    if any(p in token for p in punct):  # function that turn segments into clauses
                        if all(c in string.punctuation for c in token):  # this is for token like ... --- and ???
                            if not clause_annotation:
                                time_stamp = beg_hms
                            clause_annotation.append(token)
                            if len(token) > 3 or token in punct:  # why do I do this again, still don't know
                                clause_annotation.append(time_stamp)
                                clauses.append(clause_annotation)
                                clause_annotation = []
                            continue

                        word_punct_split = re.findall(
                            r"[^\w\d\s,.!?]*\w+[^\w\d\s,.!?]*\w*[^\w\d\s,.!?]*\w*[^\w\d\s,.!?]*|[^\w\s]", token,
                            re.UNICODE)  # separate word with punctuation

                        for wp in word_punct_split:  # maybe to split annotations into clauses
                            if not clause_annotation:
                                time_stamp = beg_hms
                            clause_annotation.append(wp)
                            if all(c in punct for c in wp):
                                clause_annotation.append(time_stamp)
                                clauses.append(clause_annotation)
                                clause_annotation = []
                    else:
                        if not clause_annotation:
                            time_stamp = beg_hms
                        clause_annotation.append(token)
            for cl in clauses:
                if '[ANT]' in cl or '[REL]' in cl:
                    # print("clause", cl)
                    beg_hms = cl[-1]
                    # print("time", beg_hms)
                    cl = cl[:-1]
                    # print("cl", cl)
                    if cl[0] not in time_segment[beg_hms]:  # closer  remaining is the punctuation problem
                        segment_annotation = []
                        for token in time_segment[beg_hms]:
                            segment_annotation += re.findall(
                                r"[^\w\d\s,.!?]*\w+[^\w\d\s,.!?]*\w*[^\w\d\s,.!?]*\w*[^\w\d\s,.!?]*|[^\w\s]", token,
                                re.UNICODE)
                        if cl[0] not in segment_annotation:
                            print(segment_annotation)
                            print(cl[0])
                    else:
                        segment_annotation = time_segment[beg_hms]
                    sym_seq = segment_annotation.index(cl[0]) + 1
                    words_std = []
                    ddm_tags = []
                    pos_sent = []

                    # get ddm
                    for i, word in enumerate(cl):
                        if word:  # empty word check
                            # match w with word_variant
                            std_list = set()
                            ddm_list = set()
                            pos_list = set()
                            no_match = True
                            rel = False
                            # check for var: REL
                            if i + 1 < len(cl):  # make sure next word exist
                                w_next = cl[i + 1]
                                if "[REL]" in w_next:
                                    rel = True
                                    if "wo" in word:
                                        rel_var = " RELd"
                                    elif "als" in word or word.startswith("d") or word.startswith(
                                            "wel") or word.startswith("jed"):
                                        rel_var = " RELs"
                                    elif ("was" in word) or ("wie" in word) or ("wer" in word):
                                        rel_var = " RLOs"
                                    else:
                                        rel_var = ""
                            for p in variant_match.keys():
                                if p.search(word) is not None:  # .lower()
                                    no_match = False
                                    for values in variant_match[p]:
                                        swg = values[0].replace("*", "")
                                        # rum[ge]draat
                                        if "ge" in swg and "ge" not in word:
                                            swg = swg.replace("ge", "g")  # for gespielt gspielt
                                        std = values[1].replace("*", "")
                                        std_list.add(std)
                                        if isinstance(values[2], float) and math.isnan(
                                                values[2]):  # check for empty var_code
                                            pass  # do nothing
                                        else:
                                            ddm_list.add(values[2])  # should be set
                                        if isinstance(values[3], float) and math.isnan(values[3]):
                                            pos_list.add('*')
                                        else:
                                            pos_list.add(values[3])
                            if no_match:
                                standard = word
                                ddm = "*"
                                pos = pos_tagger.tag([word])[0][1]
                                if "$" in pos:
                                    pos = "*"
                            else:
                                standard = " ".join(std_list)
                                ddm = " ".join(str(d) for d in ddm_list)
                                if any("SAF5" in d for d in ddm_list):
                                    for g_pattern in gehen_variants:
                                        if g_pattern.search(word) is not None:
                                            print(ddm)
                                            print(word)
                                            print("!")  # gegang* [ge]gang* will be taged as SAF5
                                            # k as prefix
                                            ddm = ddm.replace("SAF5d", "")
                                            ddm = ddm.replace("SAF5s", "")
                                            print(ddm)
                                pos = " ".join(str(p) for p in pos_list)
                            if rel:
                                if ddm != "*":
                                    ddm = ddm + rel_var
                                else:
                                    ddm = rel_var
                                ddm = ddm.strip()
                        words_std.append(standard)
                        ddm_tags.append(ddm)
                        pos_sent.append(pos)
                    # columns
                    output_clauses_csv(extract_path, each_file_name[each_file_name.rfind("_") + 1:-9], beg_hms, sym_seq,
                                       " ".join(cl), " ".join(ddm_tags),
                                       " ".join(pos_sent))
        except AttributeError as e:
            print(
                each_file_name +
                ': tier words is empty or does not exist ')
            traceback.print_tb(e.__traceback__)


# if __name__ == '__main__':
#     date = '20220310'
#     types = 'noSocialInfo' + '.csv'
#     working_directory = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
#     # simplify this
#     extract_type = 'clauses_rel'
#     speaker_tg_path_dict = {
#         working_directory + 'SWG_trend_' + extract_type + '_' + date + types: [working_directory + 'trend_tg/'],
#         working_directory + 'SWG_twin_' + extract_type + '_' + date + types: [working_directory + 'twin_tg/'],
#         working_directory + 'SWG_panel_' + extract_type + '_' + date + types: [working_directory + 'recovery_1982/',
#                                                                                working_directory + 'recovery_2017/']}
# speaker_tg_path_dict = {'SWG_trend_' + extract_type + '_' + date + types: [working_directory + 'trend_tg/']}
# speaker_tg_path_dict = {'SWG_panel_clauses_rel_'+date_type:[working_directory+'recovery_1982/',working_directory+'recovery_2017/'], 'SWG_trend_clauses_rel_'+date_type:[working_directory+'trend_tg/']}  #
# 'SWG_twin_clauses_rel_'+date_type:[working_directory+'twin_tg/']， 'SWG_style_' + extract_type + '_' + date + types: [working_directory + 'style_tg/']
# lex_table_path = working_directory+'SG-LEX 12feb2021.csv'
# done_path = working_directory+"done/"

# for extract_name in speaker_tg_path_dict.keys():
#     for tg_path in speaker_tg_path_dict[extract_name]:
#         extract_path = extract_name
#         transform = Transform(tg_path, extract_path)
#         transform.start()

# tg_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/test/'
# extract_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/test.csv'
# transform = Transform(tg_path, extract_path)
# transform.start()
