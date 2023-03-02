"""This is the main SWG script that the user interacts with."""
from nltk import CoreNLPParser

from SWG_utils import *
from add_social_info_to_csv import add_social_info_to_extracts
from extracts.clauses_rel_extract import create_rel_clauses_extract
from extracts.formants_extract import create_formants_extract
from extracts.phones_extract import create_phones_extract
from extracts.words_extract import *
from extracts.clauses_extract import *

# TODO: reorganize the order of all these input information, putting the ones requires frequent modifications at the
#  front
from lex_table_fix import fix_lex_table

lex_table_name = "SG-LEX 12feb2021"
speaker_date = '30may2021'

working_directory = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/"  # name of the directory where all the swg data and processing is happening
# also called common_path in some script.
# common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
os.chdir(working_directory)
# speaker setting
# speaker group that is relevant for the processing
speakers = ["panel", "twin", "trend"]  # ,"style"
# TODO: all the TextGrid file paths, work with selectors(lists)
speaker_TextGrid_dict = {"trend": [working_directory + 'trend_tg/'], "twin": [working_directory + 'twin_tg/'],
                         "panel": [
                             working_directory + 'panel_tg/']}  # TODO: why is this panel_tg thing a single one? why?
speaker_done_path = {'panel': [working_directory + 'done_panel/1982/', working_directory + 'done_panel/2017/'],
                     'twin': [working_directory + 'done_twin/'], 'trend': [working_directory + 'done_trend/']}
# TODO: what is the difference between "recovery_1982" and "done_panel/1982/" done is .Formant files
all_speaker_paths = [working_directory + "recovery_1982/", working_directory + "recovery_2017/",
                     working_directory + "trend_tg/",
                     working_directory + "twin_tg/", working_directory + "style_tg/"]
# the one above can be merged. speaker: files.
# different variables representing the date.
speaker_file_date = "30may2021"  # format:ddMMyyyy
speaker_date = '30may2021'  # TODO: this? why this. This is the same as speaker_file_date. Unify this.
date = '20220310'  # this might represent the processing date
# "clauses_rel", "words", "clauses","phones",
extract_type = "formants"
# TODO: remember to change target_var_code for Formants extract
target_var_code_formants = "LEO"

# tags for skipping the reading, word lists and word games parts
tags = {'[BEGIN-READING]': '[END-READING]', '[BEGIN-WORD-LISTS]': '[END-WORD-LISTS]',
        '[BEGIN-WORD-GAMES]': '[END-WORD-GAMES]'}
# step00: moving downloaded data to the right directory

pos_tagger = CoreNLPParser('http://localhost:9002', tagtype='pos')

# downloads_directory = "zips"  # name of the directory where all the downloaded files are. It can contain sub-directories.
# file_type = ".eaf"


# TODO: a list of all the extracts name so that it would run automatically everything in proper sequence

types = 'noSocialInfo' + '.csv'

# TODO: there needs to be a place where all the boolean switch variables are. It should be at the top of the file(maybe after the input strings)
update_speaker_file = False
# update speaker file with TexiGrid names
if update_speaker_file:
    for speaker_type in speakers:
        add_file_id_col(speaker_type, speaker_TextGrid_dict[speaker_type], speaker_file_date)

# run word extract
# TODO: is this a good way to manage paths? Should this be generalized to other types of extract as well?
speaker_tg_path_dict = {
    # working_directory + 'SWG_trend_' + extract_type + '_' + date + types: [working_directory + 'trend_tg/'],
    # working_directory + 'SWG_twin_' + extract_type + '_' + date + types: [working_directory + 'twin_tg/'],
    working_directory + 'SWG_panel_' + extract_type + '_' + date + types: [working_directory + 'recovery_1982/',
                                                                           working_directory + 'recovery_2017/']}
speaker_tg_path_phones_dict = {
    'panel': [working_directory + 'done_panel/1982/', working_directory + 'done_panel/2017/'],
    'twin': [working_directory + 'done_twin/'], 'trend': [working_directory + 'done_trend/']}

# lex table

lex_path = working_directory + lex_table_name + ".csv"
input_file_lex = working_directory + lex_table_name + ".xlsx"  # always use the newer version

fix_lex = True
if fix_lex:  # this is for fixing the lex_table and output it as a .csv file TODO: For what? what does this mean?
    word_counter, file_words_map, file_time_seg_map = read_tg_files(all_speaker_paths)
    lex = read_lex_table(input_file_lex)
    fix_lex_table(lex, word_counter, lex_path, date)  # TODO: fix and run lex_table_fix

lex_table = read_lex_table(lex_path)

if extract_type == "words":  # TODO: modify words_extract
    for speaker_path in speaker_tg_path_dict.keys():  # speaker should be refactored to extract
        word_extract_path = speaker_path  # maybe pass this as argument?, change it to a path
        _, file_words_map, file_time_seg_map = read_tg_files(speaker_tg_path_dict[speaker_path])
        create_word_csv(speaker_tg_path_dict[speaker_path], word_extract_path, lex_table, file_words_map,
                        file_time_seg_map, pos_tagger)

if extract_type == "clauses":
    for extract_path in speaker_tg_path_dict.keys():
        for tg_path in speaker_tg_path_dict[extract_path]:
            create_clauses_extract(extract_path, tg_path, lex_table, pos_tagger)

# TODO : if clauses merged identical functionalities. Then use if "clauses" in
if extract_type == "clauses_rel":
    for extract_path in speaker_tg_path_dict.keys():
        for tg_path in speaker_tg_path_dict[extract_path]:
            create_rel_clauses_extract(extract_path, tg_path, lex_table, pos_tagger)

if extract_type == "phones":
    for extract_path in speaker_tg_path_phones_dict.keys():
        for phones_data_path in speaker_tg_path_phones_dict[extract_path]:
            create_phones_extract(extract_path, phones_data_path, lex_table, pos_tagger)
        add_previous_following(extract_path, extract_type)

if extract_type == "formants":
    for speaker_type in speakers:
        phones_extract_path = working_directory + 'SWG_' + speaker_type + '_' + 'phones' + '_' + date + '.csv'
        formants_raw_extract_path = working_directory + 'SWG_' + speaker_type + '_' + 'formants_raw' + '_' + date + '.csv'
        formants_extract_output_path = working_directory + 'SWG_' + speaker_type + '_' + 'formants' + '_' + target_var_code_formants + '_' + date + types

        formant_data_path = working_directory + 'done_' + speaker_type + '/'
        create_formants_extract(formant_data_path, phones_extract_path, formants_raw_extract_path,
                                formants_extract_output_path, target_var_code_formants)


# TODO: need to specify this at the beginning of the file, maybe a dict from speaker group to speaker file name
def add_social_information_to_extracts():
    # TODO: maybe just let the method be called directly
    # this would not work for formants extract
    extract_input_path = working_directory + 'SWG_' + speaker_type + '_' + extract_type + '_' + date + types
    speaker_file_path = working_directory + 'SWG_' + speaker_type + '_speakers_' + speaker_date + '.csv'  # need to change in case date changes
    extract_output_path = working_directory + 'SWG_' + speaker_type + '_' + extract_type + '_' + date + '.csv'
    add_social_info_to_extracts(extract_input_path, speaker_file_path, extract_output_path)  # change names
    # TODO: give a extracts_output_path here and remove the relevant part in add_social_info_to_csv file.
