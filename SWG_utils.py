"""helper methods for the swg project data processing"""
import datetime
import regex


def compile_pattern(word_pattern):  # pattern is lowercase
    pattern = word_pattern.strip()
    pattern = pattern.replace("\ufeff", "")
    pattern = pattern.replace("???", "")
    pattern = pattern.replace(" ","")
    pattern = pattern.replace("xxx","")
    if pattern.startswith("*"):
        pattern = '.*' + pattern[1:]
    else:
        pattern = "^" + pattern
    if pattern.endswith("*"):
        pattern = pattern[:-1] + '.*'
    else:
        pattern = pattern + "$"
    pattern = pattern.replace("[", "\[")  # escape this special symbol for matching
    pattern = pattern.replace("]", "\]")
    pattern = pattern.replace("ge", "ge?") # saf5 # maybe generate doch dieser neue line/pattern for the [ge] words
    # compile variant into pattern
    compiled_pattern = regex.compile(pattern)
    # what about re?
    return compiled_pattern


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
        if begin_label in output[2] and start_index == -1:
            start_index = i
        if end_label in output[2] and end_index == -1:
            end_index = i
    if start_index != -1 and end_index != -1:
        print([output[2] for output in outputs[start_index: end_index+1]])
        print(len([output[2] for output in outputs[start_index: end_index+1]]))
        outputs = outputs[0:start_index] + outputs[end_index+1:]
        skip_by_tags(outputs, type)
    if start_index == -1 and end_index != -1:
        print(begin_label, "not found!")
    if end_index == -1 and start_index != -1:
        print(end_label, "not found!")

    return outputs


def skip_word_list(outputs, word_list_start, word_list_end, type):
    start_index = -1
    end_index = -1
    for i, output in enumerate(outputs):
        if output[2] in word_list_start:  # or output[4] in word_list_end
            s_idx = word_list_start.index(output[2])
            output_list_start = [output[2] for output in outputs[i-s_idx:i-s_idx+10]]
            #print(output_list_start)
            match_boolean_start = []
            if type == 'wl':
                match_boolean_start = [True for x in output_list_start if x in word_list_start]  # order does not matter
            elif type =='ft':
                match_boolean_start = [True for i, x in enumerate(output_list_start) if x in word_list_start[i-1:i+2]]
                # the order matters and when filler words are missing, it need to be matched between a small range.
            if sum(match_boolean_start) > 5 and start_index == -1:
                #print(match_boolean_start)
                #print(sum(match_boolean_start))
                start_index = i-s_idx
        if output[2] in word_list_end:  # or output[4] in word_list_end
            e_idx = word_list_end.index(output[2])
            output_list_end = [output[2] for output in outputs[i-e_idx:i-e_idx+10]]
            #print(output_list_end)
            match_boolean_end =[]
            if type == 'wl':
                match_boolean_end = [True for x in output_list_end if x in word_list_end]
            elif type == 'ft':
                match_boolean_end = [True for i, x in enumerate(output_list_end) if x in word_list_end[i-1:i+2]] # range matchint
                # maybe also combine the files for one speaker in one output and then process it for Bertha
                # Alfried
            if sum(match_boolean_end) > 5:
                #print(match_boolean_end)
                #print(sum(match_boolean_end))
                end_index = i-e_idx+9
    print([output[2] for output in outputs[start_index: end_index+1]])
    print(len([output[2] for output in outputs[start_index: end_index+1]]))
    print(len(outputs))
    if start_index != -1 and end_index != -1:
        outputs = outputs[0:start_index] + outputs[end_index+1:]
    print(len(outputs))
    return outputs


def timestamp_convert(ts):
    ts_list = str(ts).split('.')
    remaining_seconds = int(ts_list[0])
    ms = int(ts_list[1])
    hour = 0
    minute = 0
    if remaining_seconds >= 3600:
        hour = remaining_seconds // 3600
        remaining_seconds = remaining_seconds - (hour * 3600)
    if remaining_seconds >= 60:
        minute = remaining_seconds // 60
        remaining_seconds = remaining_seconds - (minute * 60)
    second = remaining_seconds
    # could try gmtime or other python time function
    timestamp = datetime.time(hour, minute, second, ms).strftime('%H:%M:%S.%f')
    return timestamp