import os
import re
from collections import OrderedDict

remove_weight_syntax = True

remove_slashes = True

dedupe_tags = True

remove_tis_and_loras = True

def prune_tags(directory, tag_list):
    # load list of strings to be removed
    with open(tag_list, 'r') as f:
        tags = [line.rstrip() for line in f]

    # create set of escaped tags
    escaped_tags = {re.escape(tag) for tag in tags}

    # recursive traversal
    for root, dirs, files in os.walk(directory):
        # loop through all the files in dir
        for filename in files:
            # check if the file is .txt
            if filename.endswith('.txt'):
                # read .txt contents
                with open(os.path.join(root, filename), 'r', encoding='utf8') as f:
                    content = f.read()
                if tag_list:
                    try:
                        pattern = r'\b(' + '|'.join(escaped_tags) + r')\b'  # word boundaries
                        content = re.sub(pattern, '', content)  # list-based removal
                        if not remove_weight_syntax:
                            content = re.sub(r"\s+(?=:\d.\d+)|\s+(?=[)\]])", "", content)  # move back weighting
                            # after blacklist
                            content = re.sub(r"\(\s+(?=[\w\"'\\])", r"(", content)  # move back weighting after blacklist
                            content = re.sub(r"\[\s+(?=[\w\"'\\])", r"[", content)  # move back weighting after blacklist
                            content = re.sub(r"(?<![\w!?\"'.;])(:\d.\d+)|(?<![\w!?\"'.;\]])([)\]]\d.\d+)|"
                                             r"(?<![\D!?\"'.;])([)\]]+[+-]+)|(?<=,)(\s+[+-]+)|"
                                             r"(?<=,)([+-]+)", "", content)  # floating numeric/+- weighting
                            content = re.sub(r"[([]+(?![\w\"'])", "", content)  # floating first bracket/parens
                            content = re.sub(r"[\[(]+(?!\w+)[)\]]+", "", content)  # floating bracket/parens

                    except OSError as t:
                        print(".txt blacklist not found, or something else got messed up. idk man idk what I'm doing here. "
                              "here's your error:")
                        print(t)

                content = re.sub("\n+", r", ", content)  # remove newlines they mess things up

                if remove_tis_and_loras:
                    content = re.sub(r"<.+>", "", content)
                    content = re.sub(r"withLora.+,\d.\d+\)", "", content)

                if remove_weight_syntax:
                    content = re.sub(r"[)\]]\d.\d+", "", content)  # InvokeAI numeric weight syntax
                    content = re.sub(r":\d.\d+[)\]]", "", content)  # Automatic1111-style numeric weight syntax
                    content = re.sub(r"[+)(\[\]]+", "", content)  # plusses, brackets, parens
                    content = re.sub(r"(?<=\w)(-+)(?!\w)|(?<!\S)(-+)(?!\s\w)", "", content)  # remove hyphens not
                    # between characters

                if remove_slashes:
                    content = re.sub(r"\\+", "", content)  # slashes

                content = re.sub(r"\s+(?=[.,!?;:])", "", content)  # delete whitespace before punctuation
                content = re.sub(r"\s+(?=['\"*](?!\w))", "", content)  # delete whitespace before apostrophes and
                # quotation mark and *
                content = re.sub(r"([,;?!])(?![\\,!?.\s\"*':;)\]])|"
                                 r"(?<![A-Z\d])(\.)(?![\d\s\\,!?.\"*':;)\]])(?![a-z].)|(?<=[A-Z])(\.)(?=[a-z])|"
                                 r"(?<=[a-z])(\.)(?=[A-Z])|(:)(?!\d\.\d)(?![\s\"'])(?!\d\d)|"
                                 r"(?<=[\"'])([.,;!?:])(?=[\"'])|"
                                 r"([.,;!?:\w])(?=\"\w)", r"\g<0> ", content)  # punctuation
                # spacing and whitespace fix
                content = re.sub(r"\s+-+(?=\w)|(?<=[.,;!?:])(-+)(?=\w)", " ", content)  # sometimes - behind text
                # when text deleted

                if not remove_slashes:
                    content = re.sub(r"\\+(?!\")", "", content)  # random slashes not behind quotations

                content = re.sub(r",+(,)", r"\1", content)  # extra commas
                
                if dedupe_tags:
                    words = content.strip().split(', ')
                    unique_words = list(OrderedDict.fromkeys(words))
                    content = ", ".join(unique_words)

                content = re.sub(r"^\s*,|,\s*$", "", content)  # trailing/leading whitespace and commas
                content = re.sub(r"\s+", " ", content)  # cut multiple spaces to one

                # overwrite the original file with the cleaned version
                with open(os.path.join(root, filename), 'w') as f:
                    f.write(content)

# use
prune_tags(r"F:\garb\Garb Bin New", r"F:\removenightmaretags.txt")
