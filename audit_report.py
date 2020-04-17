"""
Author: Nianheng Wu
xjtuwunianheng@gmail.com, Eberhard Karls Universität Tübingen
"""
# recover, segment remove it.q
import collections
import os
import errno
import csv
import re
import spacy
import textgrid
import traceback
import regex
import string
from nltk.parse import CoreNLPParser


class Transform:

    def __init__(self, rootpath, outputpath, the_maps):
        self.rootpath = rootpath
        self.outputpath = outputpath
        self.maps = the_maps
        self.no_ddm = set()


    def start(self):
        try:
            os.chdir(self.rootpath)  # change current working directory
        except FileNotFoundError:
            print(errno.EPERM)
        if not os.path.exists(
                self.outputpath):  # if the csv does not exist, create the csv
            self.create_a_csv()
        self.get_file_list()  # get the list of textgrids,

    def get_file_list(self):
        file_list = [
            file for file in os.listdir(
                self.rootpath) if file.endswith('.TextGrid')]
        self.read_from_textgrid(file_list)

    def read_from_textgrid(self, file_list):
        double_dash = re.compile(r'^-[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî?]+-[,.!?]*$')
        dash_l = re.compile(r'^-[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî]+-?[,.!?]*$')
        dash_r = re.compile(r'^-?[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî]+-[,.!?]*$')
        person_name_l = re.compile(r'{[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî\-?]*}?')
        person_name_r = re.compile(r'{?[a-zA-ZäöüÄÖÜßÔûôÊĩÂâõẽãÃêàéëî\-?]*}')
        hyphen_2 = re.compile(r'-{2,}')
        hyphen = re.compile(r'^-$')
        dot_2 = re.compile(r'\.{2,3}')
        quo_2 = re.compile(r'^\d?"{2,}$')
        question_2 = re.compile(r'\?{2,}')
         # lemma
        nlp = spacy.load('de_core_news_md')
        for each_file_name in file_list:
            # now combine the files of the same speakers
            outputs = []
            outputs_cnt = collections.Counter()
            print(each_file_name)
            interval_num = 0
            file_path = self.rootpath + each_file_name
            try:
                file_textgrid_obj = textgrid.TextGrid.fromFile(file_path)
            except UnicodeDecodeError:
                print(
                    each_file_name +
                    ': the encode is weird, not utf-8 or ansi')

            tier_list = file_textgrid_obj.tiers

            for each_tier in tier_list:
                if each_tier.name == 'SWG':  # read from swg tier
                    tier_swg = each_tier
                    intervals_swg = tier_swg.intervals

            try:
                for each_annotation in intervals_swg:
                    annotation_mark = each_annotation.mark
                    if not annotation_mark.strip(): continue
                    punct = [',', '.', '!', '?'] # maybe just . ! ?

                    for word_raw in annotation_mark.split():
                        word_raw = word_raw.replace(":","")
                        word_raw = word_raw.replace('"', '')
                        word_raw = word_raw.replace('…', '')
                        if re.search(person_name_l, word_raw):
                            continue
                        elif re.search(person_name_r, word_raw):  # maybe i should use 'or'
                            continue
                        elif re.search(hyphen, word_raw):
                            continue
                        elif re.search(hyphen_2, word_raw):
                            continue
                        elif re.search(double_dash, word_raw):
                            continue
                        elif re.search(dash_l, word_raw):
                            continue
                        elif re.search(dash_r, word_raw):
                            continue
                        elif re.search(dot_2, word_raw):
                            continue
                        elif re.search(question_2, word_raw):
                            continue
                        elif re.search(quo_2, word_raw):
                            continue
                        word_l = []
                        tmp = []
                        tmp.append(word_raw)
                        while tmp:
                            word = tmp.pop(0)
                            if any(char in punct for char in word):
                                for p in punct:
                                    if p in word:
                                        for w in word.split(p):
                                            if w is not '':
                                                tmp.append(w)
                            else:
                                word_l.append(word)
                        for word_p in word_l:
                            if re.search(person_name_l, word_p):
                                continue
                            elif re.search(person_name_r, word_p):  # maybe i should use 'or'
                                continue
                            elif re.search(hyphen, word_p):
                                continue
                            elif re.search(hyphen_2, word_p):
                                continue
                            elif re.search(double_dash, word_p):
                                continue
                            elif re.search(dash_l, word_p):
                                continue
                            elif re.search(dash_r, word_p):
                                continue
                            elif re.search(dot_2, word_p):
                                continue
                            elif re.search(question_2, word_p):
                                continue
                            elif re.search(quo_2, word_p):
                                continue
                            elif word_p:
                                # pos tagger got rid of the [], and anything after it
                                if word_p in self.no_ddm:
                                    DDM = ""
                                    std = word_p
                                    std = std.replace("[", "")
                                    std = std.replace("]", "")
                                else:
                                    DDM, std = self.match_ddm(word_p)
                                    DDM = " ".join(DDM)
                                    std = " ".join(std)
                                    DDM_std, word_std = self.match_std(word_p)
                                    DDM_std = " ".join(DDM_std)
                                    word_std = " ".join(word_std)
                                    if DDM == "" and DDM_std == "":
                                        self.no_ddm.add(word_p)
                                        std = word_p
                                        std = std.replace("[", "")
                                        std = std.replace("]", "")
                                    else:
                                        DDM = " ".join([DDM, DDM_std]).strip()
                                        std = " ".join([std, word_std]).strip()
                                if DDM:
                                    tokens = nlp.tokenizer(std)
                                    lemmas = []
                                    for t in tokens:
                                        lemmas.append(t.lemma_)
                                    lemma = " ".join(lemmas)
                                    outputs.append((each_file_name[each_file_name.rfind("_") + 1:-9], each_file_name, word_p, DDM, lemma))
            except AttributeError as e:
                print(
                    each_file_name +
                    ': tier words is empty or does not exist ')
                traceback.print_tb(e.__traceback__)

            outputs = skip_by_tags(outputs,'r')
            outputs = skip_by_tags(outputs, 'wl')
            outputs = skip_by_tags(outputs, 'wg')
            word_list1_start = ["Finger", "Flüge", "Biene", "Hunger", "immer", "Äpfel", "Apfel", "Asche", "zum", "waschen"]
            word_list1_end = ["laufen", "Frage", "Linde", "meist", "Haar", "Huhn", "Türe", "Kinder", "alle", "Gast"]
            word_list2_start = ["Flüge", "Fliege","Söhne", "Sehne", "können", "kennen", "Türe", "Tiere", "vermissen","vermessen"]
            word_list2_end = ["heiter", "heute", "Feuer", "feiern", "Ofen", "oben", "Kreide", "Kreuze", "Magen", "sagen"]
            ft_1_start = ["Vor", "Zeiten", "war", "ein", "König", "und", "eine", "Königin", "die", "sprachen"]
            ft_1_end = ["alte", "Frau", "mit", "einer", "Spindel", "und", "spann", "emsig", "ihren", "Flachs"]
            ft_2_start = ["Es", "war", "einmal", "eine", "alte", "Geiß", "die", "hatte", "sieben", "junge"]
            ft_2_end = ["er", "in", "seinen", "Rachen", "nur", "das", "jüngste", "fand", "er", "nicht"]
            ft_3_start = ["In", "den", "alten", "Zeiten", "wo", "das", "Wünschen", "noch", "geholfen", "hat"]
            ft_3_end = ["bei", "seinesgleichen", "und", "quakt", "und", "kann", "keines", "Menschen", "Geselle", "sein"]
            outputs = skip_word_list(outputs, word_list1_start, word_list1_end, 'wl')
            outputs = skip_word_list(outputs, word_list2_start, word_list2_end, 'wl')
            outputs = skip_word_list(outputs, ft_1_start, ft_1_end, 'ft')
            outputs = skip_word_list(outputs, ft_2_start, ft_2_end, 'ft')
            outputs = skip_word_list(outputs, ft_3_start, ft_3_end, 'ft')
            outputs_cnt.update(outputs)
            ddm_dict  = collections.OrderedDict()
            for entry, count in outputs_cnt.most_common():
                for ddm in entry[3].split():
                    if ddm not in ddm_dict.keys():
                        ddm_dict[ddm] = []
                    ddm_dict[ddm].append([entry[0], entry[1], ddm, entry[2], entry[4], count])

            for entries in ddm_dict.values():
                for entry in entries:
                    print(entry)
                    self.output_as_csv(*entry)

    def match_std(self, word):
        word = word.strip()
        # check for capital letter at the start
        capital = word[0].isupper()
        word = word.lower()
        DDM2 = []
        german_list = []
        for key in std_map.keys():
            if key.match(word) is not None:
                for each_value in std_map[key]:
                    ddm_tag = each_value + 's'
                    if ddm_tag not in DDM2:
                        DDM2.append(ddm_tag)
                    if capital:
                        w = word.title()
                    else:
                        w = word
                        # change first letter into capital letter
                    w = w.replace("[", "")
                    w = w.replace("]", "")
                    if w not in german_list:
                        german_list.append(w)
        return DDM2, german_list

    def match_ddm(self, word):
        word = word.strip()
        capital = word[0].isupper()
        word = word.lower()
        ddm_list = []
        german_list = []
        ptn = []
        for key in maps.keys():
            if key.match(word) is not None:
                for each_value in maps[key]:
                    swg = each_value[0]
                    std = each_value[1]
                    swg = swg.replace("^", "")
                    swg = swg.replace("$", "")
                    swg = swg.replace(".*", "")
                    swg = swg.replace("\[", "[")
                    swg = swg.replace("\]", "]")

                    std = std.replace("^", "")
                    std = std.replace("$", "")
                    std = std.replace(".*", "")
                    std = std.replace("?","")

                    ddm_tag = each_value[2] + 'd'
                    if ddm_tag not in ddm_list:
                        ddm_list.append(ddm_tag)
                    german = word.replace(swg, std)
                    german = german.replace("^", "")
                    german = german.replace("$", "")
                    german = german.replace("[", "")
                    german = german.replace("]", "")
                    if capital:
                        german = german.title()
                    # change the first letter
                    if german not in german_list:
                        # might be redundant
                        german_list.append(german)

        return ddm_list, german_list

    def output_as_csv(self, fileid, source_filename, DDM, word_form, lemma, cnt_form):
        with open(output_path, mode='a', newline="") as output_file:
            csv_writer = csv.writer(
                output_file,
                delimiter=',',
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow([fileid, source_filename, DDM, word_form, lemma, cnt_form])

    def create_a_csv(self):
        """
        If the csv file you want to output does not exist in your path, this function will create it.
        """
        with open(output_path, 'w', newline="") as create_the_csv:
            csv_writer = csv.writer(
                create_the_csv,
                delimiter=',',
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(
                ['File_ID', 'Filename', 'var_code', 'word_form', 'lemma', 'cnt_form'])# var_code  word_form  lemma   cnt_form
        create_the_csv.close()


def read_ddm_files(path):
    file_list = filter(lambda x: x.endswith('.csv'), os.listdir(path))
    return file_list


def read_ddm_csv(path, filename):
    with open(path + filename, 'r', encoding="utf8") as file:
        reader = csv.reader(file)
        first = next(reader)
        if (len(first) == 2) and (first[1] != ""):
            file.seek(0)
            for row in reader:
                row = make_pattern(row)
                r = row[0].lower()
                r1 = row[1].lower()
                if r != "" and r1!= "":
                    compiled_pattern = regex.compile(r)
                    compiled_pattern2 = regex.compile(r1)

                    if compiled_pattern not in maps.keys():
                        maps[compiled_pattern] = [
                            (r, r1, filename[:-4])]
                    else:
                        maps[compiled_pattern].append(
                            (r, r1.lower(), filename[:-4]))

                    if compiled_pattern2 not in std_map.keys():
                        std_map[compiled_pattern2] = {filename[:-4]}
                    else:
                        std_map[compiled_pattern2].add(filename[:-4])

        elif (len(first) == 1) or (first[1] == ""):
            file.seek(0)
            for row in reader:
                row = make_pattern(row)
                r = row[0].lower()
                if r != "":
                    compiled_pattern = regex.compile(r)
                    if r not in maps.keys():
                        maps[compiled_pattern] = [
                            (r, r, filename[:-4])]
                    else:
                        maps[compiled_pattern].append(
                            (r, r, filename[:-4]))

    return maps


def make_pattern(line_list):  # I think this pattern making might cause some problems
    new_line_list = []
    for each_word in line_list:
        each_word = each_word.strip()
        each_word = each_word.replace("\ufeff", "")
        each_word = each_word.lower()

        if each_word.startswith("*"):
            pattern = '.*' + each_word[1:]
        else:
            pattern = "^" + each_word

        if each_word.endswith("xxx"):
            pattern = pattern[:-3]

        if pattern.endswith("*"):
            pattern = pattern[:-1] + '.*'
        else:
            pattern = pattern + "$"

        pattern = pattern.replace("[", "\[") # escape this special symbol for matching
        pattern = pattern.replace("]", "\]")
        new_line_list.append(pattern)

    return new_line_list


def skip_by_tags(outputs, type):
    start_index = -1
    end_index = -1
    if type == 'r':
        begin_label = "[BEGIN-READING]"
        end_label = "[END-READING]"
    elif type == 'wl':
        begin_label = "[BEGIN-WORD-LISTS]"
        end_label = "[END-WORD-LISTS]"
    elif type == 'wg':
        begin_label = "[BEGIN-WORD-GAMES]"
        end_label = "[END-WORD-GAMES]"
    for i, output in enumerate(outputs):
        if output[2] == begin_label and start_index == -1:
                start_index = i
        if output[2] == end_label and end_index == -1:
                end_index = i
    if start_index != -1 and end_index != -1:
        print([output[2] for output in outputs[start_index: end_index+1]])
        outputs = outputs[0:start_index] + outputs[end_index+1:]
        skip_by_tags(outputs, type)
    if start_index == -1 and end_index != -1:
        print(begin_label, "not found!")
    if end_index == -1 and start_index != -1:
        print(end_label, "not found!")

    return outputs





if __name__ == '__main__':
    root_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/recovery_2017/'
    output_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/SWG_panel_audit_2019092323.csv'
    ddm_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/ddm_csv/'
    done_path = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/done/"
    maps = {}
    std_map = {}
    # ddm csv, which is just one in this case
    ddm_file_list = read_ddm_files(ddm_path)

    for each_file in ddm_file_list:
        read_ddm_csv(ddm_path, each_file)
    transform = Transform(root_path, output_path, maps)
    transform.start()
    # clause extract
    # work on word_German
