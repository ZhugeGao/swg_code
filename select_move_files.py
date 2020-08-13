import glob
import os
import pandas as pd


def get_file_paths(root_directory, filetype=''): # could also use glob
    files_paths = {}  # why is this a dictionary?
    for root, dirs, files in os.walk(root_directory):
        if dirs:
            continue
        if files:
            current_path = root
            for file in files:
                if file not in files_paths.keys() and file.endswith(filetype):
                    files_paths[file] = current_path+'/'
    return files_paths


def read_speakers(speaker_files):
    speaker_lists = {}
    for speaker in speaker_files:
        speaker_type = speaker.split('_')[1]
        df_spker = pd.read_csv(speaker)
        speaker_list = [x for x in list(df_spker['trans_id']) if str(x) != 'nan']  # nan in the list
        for spk in speaker_list:
            speaker_lists[spk] = speaker_type
    return speaker_lists


def match_file_speaker(speaker_lists, files_paths, working_directory):  # change the function name
    unprocessed_path = working_directory+'zips'+'/'
    for file in files_paths.keys():
        file_path = working_directory + files_paths[file] + file
        trans_id = file.replace(file_type, '')
        if len(trans_id.split('-')) > 5:
            trans_id = '-'.join(trans_id.split('-')[:5])
            file = trans_id + file_type
        if trans_id in speaker_lists.keys():
            speaker_type = speaker_lists[trans_id]
            speaker_path = working_directory + speaker_type + type_target[file_type]
            os.rename(file_path, speaker_path + file)
        else:
            os.rename(file_path, unprocessed_path + file)


def rename_file_with_type(old_file_type, new_file_type, root_directory):
    for filename in glob.iglob(os.path.join(root_directory, '*'+old_file_type)):
        print("Renamed file:", filename)
        os.rename(filename, filename[:-4] + new_file_type)


def match_file_pair(filetype1, filetype2, directory):
    ft1 = [fn.replace(filetype1, '') for fn in glob.iglob(os.path.join(directory, '*'+filetype1))]
    ft2 = [fn.replace(filetype2, '') for fn in glob.iglob(os.path.join(directory, '*' + filetype2))]
    print("Missing", filetype1 + ":", sorted(list(set(ft2) - set(ft1))))
    print("Missing", filetype2 + ":", set(ft1) - set(ft2))


working_directory = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/"
speaker_files = ["SWG_panel_speakers_24apr2020.csv", "SWG_trend_speakers_24apr2020.csv", "SWG_twin_speakers_24apr2020.csv"]
file_type = '.wav'
type_target = {'.eaf': '_elan/', '.TextGrid': '_tg/', '.wav': '_wav/', '.WAV': '_wav/'}  # problem with the panel
os.chdir(working_directory)
rename_file_with_type('.WAV', '.wav', 'zips')
files_paths = get_file_paths('zips', filetype=file_type)
# print(files_paths)
speaker_lists = read_speakers(speaker_files)
match_file_speaker(speaker_lists, files_paths, working_directory)

# check pairs: .wav, .TextGird
rename_file_with_type('.WAV', '.wav', 'twin_wav')
match_file_pair('.wav', '.TextGrid', 'twin')

