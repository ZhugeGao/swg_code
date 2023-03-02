"""Given a directory path for Elan files and (optional) selected tier(s), turn .eaf file to a .TextGrid file
and write it to a TextGrid directory.

Author: Zhuge Gao
"""
import glob     # easily loop over files
import pympi   # work with elan files
import os   # move file to another directory
import traceback
import re

if __name__ == '__main__':
    # change things here
    # later change this to relative path
    common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    elans_tgs = {common_path+'twin_elan/':common_path+'twin_tg/', common_path+'trend_elan/':common_path+'trend_tg/',
             common_path+'panel_elan/1982/':common_path+'recovery_1982/', common_path+'panel_elan/2017/':common_path+'recovery_2017/'}
    # elans_tgs = {common_path+'trend_elan/':common_path+'trend_tg/'}
    unprocessed_path = '/Users/gaozhuge/PycharmProjects/swg/personal_info_removal/unprocessed_file/'
    selected_tier = ['SWG']  # put the selected tiers' name here , 'ITW', 'STY', 'TOP', 'INT'
    '''if you want to keep all tiers, leave it as an empty list: tier_selected = []
    the result might not have the same order
    the rest of the program'''
    all_tier_names = []

    # Loop over all .eaf files in the elan_path directory
    for elan_path, textgrid_path in elans_tgs.items():
        for elan_file_path in glob.glob('{}/*.eaf'.format(elan_path)):
            # get the file name string, without the path and the file extension.
            file_name = elan_file_path.split('/')[-1].replace('.eaf', '')
            try:
                # Initialize the elan file
                elan_file = pympi.Elan.Eaf(elan_file_path)
                # turn it into textgrid file
                textgrid_file = elan_file.to_textgrid()
                # if there the tier is not selected remove it
                if selected_tier:  # if there are tier names in the selected_tier list
                    # create re search pattern for all tiers.
                    patterns = []
                    for tier_name in selected_tier:
                        p = re.compile(tier_name)
                        patterns.append(p)
                    for tier in textgrid_file.get_tier_name_num():
                        match = [re.search(p, tier[1]) for p in patterns ]
                        if match[0] == None:# maybe it is better to give the information about which tiers remained
                            print("remove:", tier[1])
                            textgrid_file.remove_tier(tier[1])
                            # remove tier that do not match any selected tier
                # write the textgrid to the textgrid_path directory with the same name as the elan file
                textgrid_file.to_file(textgrid_path + file_name + '.TextGrid')
                print(file_name + '.TextGrid')
            except KeyError:
                print(traceback.extract_stack())
                print(traceback._cause_message)
                print(traceback.print_exc())
                os.rename(elan_file_path, unprocessed_path + file_name + '.eaf')


