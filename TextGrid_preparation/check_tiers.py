import glob     # easily loop over files
import pympi   # work with elan files
import os   # move file to another directory
import traceback
import re
# TODO: move the call of this function to the main script
if __name__ == '__main__':
    # this script is used to check if there is a tier named "SWG" in the TextGrids
    # use a series of paths, just the name
    common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    # textgrids = [common_path+'twin_tg/', common_path+'trend_tg/', common_path+'recovery_1982/', common_path+'recovery_2017/'] #
    textgrids = [common_path+'trend/TextGrid/', common_path+'panel/TextGrid/1982/', common_path+'panel/TextGrid/2017/'] # this is a list of paths containing TextGrids
    unprocessed_path = '/Users/gaozhuge/PycharmProjects/swg/unprocessed_file/' # path to unprocessed files
    for textgrid_path in textgrids: # loop over all the TextGrids directories in the list
        for tg_file_path in glob.glob('{}/*.TextGrid'.format(textgrid_path)):
            file_name = tg_file_path.split('/')[-1]
            print(file_name)
            try:
                # Initialize tg file
                tg_file = pympi.Praat.TextGrid(tg_file_path)
                p = True
                for tier in tg_file.get_tier_name_num():  # change it to textgrid library.
                    if tier[1] == "SWG":  # if there is a tier name "SWG"
                        p = False  # don't print the file
                        break
                if p:
                    print(file_name)
                    for t in tg_file.get_tier_name_num():
                        print("tier name:", t[1])
                        if "SWG-" in t[1] or t[1] == "SWG1" or t[1] in file_name: # the last one is for the TextGrids that use speaker name as tier name
                            # auto check names
                            tg_file.change_tier_name(t[1], "SWG")  # rename the tier to SWG
                            tg_file.to_file(tg_file_path, codec='utf-8', mode='normal')  # save the file
            except KeyError:
                print(traceback.extract_stack())
                print(traceback._cause_message)
                print(traceback.print_exc())
                os.rename(tg_file_path, unprocessed_path + file_name)