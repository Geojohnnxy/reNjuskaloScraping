import itertools
import re


def remove_multiple_newlines(string):
    string = string.split("\n")
    new_string = [el.strip() for el in string if el.strip() != "" or el.strip() != " "]
    new_string = [i for i in new_string if i != ""]
    new_string = "\n".join(new_string)
    if new_string[0] == "\n":
        new_string = new_string[1:]
    return new_string


def stripping(string):
    r_unwanted = re.compile("[\n\t\r]")
    string = r_unwanted.sub("", string)
    return string.strip()


def remove_string_duplication(string):
    if "\n" in string:
        string = string.replace("\n", "<br>")
        string = string.replace("\t", "<pre>")
        string = string.replace("\r", "<br>")

    string_list = string.split()
    words_count = len(string_list)
    for index in range(words_count,0,-1):
        string_list = string.split()
        lists = [string_list[i:i +index] for i in range(0, words_count, index)]
        group_lists = [x[0] for x in itertools.groupby(lists)]
        flat_list = [item for sublist in group_lists for item in sublist]
        string = " ".join(flat_list)
        string_list = string.split()
        # reversed so we can have tuples equal sizes from the begining of the string and from ending and check for string duplication
        lists = [list(reversed(string_list))[i:i +index] for i in range(0, words_count, index)]
        group_lists = [x[0] for x in itertools.groupby(lists)]
        flat_list = [item for sublist in group_lists for item in sublist]
        string = " ".join(list(reversed(flat_list)))

    string = string.replace("<br>", "\n")
    string = string.replace("<pre>", "\t")
    return string


def capitalize_first_letter(string):
    if string.isupper():
        return string

    if string[0].isupper():
        return string
    else:
        string[0] = string[0].replace(string[0], string[0].upper())
    return string


class StringFormatter(object):

    def __init__(self, content, formatting=None):
        if type(content) in [list, tuple] and formatting is None and len(content) > 0:
            self.string = " ".join(content)
            self.string = stripping(self.string)
        elif type(content) in [list, tuple] and formatting == "digit" and len(content) > 0:
            self.string = " ".join(content)
            self.string = stripping(self.string)
            self.string = "".join([i for i in self.string if i.isdigit()])
        elif type(content) in [list, tuple] and formatting == "multi" and len(content) > 0:
            self.string = "\n".join(content)
        elif type(content) == str and formatting is None:
            self.string = content
            self.string = stripping(self.string)
        elif type(content) == str and formatting == "multi":
            self.string = content
        elif type(content) == str and formatting == "digit":
            self.string = content
            self.string = [i for i in self.string if i.isdigit()]
        else:
            self.string = None

    def format(self):
        if not self.string:
            return None

        if "\n" in self.string:
            self.string = remove_multiple_newlines(self.string)

        self.string = remove_string_duplication(self.string)
        if len(self.string.split()) > 5:
            self.string = capitalize_first_letter(self.string)
        else:
            self.string = self.string.title()
        self.string = self.string.strip()
        if "," == self.string[-1]:
            self.string = self.string[:-1]
        return self.string.strip()
