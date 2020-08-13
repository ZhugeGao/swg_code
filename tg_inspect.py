import os
import re
import argparse


def find_special_character(path):
    tg_list = os.listdir(path)
    tg = filter(lambda tg: re.search(r'\.TextGrid', tg), tg_list)
    list_tg = list(tg)
    special = set()
    character_pattern = re.compile(r'[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî]')
    for tg in list_tg:
        try:
            file = open('{}/{}'.format(path, tg), "r")
            for line in file:
                for char in line:
                    if not re.search(character_pattern, char):
                        special.add(char)
            file.close()
        except FileNotFoundError:
            print(tg, "not found!")
            continue
    print(len(special))
    for char in list(special):
        print(char)
    # isalphanum() does not find the special characters


def find_skip_label(path):  # simplify it
    tag_pattern = re.compile("\[[^\[\]]*\]")
    tags = ["[BEGIN-READING]", "[END-READING]", "[BEGIN-WORD-LISTS]", "[END-WORD-LISTS]", "[BEGIN-WORD-GAMES]", "[END-WORD-GAMES]"]
    tag_pairs = [("[BEGIN-READING]", "[END-READING]"), ("[BEGIN-WORD-LISTS]", "[END-WORD-LISTS]"), ("[BEGIN-WORD-GAMES]", "[END-WORD-GAMES]")]
    tg_list = os.listdir(path)
    tg = filter(lambda tg: re.search(r'\.TextGrid', tg), tg_list)
    list_tg = list(tg)
    for tg in list_tg:
        try:
            file = open('{}/{}'.format(path, tg), "r")
            tag_in_file = []
            for line in file:
                if "[BEGIN" in line or "[END" in line:
                    match = re.search(tag_pattern, line)
                    if match:
                        tag = match.group(0)  # get the [] tag
                        tag_in_file.append(tag)
                        if tag not in tags:
                            print("Incorrect tag!")
                            print(tg, ": " + line)
                    else:  # if there is no matching
                        print("Incorrect tag: ']' might be missing!")
                        print(tg, ": " + line)
            # check if the tags are in pair
            if (len(tag_in_file) % 2) != 0:
                print("Missing tag!")
                print(tg)
                print("tags in file: ", tag_in_file)
            # check if it tags are correctly nested
            itr = iter(tag_in_file)
            for t in zip(itr, itr):  # turn list of tags into list of tag pairs (tuples).
                if t not in tag_pairs:
                    print("Incorrect tag pair!")
                    print(tg, ": " + str(t))
                    print("tags in file: ", tag_in_file)
            file.close()

        except FileNotFoundError:
            print(tg, "not found!")
            continue


def find_rel_label(path):
    tg_list = [p for p in os.listdir(path) if p.endswith('.TextGrid')]
    tag_pattern = re.compile("\[[^\[\]\d]*\]")
    for tg in tg_list:
        with open('{}/{}'.format(path, tg), "r") as file:
            tag_in_file = [] # dict tg: tags_list
            for line in file:
                match = re.findall(tag_pattern, line)
                if match:
                    tag_in_file.extend(match)
                elif "REL" in line or "ANT" in line:
                    print(line)
        print(tg)
        # print(tag_in_file)




if __name__ == '__main__':
    # PUT path in a list
    common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    textgrids_path = [common_path + 'twin_tg/', common_path + 'trend_tg/', common_path + 'recovery_1982/',
                 common_path + 'recovery_2017/'] # , common_path+'style_tg/'

    # print which path is being processed
    for path in textgrids_path:
        find_rel_label(path)  # skip rel