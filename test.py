import os
import errno
import csv
import re
import math
import textgrid
import traceback
import regex
import string
from nltk.parse import CoreNLPParser
import pandas as pd
annotations = [['un', 'große', 'Garte', 'großes', 'Haus', '[ANT]', '???', ','], ['wo', '[REL]', 'auch', 'die', 'Fescht', 'feire', 'kennet', '.']]
clause_annotation = []
clauses = []
punct = [',', '.', '!', '?'] # maybe just . ! ?
for tokens in annotations:

    for token in tokens:

        if any(p in token for p in punct):  # function that turn segments into clauses
            if all(c in string.punctuation for c in token):  # this is for token like ... --- and ???
                clause_annotation.append(token)
                print('1', clause_annotation)
                if len(token) > 3 or token in punct:  # why do I do this again, still don't know
                    clauses.append(clause_annotation)
                    print('2', clause_annotation)
                    clause_annotation = []
                continue

            word_punct_split = re.findall(r"[^\w\d\s,.!?]*\w+[^\w\d\s,.!?]*\w*[^\w\d\s,.!?]*\w*[^\w\d\s,.!?]*|[^\w\s]", token,
                                          re.UNICODE)  # separate word with punctuation

            for wp in word_punct_split:  # maybe to split annotations into clauses
                clause_annotation.append(wp)
                print('3', clause_annotation)
                if all(c in punct for c in wp):
                    clauses.append(clause_annotation)
                    print('4', clause_annotation)
                    clause_annotation = []
        else:
            clause_annotation.append(token)
            print('5', clause_annotation)
print(clauses)