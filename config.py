"""
Configuration file for the SWG processing pipeline.
All user-configurable settings should be here.
"""
# For now, we keep the original to ensure the refactoring step is isolated.
working_directory = "/Users/zhugegao/Documents/SWG/"  # This will be made dynamic later.

# TODO: reorganize the order of all these input information, putting the ones requires frequent modifications at the
#  front

date = '20250313'  # the processing date. format: yyyymmdd
# NOTE: the date needs tobe the same for all the extracts.
lex_table_name = "SG-LEX 10jun2024" # the name of the lex table before count update. format: SG-LEX ddMMMyyyy
lex_table_type = ".xlsx"  # the type of the lex table. format: .xlsx or .csv
speaker_file_date = "01jul2024"  # format:ddMMMyyyy

speaker_groups = ["panel" ,"trend", "style"]  # "style" "test"

# extract_types: a list of all the extracts name so that it would run automatically everything in proper sequence
extract_types = ["words", "clauses_rel", "clauses", "phones", "formants"]  # for processing everything all at once
# "clauses_rel", "words", "clauses", "phones","formants"
extract_type = "clauses"

# TODO: automation and pay attention to the formants extract


# if new Elan, audio file are downloaded from Google Drive, then set this to True to move the downloaded files to the corresponding directories.
move_downloaded_files = False
# boolean switches: if True, will turn the .xlsx lex table spread sheet to a .csv formant lex table and updates it
fix_lex = False # fix the lex table and turn the .xslx file to .csv file. This only needs to be done once for a new version of the lex table.
Elan_to_TextGrid = False # boolean switches: if True, will turn the .eaf files to .TextGrid files
check_tg = False # boolean switches: if True, will check the .TextGrid files for correctness

# update speaker file with TexiGrid names. This needs to be done only once for each speaker file.
# Updated speaker files are needed before moving the downloaded files to the corresponding directories.
update_speaker_file = False # TODO: might be obeselete

run_extract = True # if True, will run the extract processing part

add_social_info = False # if True, will add social information to the extract. This could be individually turned off or on.

# TODO: This is a [REMINDER]. Remember to change target_var_code for Formants extract
# ONLY used when extract_type is "formants"
no_target = False # if True, then there is no target, whatever the setting for the following variables are, they will not be used.
# ONLY used when no_target is False
target_is_var_code = False # if True, then the target variable is a variable code, otherwise it is a list of phones
target_var_code_formants = "ANN" # this is the target variable code for formants extract, not relevant for other extract types.
target_phones = ['a', 'aː'] # this is the target phones for formants extract, not relevant for other extract types.

types = 'noSocialInfo' + '.csv'

unprocessed_path = '/Users/gaozhuge/Documents/SWG/unprocessed/'  # path to the unprocessed files

# speaker setting
# speaker group that is relevant for the processing

# speaker_file_dict: a mapping from speaker type to speaker file name
# TODO: could this be simplified?
speaker_file_dict = {"panel": "panel/" + "SWG_panel_speakers_" + speaker_file_date + ".csv",
                     "trend": "trend/" + "SWG_trend_speakers_" + speaker_file_date + ".csv"}
# TODO: all the TextGrid file paths, work with selectors(lists)
speaker_TextGrid_dict = {"trend": [working_directory + "trend/TextGrid/"],
                         "panel": [working_directory + "panel/TextGrid/1982/",
                                   working_directory + "panel/TextGrid/2017/"],
                         "style": [working_directory + "style/TextGrid/"]}

all_speaker_paths = [working_directory + "panel/TextGrid/1982/", working_directory + "panel/TextGrid/2017/",
                     working_directory + "trend/TextGrid/"] # , working_directory + "style/TextGrid/"

speaker_Elan_TextGrid_dict = {"trend": [(working_directory + "trend/Elan/", working_directory + "trend/TextGrid/")],
                              "panel": [(working_directory + "panel/Elan/1982/", working_directory + "panel/TextGrid/1982/"),
                                        (working_directory + "panel/Elan/2017/", working_directory + "panel/TextGrid/2017/")],
                              "style": [(working_directory + "style/Elan/", working_directory + "style/TextGrid/")]}
all_textgrid_paths = [path for paths in speaker_TextGrid_dict.values() for path in paths]

speaker_done_path = {'panel': [working_directory + "panel/formant_extracts_data/1982/",
                               working_directory + "panel/formant_extracts_data/2017/"],
                     'trend': [working_directory + "trend/formant_extracts_data/"]}
# TODO: is this a good way to manage paths? Should this be generalized to other types of extract as well?
# TODO: figure out a more unified ways to manage paths
# TODO: change the name of the dictionary to reflect what it is doing
speaker_tg_path_phones_dict = {
    'panel': [working_directory + "panel/formants/1982/", working_directory + "panel/formants/2017/"],
    'trend': [working_directory + "trend/formants/"]}

# the one above can be merged. speaker: files.
# different variables representing the date.

# turn Eaf files to TextGrid files
# TODO: these are not used anymore, delete them?
elans_tgs = {working_directory + "trend/Elan/": working_directory + "trend/TextGrid/",
             working_directory + "panel/Elan/1982/": working_directory + "panel/TextGrid/1982/",
             working_directory + "panel/Elan/2017/": working_directory + "panel/TextGrid/2017/",
             working_directory + "style/Elan/": working_directory + "style/TextGrid/"}
