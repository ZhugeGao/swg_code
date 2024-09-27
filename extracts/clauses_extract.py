# recover, segment remove it.q

import math
import os
import re
import string
import traceback

import textgrid
from ordered_set import OrderedSet

from SWG_utils import compile_pattern, timestamp_convert, output_clauses_csv, create_clauses_csv, tags_for_skipping, \
    get_gehen_variants, tags_to_type


# TODO: change this class structure. Make it easier to change
# comment out the functional module of each class. and merge


# TODO: does it makes sense to keep this tag in each extract class? or only keep it in one place so modifying it
#  would be easy.
def create_clauses_extract(extract_path, tg_paths, lex_table,
                           pos_tagger):
    # TODO: tg_path, what about panel with more than one tg path. process one tg directory at a time. will it be
    #  appended to the existing extract? I think so.
    create_clauses_csv(extract_path)
    TextGrid_file_list = []
    for path in tg_paths: # get all the TextGrid files in the list of paths
        TextGrid_file_list.extend([os.path.join(path, file) for file in os.listdir(path) if file.endswith('.TextGrid')])
    # TextGrid_file_list = [file for file in os.listdir(tg_path) if file.endswith()]
    # sort the TextGrid files by year, then by session, then by file number
    if 'panel' in extract_path:
        TextGrid_file_list = sorted(TextGrid_file_list, key=lambda path: (
            int(path.split('/')[-2]),  # Sort based on '1982', '2017', etc.
            int(path.split('S')[1].split('-')[0]),  # Sort based on '007', '008', etc.
            int(path.split('-')[3])  # Sort based on '-1-', '-2-', etc.
            ))
    else:
        TextGrid_file_list = sorted(TextGrid_file_list, key=lambda path: (
            int(path.split('-')[1]),  # Sort based on '-82-', '-17-', etc.
            int(path.split('S')[1].split('-')[0]),  # Sort based on '007', '008', etc.
            int(path.split('-')[3])  # Sort based on '-1-', '-2-', etc.
            ))
    print(TextGrid_file_list)
    punct = [',', '.', '!', '?']  # maybe just . ! ?, for

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
    for each_file_name in TextGrid_file_list:  # loop through each .TextGrid
        # now combine the files of the same speakers
       # TODO: modify this to show the progress
        interval_num = 0
        file_path = each_file_name  # the complete path of .TextGrid file
        each_file_name = each_file_name.split('/')[-1]
        print(each_file_name)
        try:
            file_textgrid_obj = textgrid.TextGrid.fromFile(file_path)
        except UnicodeDecodeError:
            print(
                each_file_name +
                ': the encode is weird, not utf-8 or ansi')

        tier_list = file_textgrid_obj.tiers  # a list of tier names from the TextGrid

        for each_tier in tier_list:
            if each_tier.name == 'SWG':  # only read from SWG tier
                tier_swg = each_tier
                intervals_swg = tier_swg.intervals  # all the annotated intervals from
        try:
            clauses = []
            clause_annotation = []
            # skip = False
            begin_tag = ''
            type_label = 'interview'
            time_segment = dict()
            for each_annotation in intervals_swg:
                annotation_mark = each_annotation.mark
                beg_hms = timestamp_convert(each_annotation.minTime)
                # annotations
                if not annotation_mark.strip(): continue  # skip empty ones
                tokens = annotation_mark.split()
                print(f"Tokens: {tokens}")

                time_segment[beg_hms] = tokens

                for token in tokens:
                    # print("token", token)
                    if token in tags_for_skipping.keys():
                        # print("found", token)
                        # skip = True
                        begin_tag = token
                        type_label = tags_to_type[begin_tag]
                        # print("type_label", type_label)

                    if token in tags_for_skipping.values() and begin_tag != '':
                        if token == tags_for_skipping[begin_tag]:
                            # print("found end", token)
                            # skip = False
                            begin_tag = ''
                            type_label = 'interview'

                    # if not skip:
                    if any(p in token for p in punct):  # any punctuation in punct list is present in the token
                        if all(c in string.punctuation for c in
                               token):  # this is for token like ... --- and ???. All the character in this token is punctuation
                            if not clause_annotation:  # when no token is added to the current clause
                                time_stamp = beg_hms
                            clause_annotation.append(token)
                            if len(token) > 3:
                                clause_annotation.append(type_label)
                                clause_annotation.append(time_stamp)
                                clauses.append(clause_annotation)
                                # print("cl0", clause_annotation)
                                clause_annotation = []
                            continue

                        word_punct_split = re.findall(
                            r"[^\w\d\s,.!?]*\w+[^\w\d\s,.!?]*\w*[^\w\d\s,.!?]*\w*[^\w\d\s,.!?]*|[^\w\s]", token,
                            re.UNICODE)

                        for wp in word_punct_split:  # maybe to split annotations into clauses
                            if not clause_annotation:
                                time_stamp = beg_hms
                            clause_annotation.append(wp)
                            if all(c in punct for c in wp):
                                clause_annotation.append(type_label)
                                clause_annotation.append(time_stamp)
                                clauses.append(clause_annotation)
                                # print("cl1", clause_annotation)
                                clause_annotation = []
                            continue # TODO: this may not be necessary
                    else:
                        if not clause_annotation:
                            time_stamp = beg_hms
                        clause_annotation.append(token)
                        # print("cl3", clause_annotation)

                # where should this be?
                # if token in tags_for_skipping.values() and begin_tag != '':
                #     if token == tags_for_skipping[begin_tag]:
                #         # print("found end", token)
                #         # skip = False
                #         begin_tag = ''
                #         type_label = 'interview'

            if clause_annotation:
                clause_annotation.append(type_label)
                clause_annotation.append(time_stamp)
                clauses.append(clause_annotation)
                # print("cl2", clause_annotation)
                clause_annotation = []

            for cl in clauses:  # why do I need to put this into clauses, for skipping?
                # add the time stamp and word count first
                beg_hms = cl[-1]
                type_label = cl[-2]
                # print("time", beg_hms)
                cl = cl[:-2]
                # print("cl check", cl)
                if cl[0] not in time_segment[beg_hms]:  # closer remaining is the punctuation problem
                    # print("cl", cl)
                    # print("time_segment[beg_hms]", time_segment[beg_hms])
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
                swg_vv_list = []
                pos_vv_list = []
                # get ddm
                for i, word in enumerate(cl):
                    if word:  # empty word check
                        # match w with word_variant
                        std_list = OrderedSet()
                        ddm_list = OrderedSet()
                        pos_list = OrderedSet()
                        swg_vv = []
                        pos_vv = []
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
                                elif "was" in word or "wie" in word:
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
                                    if isinstance(values[2], float) and math.isnan(values[2]):  # check for empty var_code
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
                            if "VV" in pos:
                                swg_vv.append(word.strip())
                                pos_vv.append(pos.strip())
                        if rel:
                            ddm = ddm + rel_var
                            ddm = ddm.strip()
                    words_std.append(standard)
                    ddm_tags.append(ddm)
                    pos_sent.append(pos)
                    swg_vv_list.append(" ".join(swg_vv))
                    pos_vv_list.append(" ".join(pos_vv))
                # columns
                output_clauses_csv(extract_path, each_file_name[each_file_name.rfind("_") + 1:-9], beg_hms, sym_seq,
                                   " ".join(cl),
                                   " ".join(ddm_tags),
                                   " ".join(pos_sent),
                                   " ".join(swg_vv_list),
                                   " ".join(pos_vv_list),
                                   type_label)
                # format the output
                # skip the story
        except AttributeError as e:
            print(
                each_file_name +
                ': tier words is empty or does not exist ')
            traceback.print_tb(e.__traceback__)

#
# def timestamp_convert(ts): # TODO: could import this from the utils
#     ts_list = str(ts).split('.')
#     remaining_seconds = int(ts_list[0])
#     ms = int(ts_list[1])
#     hour = 0
#     minute = 0
#     if remaining_seconds >= 3600:
#         hour = remaining_seconds // 3600
#         remaining_seconds = remaining_seconds - (hour * 3600)
#     if remaining_seconds >= 60:
#         minute = remaining_seconds // 60
#         remaining_seconds = remaining_seconds - (minute * 60)
#     second = remaining_seconds
#     # could try gmtime or other python time function
#     timestamp = datetime.time(hour, minute, second, ms).strftime('%H:%M:%S.%f')
#     return timestamp


# if __name__ == '__main__':
#     date = '20220214'
#     types = 'noSocialInfo' + '.csv'
#     working_directory = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
#     extract_type = 'clauses'
#     # speaker_tg_path_dict = {}
#     # speaker_tg_path_dict = {
#     #  'SWG_trend_'+ extract_type + '_' + date + types: [working_directory + 'trend_tg/']}
#     # speaker_tg_path_dict = {'SWG_style_' + extract_type + '_' + date + types: [working_directory + 'style_tg/']}
#     speaker_tg_path_dict = {'SWG_trend_' + extract_type + '_' + date + types: [working_directory + 'trend_tg/'],
#                             'SWG_panel_clauses_' + date + types: [working_directory + 'recovery_1982/',
#                                                                   working_directory + 'recovery_2017/']}
#     lex_table_path = working_directory + "SG-LEX 12feb2021.csv"
#
#     for extract_name in speaker_tg_path_dict.keys():
#         for tg_path in speaker_tg_path_dict[extract_name]:
#             extract_path = working_directory + extract_name
#             transform = Transform(tg_path, extract_path, lex_table_path)
#             transform.start()
