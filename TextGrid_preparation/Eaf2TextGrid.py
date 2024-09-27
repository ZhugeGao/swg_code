"""Given a directory path for Elan files and (optional) selected tier(s), turn .eaf file to a .TextGrid file
and write it to a TextGrid directory.

Author: Zhuge Gao
"""
import glob  # easily loop over files
import pympi  # work with elan files
import os  # move file to another directory
import traceback
import re



def manual_eaf_to_TextGrid(elan_path, textgrid_path, selected_tier):
    # Loop over all .eaf files in the elan_path directory
    print("Converting .eaf files to .TextGrid files...")
    # identify the number of names in the elan file name, and extract the speaker names into a list
    # make copies of the elan file for each speaker name
    for elan_file_path in glob.glob('{}/*.eaf'.format(elan_path)):
        # get the file name string, without the path and the file extension.
        file_name = elan_file_path.split('/')[-1].replace('.eaf', '')
        try:
            # Initialize the elan file
            elan_file = pympi.Elan.Eaf(elan_file_path)
            # turn it into textgrid file
            textgrid_file = elan_file.to_textgrid()
            # if the tier is not selected remove it
            if selected_tier:  # if there are tier names in the selected_tier list
                # create re search pattern for all tiers.
                patterns = []
                for tier_name in selected_tier:
                    p = re.compile(tier_name)
                    patterns.append(p)
                for tier in textgrid_file.get_tier_name_num():
                    match = [re.search(p, tier[1]) for p in patterns]
                    if all(m is None for m in match):  # maybe it is better to give the information about which tiers remained
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
            os.rename(elan_file_path, elan_path + 'unprocessed/' + file_name + '.eaf')

def eaf_to_TextGrid(elans_tgs, selected_tier, unprocessed_path):
    # Loop over all .eaf files in the elan_path directory
    print("Converting .eaf files to .TextGrid files...")
    for elan_path, textgrid_path in elans_tgs.items():
        print(elan_path, textgrid_path)
        for elan_file_path in glob.glob('{}/*.eaf'.format(elan_path)):
            # get the file name string, without the path and the file extension.
            file_name = elan_file_path.split('/')[-1].replace('.eaf', '')
            try:
                # Initialize the elan file
                elan_file = pympi.Elan.Eaf(elan_file_path)
                # turn it into textgrid file
                textgrid_file = elan_file.to_textgrid()
                # if the tier is not selected remove it
                if selected_tier:  # if there are tier names in the selected_tier list
                    # create re search pattern for all tiers.
                    patterns = []
                    for tier_name in selected_tier:
                        p = re.compile(tier_name)
                        patterns.append(p)
                    for tier in textgrid_file.get_tier_name_num():
                        match = [re.search(p, tier[1]) for p in patterns]
                        if all(m is None for m in match):  # maybe it is better to give the information about which tiers remained
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