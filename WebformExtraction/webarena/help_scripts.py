import json
import random
import re
from collections import defaultdict
import os
import pickle
import pandas as pd
close_keywords = ['close', 'deny', 'continu', 'all', 'decline', 'reject']

def read_csv(datapath):
    df = pd.read_csv(datapath)
    return df

def read_txt(filepath)->list:
    data = []
    with open(filepath, "r") as f:
        for line in f.readlines():
            data.append(line.strip('\n'))
    return data

def is_subdirectory(child, parent):
    # 
    parent = os.path.abspath(parent)

    child = os.path.abspath(os.path.join(parent, child))
    
    return os.path.commonpath([parent]) == os.path.commonpath([parent, child])
def write_txt(data, savepath)->None:
    with open(savepath, "w") as f:
        if isinstance(data, list):
            for _ in data:
                f.write(_)
                f.write("\n")
        else:
            f.write(data)

def append_txt(data, savepath)->None:
    with open(savepath, "a") as f:
        if isinstance(data, list):
            for _ in data:
                f.write(_)
                f.write("\n")
        else:
            f.write(data)
def pickle_load(path):
    with open(path, 'rb') as file:
        loaded_trajectory = pickle.load(file)
    return loaded_trajectory
def read_json(filepath)->json:
    return json.load(open(filepath, "r", encoding='utf-8'))
def is_file_in_folder(filename, folder_path):
    """Check if a file with a given name exists in a folder or its subfolders."""
    # Walk through the directory tree
    for root, dirs, files in os.walk(folder_path):
        if filename in files:
            return True
    return False
def write2json(data,filepath)->None:
    with open(filepath, "w") as f:
        json.dump(data, f)

def count_leading_tabs(string):
    count = 0
    for char in string:
        if char == '\t':
            count += 1
        else:
            break
    return count

def remove_navigation_elements(tree):
    lines = tree.split('\n')
    result = []
    skip = False
    navigation_intent = 0
    for line in lines:
        if 'navigation' in line:
            # Start skipping lines when a navigation element is found
            skip = True
            navigation_intent = count_leading_tabs(line)
            # navigation_indent_level = indent_level
        elif skip:
            # Stop skipping if the indent level is less than or equal to the navigation element
            curr_intent = count_leading_tabs(line)
            if navigation_intent >= curr_intent:
                skip = False
            # if indent_level <= navigation_indent_level:
            #     skip = False

        if not skip:
            result.append(line)
        result = [_ for _ in result if 'menuitem' not in _]
    return '\n'.join(result)

def process_accessibility_tree(tree):
    start = "\n".join(tree.split('\n')[:2])+"\n"
    tree_str = "\n".join(tree.split('\n')[2:])
    tmp_dict = {}
    # tmp_dict['ori_text'] = tree_str
    tmp_dict['text'] = start + remove_navigation_elements(tree_str)
    
    return tmp_dict['text']
    # write2json(tmp_dict, 'test.json')

def process_accessibility_tree2(tree):
    # tree_str = "\n".join()
    ret_list = []
    tree =  tree.split('\n')[2:]
    for each in tree:
        each = re.sub(r'\[\d+\]', '', each)
        ret_list.append(each)
    return ret_list

def contains_any(main_string, substrings):
    for substring in substrings:
        if substring in main_string:
            return True 
    return False


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

def get_close_id(obs_tree):
    buttons = find_dialog_buttons(obs_tree)
    # buttons = [_ for _ in buttons if contains_any(_.lower(), 'close')]
    buttons = [_ for _ in buttons if contains_any(_.lower(), close_keywords)]
    # if len(buttons) == 0:
    #     buttons = [_ for _ in buttons if contains_any(_.lower(), close_keywords)]
    if len(buttons) >0:
        selected = random.sample(buttons, 1)
        print(selected)
        selected_id = re.search(r"\[(\d+)\]", selected[0]).group()
        return selected_id
    else:
        return ""
    

def extract_accessibility_label(accessibility_output):
    clean_atree = []
    for line in accessibility_output:
        if re.match(r'^\t\t', line) is not None:
            continue
        cleaned_text = re.sub(r'\[.*?\]', '', line)
        cleaned_text = re.sub(r"'[^']*'", "", cleaned_text)
        cleaned_text = re.sub(r'"[^"]*"', "", cleaned_text)
        clean_atree.append(cleaned_text)
    return clean_atree

def select_unique_trees(strings):
    # Step 2: Store the links and strings in a dictionary
    # tree_to_links_strings = defaultdict(list)
    tree_strings = []
    for  s in strings:
        tree = "\n".join(extract_accessibility_label(s))
        tree_strings.append(tree)
    
    # Step 3: Randomly select one link and string for each unique tree
    # unique_tree_links_strings = {tree: random.choice(links_strings) for tree, links_strings in tree_to_links_strings.items()}
    
    return tree_strings

def is_stateinfo(element: dict) -> bool:
    """"""
    return 'observation' in element and 'info' in element

def extract_textboxes(accessibility_output):
    textbox_strings = []
    for line in accessibility_output:
        line = line.strip('\t')
        if 'textbox' in line and 'search' in line.lower():
            continue
        elif 'textbox' in line or 'iframe' in line:
            textbox_strings.append(line.strip())
    return textbox_strings

def url_process(url):
    url = url.split("?")[0]
    return url


def get_visited_links(result_folder):
    return_urls = []
    all_folders = os.listdir(result_folder)
    for folder in all_folders:
        files = [_ for _ in os.listdir(os.path.join(result_folder,folder)) if _.endswith('.pkl') and 'overall' not in _]
        for file in files:
            try:
                with open(os.path.join(result_folder,folder, file), 'rb') as f:
                    loaded_trajectory = pickle.load(f)  
            except:
                continue
            # for _ in loaded_trajectory:
            #     print(_.keys())
            urls = [url_process(_['info']['page'].url) for _ in loaded_trajectory[0::2]]
            return_urls.extend(urls)
    with open("visited_link.txt", "w") as f:
        for url in list(set(return_urls)):
            f.write(url)
            f.write('\n')
    return return_urls

def get_visited_links_this_folder(current_folder):
    return_urls = []
    files = [_ for _ in os.listdir(os.path.join(current_folder)) if _.endswith('.pkl') and 'overall' not in _]
    for file in files:
        try:
            with open(os.path.join(current_folder, file), 'rb') as f:
                    loaded_trajectory = pickle.load(f)  
        except:
            continue
        urls = [url_process(_['info']['page'].url) for _ in loaded_trajectory[0::2]]
        return_urls.extend(urls)
    return return_urls
