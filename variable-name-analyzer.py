# pip install -U spacy
# python -m spacy download en_core_web_sm
# python3 variable-name-analyzer.py

import spacy
import os
import keyword
from string import ascii_letters, digits
import re
import statistics
import csv

# FUNCTIONS #################################################
# Checks if word exists in English dictionary
def is_english_word(word: str):
    return word.lower() in words

# Return true if first string element is not a keyword 
# AND only contains alphanumeric characters OR underscores
# AND if the second string element is "="
# signifying an assignment, otherwise it is false
def check_valid_assignment_py(line: list[str]) -> bool:
    # Anything less than 2 strings cannot be an assignment
    if len(line) < 2:
        return False
    if not keyword.iskeyword(line[0]) and (not set(line[0]).difference(ascii_letters, digits) or "_" in line[0]) and line[1] == "=":
        return True
    return False

# Return true if the first string element is "def"
# indicating a function is being defined
def check_valid_function_py(line: list[str]) -> bool:
    # Anything less than 2 strings cannot be an assignment
    if len(line) < 2:
        return False
    if line[0] == "def":
        return True
    return False

# Return true if first string element starts with "#"
# indicating a comment is started
def check_valid_comment_py(line: list[str]) -> bool:
    if len(line) < 1:
        return False
    if line[0][0] == '#':
        return True
    return False

# Get all variable names from Python file into list
def accumulate_variables(file_lines: list[str]) -> list[str]:
    variable_names = []
    for line in file_lines:
        line_split = line.split()
        # If line is variable assignment AND variable name is not already in list
        if check_valid_assignment_py(line_split) and line_split[0] not in variable_names:
            variable_names.append(line_split[0])
    return variable_names

# Get all function names from Python file into list
def accumulate_functions(file_lines: list[str]) -> list[str]:
    function_names = []
    for line in file_lines:
        line_split = line.split()
        if check_valid_function_py(line_split):
            function_names.append(line_split[1].split('(')[0])
    return function_names

# Get all comments from Python file into string
def accumulate_comments(file_lines: list[str]) -> str:
    comment_names = ""
    for line in file_lines:
        line_split = line.split()
        if check_valid_comment_py(line_split):
            comments = [word for word in line_split if "#" not in word]
            comment_names += " ".join(comments)
            comment_names += " "
    return comment_names

# Split each name into "words" through multiple delimiters
# and find proportion of English words over total words
def compute_english_words_proportion(variable_names: list[str]) -> list[list[str]]:
    proportions = []
    for variable_name in variable_names:
        # Split by underscores and numbers, remove empty strings
        split_words = list(filter(None, re.split('_|([0-9]+)', variable_name)))
        # Check if word exists in dictionary
        checked_words = [word for word in split_words if is_english_word(word)]
        proportions.append(len(checked_words) / len(split_words))
    return proportions

# CODE #######################################################
# Grabbed words from https://github.com/dwyl/english-words
with open("words.txt") as word_file:
    words = set(word.strip().lower() for word in word_file)

filesPath = os.getcwd()
filesPath += '/files'

# Load English tokenizer, tagger, parser and NER
nlp = spacy.load("en_core_web_sm")

csv_lines = [["NAME","VAR","FUNC","COMM","UND"]]

# Iterate through all Python files in "/files" directory
for file_name in os.listdir(filesPath):
    variable_names = []
    function_names = []
    comments = []
    # Grab variables from file
    if file_name.endswith(".py"):
        with open(filesPath + '/' + file_name) as file:
            # Grab all lines and remove newline/whitespace
            file_lines = [line.rstrip() for line in file]
            variable_names = accumulate_variables(file_lines)
            function_names = accumulate_functions(file_lines)
            comments = accumulate_comments(file_lines)
            print(comments)
    else:
        continue

    # CSV-line with file name and other proportions
    csv_line = [file_name.split('.')[0]]
    
    # Determine proportion of English words over total words
    variable_proportions = compute_english_words_proportion(variable_names)
    variable_mean = statistics.mean(variable_proportions)
    function_proportions = compute_english_words_proportion(function_names)
    function_mean = statistics.mean(function_proportions)
    csv_line.append("{:.2f}".format(variable_mean))
    csv_line.append("{:.2f}".format(function_mean))
    
    sentence_proportions = []
    doc = nlp(comments)
    # comment_nouns = [chunk.text for chunk in doc.noun_chunks]
    # comment_verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
    sentences = list(doc.sents)
    for sentence in sentences:
        is_sentence = 0
        sent = nlp(sentence.text)
        if len([chunk.text for chunk in sent.noun_chunks]) > 0:
            is_sentence += 0.5
        if len([token.lemma_ for token in sent if token.pos_ == "VERB"]) > 0:
            is_sentence += 0.5
        sentence_proportions.append(is_sentence)
    comment_mean = statistics.mean(sentence_proportions)
    csv_line.append("{:.2f}".format(comment_mean))

    # Compute Understandability Mean by averaging across all other metrics
    understandability_mean = (variable_mean + function_mean + comment_mean) / 3
    csv_line.append("{:.2f}".format(understandability_mean))

    csv_lines.append(csv_line)

with open(os.getcwd() + '/results.csv', 'w', encoding='UTF8') as f:
    writer = csv.writer(f)
    for csv_line in csv_lines:
        writer.writerow(csv_line)
