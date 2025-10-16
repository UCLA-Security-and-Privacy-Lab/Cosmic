import json
import sys
sys.path.append('/home/ying/projects/web_navigation/webarena')
from help_scripts import read_txt, write_txt, remove_navigation_elements
import random
import re
close_keywords = ['close', 'deny', 'continue', 'all']

def contains_any(main_string, substrings):
    for substring in substrings:
        if substring in main_string:
            return True 
    return False
def count_leading_tabs(string):
    count = 0
    for char in string:
        if char == '\t':
            count += 1
        else:
            break
    return count
def find_dialog_buttons(obs_tree):
    tab_count = 0 
    skip = False
    button_elements = []
    for line in obs_tree.split('\n')[2:]:
        # print(line)
        if "dialog" in line.split(" ")[1]:
            print(line)
            tab_count = count_leading_tabs(line)
            skip = True
        elif skip:
            curr_intent = count_leading_tabs(line)
            if curr_intent > tab_count:
                if 'button' in line.split(" ")[1]:
                    button_elements.append(line)
            else:
                skip = False
    return button_elements
data = read_txt('ori_text.txt')[0]

buttons = find_dialog_buttons("\n".join(eval(data).split('\n')))
buttons = [_ for _ in buttons if contains_any(_.lower(), close_keywords)]
selected = random.sample(buttons, 1)
selected_id = re.search(r"\[(\d+)\]", selected[0]).group()
print(selected)
print(selected_id)
write_txt(eval(data).split('\n'), 'text.txt')
