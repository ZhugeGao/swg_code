"""This is the main SWG script that the user interacts with."""

import config
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
 
if config.extract_type == "formants" and config.target_is_var_code: # if the extract type is formants, then add the target_var_code to the extract type
    # global extract_type
    config.extract_type = config.extract_type + "_" + config.target_var_code_formants

pos_tagger = CoreNLPParser('http://localhost:9002', tagtype='pos')

os.chdir(config.working_directory) # change the working directory to the one where all the swg data and processing is happening


"""The following part is for the automatic processing of .eaf files to .TextGrid files. All the .TextGrid files need to be validated before moving on to the extract processing step."""


if config.update_speaker_file: # if True, will update the speaker file with the TextGrid file names
    for speaker_type in config.speaker_groups:
        add_file_id_col(speaker_type, config.speaker_TextGrid_dict[speaker_type], config.speaker_file_date)       

if config.move_downloaded_files:
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
        speaker_files = [config.speaker_file_dict[s] for s in config.speaker_groups] #
        trans_id_speaker_dict = read_speakers(speaker_files)
        relocating_files_by_speaker(config.working_directory, downloads_directory, trans_id_speaker_dict, files_paths, file_type)

if config.Elan_to_TextGrid:
    selected_tier = ['SWG', 'TOP']  # put the selected tiers' name here , 'ITW', 'STY', 'INT'
    # TODO: Is this the correct way to select all tiers now?
    # '''if you want to keep all tiers, leave it as an empty list: tier_selected = []
    # the result might not have the same order
    # the rest of the program'''
    # all_tier_names = []
    for speaker_type in config.speaker_groups:
        eaf_to_TextGrid(config.speaker_Elan_TextGrid_dict[speaker_type], selected_tier)  # run the eaf to TextGrid conversion
    config.check_tg = True # check the TextGrid files for correctness automatically after conversion
    
if config.check_tg:
    for speaker_type in config.speaker_groups:
        for textgrid_path in config.speaker_TextGrid_dict[speaker_type]:
            find_skip_label(textgrid_path)
 

# check pairs: .wav, .TextGird

# def file_manipulation_pipeline(working_directory, downloads_directory, file_type, speakers=speakers,
#                                speaker_file_dict=speaker_file_dict):
#     os.chdir(working_directory)
#     type_target = {'.eaf': '_elan/', '.TextGrid': '_tg/', '.wav': '_wav/'}
#     # must put every file into this folder
#     files_paths = get_file_paths(downloads_directory, filetype=file_type)
#      . a further helper method for that


# run word extract
# lex table

lex_path = config.working_directory + config.lex_table_name + "_updated_counts" +".csv"
input_file_lex = config.working_directory + config.lex_table_name + config.lex_table_type  # always use the newer version


if config.fix_lex:  # this is for fixing the lex_table and output it as a .csv file
    word_counter, file_words_map, file_time_seg_map = read_tg_files(config.all_speaker_paths)
    lex = read_lex_table(input_file_lex)
    fix_lex_table(lex, word_counter, lex_path, config.date)  # TODO: fix and run lex_table_fix

lex_table = read_lex_table(lex_path)

   

if config.run_extract:
    for speaker_type in config.speaker_groups:
        print("Running " + speaker_type + " " + config.extract_type + " extract")
        extract_path = config.working_directory + speaker_type + "/extracts/" + 'SWG_' + speaker_type + '_' + config.extract_type + '_' + config.date + config.types

        if config.extract_type == "words":  # TODO: modify words_extract for additional columns
            # TODO: modify to only work for speaker_type in speakers
            word_extract_path = extract_path
            _, file_words_map, file_time_seg_map = read_tg_files(config.speaker_TextGrid_dict[speaker_type])
            create_word_csv(config.speaker_TextGrid_dict[speaker_type], word_extract_path, lex_table, file_words_map,
                            file_time_seg_map, pos_tagger)
        # TODO: modify to only work for speaker_type in speakers
        if config.extract_type == "clauses":
            create_clauses_extract(extract_path, config.speaker_TextGrid_dict[speaker_type], lex_table, pos_tagger)

        if config.extract_type == "clauses_rel":
            for tg_path in config.speaker_TextGrid_dict[speaker_type]:
                print(f"\nProcessing TextGrids in {tg_path}")
                create_rel_clauses_extract(extract_path, tg_path, lex_table, pos_tagger)

        if config.extract_type == "phones":
            for speaker_type in config.speaker_groups:
                for phones_data_path in config.speaker_tg_path_phones_dict[speaker_type]:
                    create_phones_extract(extract_path, phones_data_path, lex_table, pos_tagger)
                add_previous_following(extract_path, config.extract_type)

        if config.extract_type == "formants" :
              # make sure that all the TextGrid has a .Formant file. The praat script sometimes broke before finishing
            # TODO: modify to only work for speaker_type in speakers
            phones_extract_path = config.working_directory + speaker_type + '/extracts/' + 'SWG_' + speaker_type + '_' + 'phones' + '_' + config.date + '.csv'
            formants_raw_extract_path = config.working_directory + speaker_type + '/extracts/' + 'SWG_' + speaker_type + '_' + 'formants_raw' + '_' + config.date + '.csv'
            formants_extract_output_path = config.working_directory + speaker_type + '/extracts/' + 'SWG_' + speaker_type + '_' + config.extract_type + '_' + config.date + config.types

            formant_data_paths = config.speaker_tg_path_phones_dict[speaker_type]

            proceed = file_are_in_pairs('.TextGrid', '.Formant', formant_data_paths)

            if proceed:
                if config.target_is_var_code:
                    create_raw_formants_extract(phones_extract_path, formants_raw_extract_path,
                                        config.target_var_code_formants)
                else:
                    create_raw_formants_extract(phones_extract_path, formants_raw_extract_path, config.target_phones,
                                                config.target_is_var_code)

                if config.no_target:
                    formants_raw_extract_path = phones_extract_path

                create_formants_extract(formant_data_paths, phones_extract_path, formants_raw_extract_path,
                                        formants_extract_output_path)

if config.add_social_info:
    # finally add social information to the extract
    # TODO: maybe just let the method be called directly
    # TODO: would this work for formants extract? What modifications are needed?
    for speaker_type in config.speaker_groups:
        extract_input_path = config.working_directory + speaker_type + "/extracts/" + 'SWG_' + speaker_type + '_' + config.extract_type + '_' + config.date + config.types
        speaker_file_path = config.working_directory + speaker_type + "/" +'SWG_' + speaker_type + '_speakers_' + config.speaker_file_date + '.csv'  # need to change in case date changes
        extract_output_path = config.working_directory + speaker_type + "/extracts/" +'SWG_' + speaker_type + '_' + config.extract_type + '_' + config.date + '.csv'
        
        print("Adding social information to the extract...")
        add_social_info_to_extracts(extract_input_path, speaker_file_path, extract_output_path)  # change names

        print("Cleaning empty rows from extract...")
        if config.extract_type == "words":
            clean_empty_column_rows(extract_output_path, 'Word_SWG', extract_output_path)
        elif config.extract_type == "clauses":
            clean_empty_column_rows(extract_output_path, 'swg_clause', extract_output_path)
        elif config.extract_type == "clauses_rel":
            clean_empty_column_rows(extract_output_path, 'swg_clause', extract_output_path)        # TODO: add phones and formants extract
