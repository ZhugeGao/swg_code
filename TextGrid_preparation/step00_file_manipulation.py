import glob
import os
import re

import pandas as pd


def get_file_paths(root_directory, filetype=''):
    """this method will return a dictionary with all the name of files in this directory and sub-directories as key
    and it's path as value."""
    files_paths = {}
    for root, dirs, files in os.walk(root_directory):
        if dirs:
            continue
        if files:
            current_path = root
            for file in files:
                if file not in files_paths.keys() and file.endswith(filetype):
                    files_paths[file] = current_path + '/'
    return files_paths


def read_speakers(speaker_files):
    """this method reads in speaker files and return a dictionary with trans_id as key and corresponding
    speaker as value."""
    print("Reading in speaker files...")
    trans_id_speaker_dict = {}
    for speaker in speaker_files:
        speaker_type = speaker.split('_')[1]
        df_spker = pd.read_csv(speaker)
        # the list of file names for the speaker
        speaker_list = [x for x in list(df_spker['trans_id']) if str(x) != 'nan']  # nan in the list
        for spk in speaker_list:
            trans_id_speaker_dict[spk] = speaker_type
    return trans_id_speaker_dict


def relocating_files_by_speaker(working_directory, downloads_directory, trans_id_speaker_dict, files_paths, file_type):
    """this method will match all the filenames with the trans_id, and put the file into corresponding speaker
    directory if there is a match. If there is not a match, the file will be put into the unprocessed"""
    print("Relocating files...")
    unprocessed_path = working_directory + downloads_directory + '/'  # all the unmatched files will be put in this directory
    manual_path = working_directory + "manual" + "/"
    type_target = {'.eaf': 'Elan/', '.TextGrid': 'TextGrid/', '.wav': 'wav/'}
    for file in files_paths.keys():
        file_path = working_directory + files_paths[file] + file
        trans_id = file.replace(file_type, '')
        if len(trans_id.split('-')) > 5:
            trans_id = '-'.join(trans_id.split('-')[:5])
            file = trans_id + file_type
        if trans_id in trans_id_speaker_dict.keys():
            speaker_type = trans_id_speaker_dict[trans_id]
            speaker_path = working_directory + speaker_type + "/" + type_target[file_type]
            if speaker_type == "panel":  # panel has sub directories: /1982 and /2017
                if "-17-" in trans_id:
                    speaker_path = speaker_path + "2017/"
                elif "-82-" in trans_id:
                    speaker_path = speaker_path + "1982/"
            os.rename(file_path, speaker_path + file)
        elif "_" in file:
            os.rename(file_path, manual_path + file)
        else:
            os.rename(file_path, unprocessed_path + file)


def rename_file(old_file_name, new_file_name, root_directory):
    """this method can rename file. Given a substring of the old file name and a new string, this method will replace
    the old string with the new string. Here it is used to change file types."""
    for filename in glob.iglob(os.path.join(root_directory, '*' + old_file_name)):
        print("Renamed file:", filename)
        new_file_name = filename.replace(old_file_name, new_file_name)
        os.rename(filename, new_file_name)

def file_are_in_pairs(filetype1, filetype2, list_of_directory):
    """this method will check if the two types of files in the same directory are in pairs. If not, it will return False."""
    pairs = True
    for directory in list_of_directory:
        filetype1_missing_list, filetype2_missing_list = match_file_pair(filetype1, filetype2, directory)
        if any(filetype1_missing_list) or any(filetype2_missing_list):
            print("Files are not in pairs.")
            pairs = False
    return pairs

def match_file_pair(filetype1, filetype2, directory):
    """In the same directory, check if there are two files with the same file name and two file types. """
    ft1 = [fn.replace(filetype1, '') for fn in glob.iglob(os.path.join(directory, '*' + filetype1))]
    ft2 = [fn.replace(filetype2, '') for fn in glob.iglob(os.path.join(directory, '*' + filetype2))]
    print("Missing", filetype1 + ":", sorted(list(set(ft2) - set(ft1))))
    print("Missing", filetype2 + ":", set(ft1) - set(ft2))
    return sorted(list(set(ft2) - set(ft1))), sorted(list(set(ft1) - set(ft2)))


# a helper method to extract only the title
def extract_speaker_file_name(file_name):
    p = re.compile(r'S[0-9]+-')
    m = re.search(p, file_name)
    return m.group(0)

#
# # TODO: run this also in swg_main
working_directory = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/"
os.chdir(working_directory)
#
w, f = match_file_pair(".Formant", ".wav", "panel/formant_extracts_data/2017/")
# s = set()
# for fn in w:
#     s.add(extract_speaker_file_name(fn))
# print(sorted(list(s)))
# s1 = set()
# for fn in f:
#     s1.add(extract_speaker_file_name(fn))
# print(s1)





