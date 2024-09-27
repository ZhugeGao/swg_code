"""This is the main SWG script that the user interacts with."""
from nltk import CoreNLPParser

from SWG_utils import *
from TextGrid_preparation.Eaf2TextGrid import eaf_to_TextGrid
from TextGrid_preparation.step00_file_manipulation import get_file_paths, read_speakers, relocating_files_by_speaker, \
    rename_file, file_are_in_pairs
from add_social_info_to_csv import add_social_info_to_extracts
from extracts.clauses_rel_extract import create_rel_clauses_extract
from extracts.formants_extract import create_formants_extract, create_raw_formants_extract
from extracts.phones_extract import create_phones_extract
from extracts.words_extract import *
from extracts.clauses_extract import *

# TODO: reorganize the order of all these input information, putting the ones requires frequent modifications at the
#  front
from lex_table_fix import fix_lex_table

date = '20240901'  # the processing date. format: yyyymmdd
# NOTE: the date needs tobe the same for all the extracts.
lex_table_name = "SG-LEX 10jun2024" # the name of the lex table before count update. format: SG-LEX ddMMMyyyy
lex_table_type = ".xlsx"  # the type of the lex table. format: .xlsx or .csv
speaker_file_date = "01jul2024"  # format:ddMMMyyyy

speaker_groups = ["test"]  # "panel" ,"trend", "style" "test"

# extract_types: a list of all the extracts name so that it would run automatically everything in proper sequence
extract_types = ["words", "clauses_rel", "clauses", "phones", "formants"]  # for processing everything all at once
# "clauses_rel", "words", "clauses", "phones","formants"
extract_type = "clauses"

# TODO: automation and pay attention to the formants extract


# if new Elan, audio file are downloaded from Google Drive, then set this to True to move the downloaded files to the corresponding directories.
move_downloaded_files = False
# boolean switches: if True, will turn the .xlsx lex table spread sheet to a .csv formant lex table and updates it
fix_lex = False # fix the lex table and turn the .xslx file to .csv file. This only needs to be done once for a new version of the lex table.
Elan_to_TextGrid = False  # boolean switches: if True, will turn the .eaf files to .TextGrid files

# update speaker file with TexiGrid names. This needs to be done only once for each speaker file.
# Updated speaker files are needed before moving the downloaded files to the corresponding directories.
update_speaker_file = False # TODO: might be obeselete

run_extract = True # if True, will run the extract processing part

# TODO: This is a [REMINDER]. Remember to change target_var_code for Formants extract
# ONLY used when extract_type is "formants"
no_target = False # if True, then there is no target, whatever the setting for the following variables are, they will not be used.
# ONLY used when no_target is False
target_is_var_code = False # if True, then the target variable is a variable code, otherwise it is a list of phones
target_var_code_formants = "ANN" # this is the target variable code for formants extract, not relevant for other extract types.
target_phones = ['a', 'aː'] # this is the target phones for formants extract, not relevant for other extract types.

if extract_type == "formants" and target_is_var_code: # if the extract type is formants, then add the target_var_code to the extract type
    # global extract_type
    extract_type = extract_type + "_" + target_var_code_formants

pos_tagger = CoreNLPParser('http://localhost:9002', tagtype='pos')

types = 'noSocialInfo' + '.csv'

unprocessed_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/unprocessed/'  # path to the unprocessed files

os.chdir(working_directory) # change the working directory to the one where all the swg data and processing is happening
# speaker setting
# speaker group that is relevant for the processing

# speaker_file_dict: a mapping from speaker type to speaker file name
speaker_file_dict = {"panel": "panel/" + "SWG_panel_speakers_" + speaker_file_date + ".csv",
                     "trend": "trend/" + "SWG_trend_speakers_" + speaker_file_date + ".csv"}
# TODO: all the TextGrid file paths, work with selectors(lists)
speaker_TextGrid_dict = {"trend": [working_directory + "trend/TextGrid/"],
                         "panel": [working_directory + "panel/TextGrid/1982/",
                                   working_directory + "panel/TextGrid/2017/"]} # , "style": [working_directory + "style/TextGrid/"]}
speaker_done_path = {'panel': [working_directory + "panel/formant_extracts_data/1982/",
                               working_directory + "panel/formant_extracts_data/2017/"],
                     'trend': [working_directory + "trend/formant_extracts_data/"]}

# the one above can be merged. speaker: files.
# different variables representing the date.


"""The following part is for the automatic processing of .eaf files to .TextGrid files. All the .TextGrid files need to be validated before moving on to the extract processing step."""
# turn Eaf files to TextGrid files
elans_tgs = {working_directory + "trend/Elan/": working_directory + "trend/TextGrid/",
             working_directory + "panel/Elan/1982/": working_directory + "panel/TextGrid/1982/",
             working_directory + "panel/Elan/2017/": working_directory + "panel/TextGrid/2017/"}



tags = {'[BEGIN-READING]': '[END-READING]', '[BEGIN-WORD-LISTS]': '[END-WORD-LISTS]',
        '[BEGIN-WORD-GAMES]': '[END-WORD-GAMES]'} # tags for skipping the reading, word lists and word games parts



if update_speaker_file: # if True, will update the speaker file with the TextGrid file names
    for speaker_type in speaker_groups:
        add_file_id_col(speaker_type, speaker_TextGrid_dict[speaker_type], speaker_file_date)

if Elan_to_TextGrid:
    selected_tier = ['SWG', 'TOP']  # put the selected tiers' name here , 'ITW', 'STY', 'INT'
    '''if you want to keep all tiers, leave it as an empty list: tier_selected = []
    the result might not have the same order
    the rest of the program'''
    all_tier_names = []

    eaf_to_TextGrid(elans_tgs, selected_tier, all_tier_names)  # run the eaf to TextGrid conversion

if move_downloaded_files:
    # step00: moving downloaded files to the corresponding directories
    # the downloaded files need to have the same name as the corresponding TextGrid files and it should be in the updated speaker files under the column "trans_id"
    downloads_directory = "drive_downloads"  # name of the directory where all the downloaded files are. It can contain subdirectories.
    # file_type = ".eaf"
    file_types = [".eaf", ".wav"]  # for downloaded .eaf and .wav files from Google Drive.
    for file_type in file_types:
        if file_type == ".wav":
            rename_file('.WAV', '.wav',
                        downloads_directory)  # rename all the file extension for wav audio files downloaded from Google Drive.
        files_paths = get_file_paths(downloads_directory, filetype=file_type) # get all the file paths for the downloaded files
        speaker_files = [speaker_file_dict[s] for s in speaker_groups] #
        trans_id_speaker_dict = read_speakers(speaker_files)
        relocating_files_by_speaker(working_directory, downloads_directory, trans_id_speaker_dict, files_paths, file_type)

# check pairs: .wav, .TextGird

# def file_manipulation_pipeline(working_directory, downloads_directory, file_type, speakers=speakers,
#                                speaker_file_dict=speaker_file_dict):
#     os.chdir(working_directory)
#     type_target = {'.eaf': '_elan/', '.TextGrid': '_tg/', '.wav': '_wav/'}
#     # must put every file into this folder
#     files_paths = get_file_paths(downloads_directory, filetype=file_type)
#      . a further helper method for that


# run word extract
# TODO: is this a good way to manage paths? Should this be generalized to other types of extract as well?
# TODO: figure out a more unified ways to manage paths
speaker_tg_path_dict = {
    'test' : [working_directory + "test/TextGrid/"], # for testing purposes
    'trend': [working_directory + "trend/TextGrid/"],
    'panel': [working_directory + "panel/TextGrid/1982/", working_directory + "panel/TextGrid/2017/"]}
# TODO: change the name of the dictionary to reflect what it is doing
speaker_tg_path_phones_dict = {
    'panel': [working_directory + "panel/formant_extracts_data/1982/", working_directory + "panel/formant_extracts_data/2017/"],
    'trend': [working_directory + "trend/formant_extracts_data/"]}

# lex table

lex_path = working_directory + lex_table_name + "_updated_counts" +".csv"
input_file_lex = working_directory + lex_table_name + lex_table_type  # always use the newer version

if fix_lex:  # this is for fixing the lex_table and output it as a .csv file
    word_counter, file_words_map, file_time_seg_map = read_tg_files(all_speaker_paths)
    lex = read_lex_table(input_file_lex)
    fix_lex_table(lex, word_counter, lex_path, date)  # TODO: fix and run lex_table_fix


lex_table = read_lex_table(lex_path)

# TODO: need to specify this at the beginning of the file, maybe a dict from speaker group to speaker file name
def add_social_information_to_extracts(working_directory, speaker_type, speaker_file_date, extract_type, date, types):
    # TODO: maybe just let the method be called directly
    # this would not work for formants extract
    extract_input_path = working_directory + speaker_type + "/extracts/" + 'SWG_' + speaker_type + '_' + extract_type + '_' + date + types
    speaker_file_path = working_directory + speaker_type + "/" +'SWG_' + speaker_type + '_speakers_' + speaker_file_date + '.csv'  # need to change in case date changes
    extract_output_path = working_directory + speaker_type + "/extracts/" +'SWG_' + speaker_type + '_' + extract_type + '_' + date + '.csv'
    print(extract_type)
    add_social_info_to_extracts(extract_input_path, speaker_file_path, extract_output_path)  # change names
    # TODO: give a extracts_output_path here and remove the relevant part in add_social_info_to_csv file.
if run_extract:
    for speaker_type in speaker_groups:
        extract_path = working_directory + speaker_type + "/extracts/" + 'SWG_' + speaker_type + '_' + extract_type + '_' + date + types

        if extract_type == "words":  # TODO: modify words_extract for additional columns
            # TODO: modify to only work for speaker_type in speakers
            # TODO: speaker_tg_path_dict changed key to speaker types
            word_extract_path = extract_path
            _, file_words_map, file_time_seg_map = read_tg_files(speaker_tg_path_dict[speaker_type])
            create_word_csv(speaker_tg_path_dict[speaker_type], word_extract_path, lex_table, file_words_map,
                            file_time_seg_map, pos_tagger)
        # TODO: modify to only work for speaker_type in speakers
        if extract_type == "clauses":
            create_clauses_extract(extract_path, speaker_tg_path_dict[speaker_type], lex_table, pos_tagger)
        # TODO: modify to only work for speaker_type in speakers
        # # TODO : if clauses merged identical functionalities. Then use if "clauses" in
        # if extract_type == "clauses_rel":
        #     for extract_path in speaker_tg_path_dict.keys():
        #         for tg_path in speaker_tg_path_dict[extract_path]:
        #             create_rel_clauses_extract(extract_path, tg_path, lex_table, pos_tagger)
        #
        if extract_type == "phones":
            for speaker_type in speaker_groups:
                for phones_data_path in speaker_tg_path_phones_dict[speaker_type]:
                    create_phones_extract(extract_path, phones_data_path, lex_table, pos_tagger)
                add_previous_following(extract_path, extract_type)

        if "formants" in extract_type:
              # make sure that all the TextGrid has a .Formant file. The praat script sometimes broke before finishing
            # TODO: modify to only work for speaker_type in speakers
            phones_extract_path = working_directory + speaker_type + '/extracts/' + 'SWG_' + speaker_type + '_' + 'phones' + '_' + date + '.csv'
            formants_raw_extract_path = working_directory + speaker_type + '/extracts/' + 'SWG_' + speaker_type + '_' + 'formants_raw' + '_' + date + '.csv'
            formants_extract_output_path = working_directory + speaker_type + '/extracts/' + 'SWG_' + speaker_type + '_' + extract_type + '_' + date + types

            formant_data_paths = speaker_tg_path_phones_dict[speaker_type]

            proceed = file_are_in_pairs('.TextGrid', '.Formant', formant_data_paths)

            if proceed:
                if target_is_var_code:
                    create_raw_formants_extract(phones_extract_path, formants_raw_extract_path,
                                        target_var_code_formants)
                else:
                    create_raw_formants_extract(phones_extract_path, formants_raw_extract_path, target_phones,
                                                target_is_var_code)

                if no_target:
                    formants_raw_extract_path = phones_extract_path

                create_formants_extract(formant_data_paths, phones_extract_path, formants_raw_extract_path,
                                        formants_extract_output_path)


        # finally add social information to the extract
        add_social_information_to_extracts(working_directory, speaker_type, speaker_file_date, extract_type, date, types)
