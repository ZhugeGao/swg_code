"""
Author: Nianheng Wu
xjtuwunianheng@gmail.com, Eberhard Karls Universität Tübingen
"""
import os
import textgrid
from pydub import AudioSegment
import shutil
import traceback

# annotation = '<[A-ZÄÖÜß]*>|^$'


def read_file_names(path):
    file_list = filter(lambda x: x.endswith('.TextGrid'), os.listdir(path))
    # need to resort this because to skip the words it needs tobe
    return file_list


def read_text_grid(name):
    tg=textgrid.TextGrid()
    tg.read(name)

    for each_tier in tg.tiers:
        if each_tier.name.find('SWG') != -1:
            phrase_list = get_text(each_tier) # get the annotations in this tier.
            return phrase_list


def get_text(tier):
    phrase_list =[]
    intervals = tier.intervals

    for each_sentence in intervals:

        if each_sentence.mark != '':
            new_phrase = phrase(each_sentence.minTime, each_sentence.maxTime, each_sentence.mark)
            phrase_list.append(new_phrase)

        elif each_sentence.mark == '':
            new_phrase = phrase(each_sentence.minTime, each_sentence.maxTime, '<P>')
            phrase_list.append(new_phrase)

    phrase_list = reorganize_phrase_list(phrase_list)

    return phrase_list


def reorganize_phrase_list(phrase_list):
    organized_phrase_list = []
    count = 1
    organized_phrase_list.append(phrase_list[0])

    for each_phrase in phrase_list:

        if each_phrase.phrase == '<P>':
            if organized_phrase_list[count-1].phrase == '<P>':
                last_empty_phrase = organized_phrase_list[count-1]
                last_empty_phrase.update_end_time(each_phrase.end_time)
                organized_phrase_list[count-1] = last_empty_phrase
            else:
                organized_phrase_list.append(each_phrase)
                count += 1
        else:
            organized_phrase_list.append(each_phrase)
            count += 1

    return organized_phrase_list


class phrase:
    def __init__(self, start_time, end_time, phrase):
        self.start_time = start_time
        self.end_time = end_time
        self.phrase = phrase

    def update_start_time(self, new_start_time):
        self.start_time = new_start_time

    def update_end_time(self, new_end_time):
        self.end_time = new_end_time

    def update_phrase(self, new_phrase):
        self.phrase = new_phrase


def strip_txt_and_wav(phrase_list, wav_path, empty_path, none_empty_path, filename):
    filename = filename[:-9]
    suffix = 0
    this_whole_wav = AudioSegment.from_wav(wav_path + filename + ".wav")

    for each_phrase in phrase_list:
        phrase_string = each_phrase.phrase # what does it mean by phrase?
        if phrase_string != '<P>':
            with open(none_empty_path+filename+"_"+str(suffix)+".txt", 'w', encoding= 'utf8') as file:
                file.write(phrase_string)
            this_wav = this_whole_wav[int(each_phrase.start_time* 1000) : int(each_phrase.end_time *1000)]
            this_wav.export(none_empty_path+filename+"_"+str(suffix)+".wav", format="wav")
            suffix += 1
            # isn't this the same if the else block is removed?
        else:
            with open(empty_path+filename+"_"+str(suffix)+".txt", 'w', encoding= 'utf8') as file:
                file.write(phrase_string)
            this_wav = this_whole_wav[int(each_phrase.start_time * 1000) : int(each_phrase.end_time * 1000)]
            this_wav.export(empty_path + filename + "_" + str(suffix) + ".wav", format="wav")
            suffix += 1 # skip word lists here. maintain the time information for wav...
# skip the words here

if __name__ == '__main__':
    #textgrid_path = "/home/nianheng/Documents/hiwi/12December/Nianheng_Fabian/TextGrids_problem/"
    #audio_path = "/home/nianheng/Documents/hiwi/12December/Nianheng_Fabian/Wav_processed_no_names/"
    #path = '/home/nianheng/Documents/hiwi/01januar/karen/test/'
    path = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/test/" # wav and tg together
    problem = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/unprocessed/'
    empty_path = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/empty/"
    none_empty_path = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/none_empty/"

    textgrid_file_name = read_file_names(path)

    for each_file_name in textgrid_file_name:
        try:
            phrase_list = read_text_grid(path+each_file_name)
            strip_txt_and_wav(phrase_list, path, empty_path, none_empty_path, each_file_name)
        except Exception as e:
            print(each_file_name)
            shutil.copy(path + each_file_name, problem + each_file_name)
            shutil.copy(path + each_file_name[:-9]+'.wav', problem + each_file_name[:-9]+'.wav')
            traceback.print_tb(e.__traceback__)



