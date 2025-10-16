import pickle
from bs4 import BeautifulSoup
from PIL import Image
import io
import base64
import json
import hashlib
import re
import os
from argparse import ArgumentParser
from tqdm import tqdm 
def parse_args():
    parser = ArgumentParser(description="Extract form properties")
    result_folder = parser.add_argument('--folder', type=str)
def get_image_md5(image_array):
    image = Image.fromarray(image_array)
    image_bytes = image.tobytes()
    hash_md5 = hashlib.md5(image_bytes).hexdigest()
    return hash_md5

def get_json(data_path):
    with open(data_path, "r") as f:
        data = json.load(f)
    return data

def generate_new_dict(dict_list, key):
    new_dict = {}

    for original_dict in dict_list:
        if key not in original_dict:
            raise KeyError(f"The key '{key}' is not in the original dictionary.")
        new_key = original_dict[key]
        new_dict[new_key] = original_dict
    return new_dict

def ac_treeTolist(ac_tree):
    return_elements = []
    for line in ac_tree.split("\n")[1:]:
        splited_element = line.strip()
        match = re.match(r"(\w+)\s'(.*?)'(?:\s(\w+:\s.+))?", splited_element)
        if not match:
            pattern = r'(\w+)\s+"([^"]+)"'

            match = re.search(pattern, splited_element)

        if match:
            field_type = match.group(1)
            label = match.group(2)
            try:
                attribute_name = match.group(3)
            except:
                attribute_name = ""
            if field_type == 'group':
                continue
            return_elements.append({"Element_Type":field_type, "Element_Text": label, "Element_Property": attribute_name})
    return return_elements


def write2json(data, json_file):
    with open(json_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def filter_elements_by_type(dict_list, values_of_interest):
    """
    Filters a list of dictionaries based on the value of 'Element_Type' key.

    Parameters:
    dict_list (list): List of dictionaries to filter.
    values_of_interest (list): List of values to filter by.

    Returns:
    list: A filtered list of dictionaries.
    """
    return [d for d in dict_list if d.get('Element_Type') in values_of_interest]
def has_textbox(dict_list_tuple):
    for element in dict_list_tuple:
        if element[0].get('Element_Type') == 'textbox' and 'search' not in element[0].get('Element_Text').lower():
            return True
    return False
def match_elements(dict_list, another_list):
    matches = []

    for d in dict_list:
        element_type = d.get('Element_Type')
        value = d.get('Element_Text')
        for i, elem in enumerate(another_list):
            if elem.get('Element_Type') == element_type and strip_multiple_chars(elem.get('Element_Text').lower()) == strip_multiple_chars(value.lower()):
                matches.append((elem, i))
        match_has_textbox = has_textbox(matches)
        if not match_has_textbox:
            for i, elem in enumerate(another_list):
                if elem.get('Element_Type') == 'textbox' and 'search' not in elem.get('Element_Text').lower():
                    matches.append((elem, i)) 
    return matches

def strip_multiple_chars(s, chars=":'\"."):
    # Create a translation table where each character in chars maps to None
    translation_table = str.maketrans('', '', chars)
    
    # Use the translation table to remove the specified characters
    return s.translate(translation_table)

def find_start_idx_with_heading(ac_tree, start_idx):
    # if head_flag:
    #     for i in range(start_idx-1, -1, -1):
    #         if ac_tree[i]['Element_Type'] == 'heading':
    #             return i
    if start_idx >6:
        for i in range(start_idx-1, start_idx-7, -1):
            if ac_tree[i]['Element_Type'] in ['heading']:
                return i, True
        return start_idx-6, False
    else:
        for i in range(start_idx-1, 0, -1):
            if ac_tree[i]['Element_Type'] in ['heading']:
                return i, True
        return 0, False
    

def find_end_idx_with_heading(ac_tree, end_idx, head_flag):
    if end_idx+5 > len(ac_tree):
        end_candidate_idx = len(ac_tree)
    else:
        end_candidate_idx = end_idx +5
    if head_flag:
        for i in range(end_idx, len(ac_tree)):
            if ac_tree[i]['Element_Type'] == 'heading':
                return i
    if end_idx + 5 < len(ac_tree):
        return end_idx + 5
    else:
        return len(ac_tree)
def filter_elements_after_button(element_list):
    # Step 1: Sort the list by the index
    sorted_element_list = sorted(element_list, key=lambda x: x[1])
    
    # Step 2: Find the highest index of a button
    max_button_index = None
    for element, index in sorted_element_list:
        if element.get('Element_Type') == 'button':
            max_button_index = index
    
    # If no button found, return the original sorted list
    if max_button_index is None:
        return sorted_element_list
    
    # Step 3: Filter out elements that come after the button
    filtered_elements = [item for item in sorted_element_list if item[1] <= max_button_index]
    
    return filtered_elements

def count_textbox_elements(element_list):
    count = 0
    for element in element_list:
        if element.get('Element_Type') == 'textbox':
            count += 1
    return count

def filter_elements_before_last_button(element_list, textbox_count):
    # Find the index of the last button
    button_idx = -1
    for i in range(len(element_list)):
        if element_list[i][0].get('Element_Type') == 'button':
            button_idx = i

    # If no button is found, return an empty list
    if button_idx == -1:
        return []

    count = 0
    selected_elements = []

    # Add the last button to the selected elements
    selected_elements.append(element_list[button_idx])

    # Iterate backward from the last button index
    for i in range(button_idx - 1, -1, -1):
        selected_elements.append(element_list[i])
        if element_list[i][0].get('Element_Type') == 'textbox':
            count += 1
            if count == textbox_count:
                break

    # Reverse the list to maintain the original order
    selected_elements.reverse()

    return selected_elements

def has_element_type(element_list, element_type):
    for element in element_list:
        if element[0].get('Element_Type') == element_type:
            return True
    return False

def find_first_button_after_last_textbox(element_list, ac_tree):
    last_textbox_idx = -1
    first_button_after_textbox_idx = -1

    # Find the last textbox index
    for i in range(len(element_list)):
        if element_list[i][0].get('Element_Type') == 'textbox':
            last_textbox_idx = element_list[i][1]

    # Find the first button after the last textbox
    if last_textbox_idx != -1:
        for idx, element in enumerate(ac_tree[last_textbox_idx:]):
            if element.get('Element_Type') == 'button':
                first_button_after_textbox_idx = last_textbox_idx + idx
                break

    return last_textbox_idx, first_button_after_textbox_idx

def extract_blocks(elements):
    blocks = []
    current_block = []
    for element in elements:
        if element['Element_Type'] == 'heading' and current_block:
            blocks.append(current_block)
            current_block = []
        current_block.append(element)
    if current_block:
        blocks.append(current_block)
    return blocks

def find_blocks_with_textbox(blocks):
    """
    """
    blocks_with_textbox = []
    current_group = []
    found_first_group = False

    for block in blocks:
        has_heading = any(element['Element_Type'] == 'heading' for element in block)
        has_textbox = any(element['Element_Type'] == 'textbox' for element in block)
        
        # 如果当前块包含textbox
        if has_textbox:
            current_group.extend(block)
            found_first_group = True
        # 如果当前块包含heading且我们已经找到了包含textbox的块
        elif has_heading and found_first_group:
            current_group.extend(block)
        # 如果我们已经在收集块，但遇到既没有heading也没有textbox的块
        elif found_first_group:
            # 如果已经收集了一些块，就结束收集
            if current_group:
                return current_group
            found_first_group = False
            current_group = []

    # 返回最后收集的组（如果有的话）
    return current_group if current_group else []

def clean_form_elements(form):
    """
    Clean a single form by removing duplicate consecutive elements.
    """
    if not form:
        return []
    
    cleaned_elements = []
    last_text = None
    
    def is_interactive(elem_type):
        return elem_type in {'checkbox', 'textbox', 'radio', 'toggle', 'button', 'option'}
    
    for elem in form:
        if elem['Element_Text'] in ['reCAPTCHA']:
            continue
        # 如果是textbox且有Visual_Element_Text，更新Element_Text
        if elem['Element_Type'] == 'textbox' and 'Visual_Element_Text' in elem:
            elem['Element_Text'] = elem['Visual_Element_Text']
            
        # 交互元素直接保留
        if is_interactive(elem['Element_Type']):
            cleaned_elements.append(elem)
            last_text = None  # 重置last_text，因为交互元素不参与连续性判断
            continue
            
        # 对于非交互元素，检查是否与上一个元素文本相同
        current_text = elem['Element_Text']
        if current_text != last_text:
            cleaned_elements.append(elem)
            last_text = current_text
    
    return cleaned_elements

def clean_duplicate_elements(form):
    """
    Clean form elements by removing duplicates (not necessarily consecutive),
    prioritizing interactive elements.
    """
    if not form:
        return []
    
    def is_interactive(elem_type):
        return elem_type in {'checkbox', 'textbox', 'radio', 'toggle', 'button', 'option'}
    
    # 第一遍：找出每个文本对应的最佳元素
    text_to_best_elem = {}
    for elem in form:
        
        # 如果是textbox且有Visual_Element_Text，更新Element_Text
        if elem['Element_Type'] == 'textbox' and 'Visual_Element_Text' in elem:
            elem['Element_Text'] = elem['Visual_Element_Text']
            
        text = elem['Element_Text']
        if text not in text_to_best_elem:
            text_to_best_elem[text] = elem
        elif is_interactive(elem['Element_Type']) and not is_interactive(text_to_best_elem[text]['Element_Type']):
            # 如果新元素是交互元素而当前保存的不是，更新为新元素
            text_to_best_elem[text] = elem
    
    # 第二遍：按原始顺序重建列表，只保留每个文本的最佳元素
    seen_texts = set()
    cleaned_elements = []
    for elem in form:
        text = elem['Element_Text']
        if text not in seen_texts:
            cleaned_elements.append(text_to_best_elem[text])
            seen_texts.add(text)
    
    return cleaned_elements

def filter_forms(form_data):
    ret_list = []
    i = 0
    while i < len(form_data):
        each = form_data[i]
        each['Element_Text'] = each['Element_Text'].strip().replace('*', '').replace('\n', '').replace(":","")
        if 'Visual_Element_Text' in each:
            each['Visual_Element_Text'] = each['Visual_Element_Text'].strip().replace('*', '').replace('\n', '').replace(":","")
        # Skip empty non-interactive elements
        if each['Element_Type'] not in ['textbox', 'button', 'checkbox', 'radio', 'toggle'] and each['Element_Text'] in ['', '*', '\n']:
            i += 1
            continue
            
        # Check for staticText and link with same content (in either order)
        if i < len(form_data) - 1:
            next_elem = form_data[i + 1]
            if ((each['Element_Type'] == 'StaticText' and next_elem['Element_Type'] == 'link') or
                (each['Element_Type'] == 'link' and next_elem['Element_Type'] == 'StaticText')) and \
                each['Element_Text'] == next_elem['Element_Text']:
                i += 1
                continue
            
        ret_list.append(each)
        i += 1
        
    return ret_list

def get_textbox_blocks(elements):
    blocks = extract_blocks(elements)
    ret_block = find_blocks_with_textbox(blocks)
    ret_block = filter_forms(ret_block)
    ret_block = merge_checkbox_text(ret_block)
    ret_block = clean_form_elements(ret_block)
    ret_block = clean_duplicate_elements(ret_block)
    return ret_block

def merge_checkbox_text(form):
    """
    Process a single form to merge text around empty checkboxes.
    
    Args:
        form: List of form elements
    Returns:
        Processed form with merged checkbox text
    """
    i = 0
    while i < len(form):
        # Find LayoutTableCell
        if form[i]["Element_Type"] == "LayoutTableCell":
            layout_text = form[i]["Element_Text"]
            
            # Look for checkbox in next few elements
            j = i + 1
            while j < len(form) and j < i + 10:  # Limit search to next 10 elements
                if form[j]["Element_Type"] == "checkbox" and form[j]["Element_Text"] == "":
                    # Collect text from following StaticText elements
                    combined_text = []
                    k = j + 1
                    while (k < len(form) and 
                          k < j + 10 and  # Limit search to next 10 elements
                          form[k]["Element_Type"] == "StaticText"):
                        combined_text.append(form[k]["Element_Text"])
                        k += 1
                    
                    # If combined text matches layout text, update checkbox
                    combined = "".join(combined_text)
                    if combined == layout_text or layout_text.replace(" ", "") == combined.replace(" ", ""):
                        form[j]["Element_Text"] = layout_text
                        # Remove the StaticText elements we combined
                        del form[j+1:k]
                    break
                j += 1
        i += 1
    return form


def form_actree_match(form_data, ac_tree):
    form_elements = filter_elements_by_type(form_data, ['textbox','button'])
    # print(form_elements)
    matched_elements = match_elements(form_elements, ac_tree)
    if not has_element_type(matched_elements, 'button'):
        sorted_element_list = sorted(matched_elements, key=lambda x: x[1])
        last_textbox_idx, button_idx = find_first_button_after_last_textbox(sorted_element_list, ac_tree)
        for idx, each in enumerate(ac_tree[last_textbox_idx: button_idx+1]):
            sorted_element_list.append((each, last_textbox_idx+idx))
    else:
        sorted_element_list = sorted(filter_elements_after_button(matched_elements), key=lambda x: x[1])
        textbox_cnt = count_textbox_elements(form_data)
        sorted_element_list = filter_elements_before_last_button(sorted_element_list, textbox_cnt)
    # print(sorted_element_list)
    # head_in_tree = heading_in_tree(ac_tree)
    # if heading_in_tree:
    #    start_idx = sorted_element_list[0][1]
    #    end_idx = sorted_element_list[-1][1] 
    # try:
    # print(sorted_element_list)
    if len(sorted_element_list)>0:
        start_idx = sorted_element_list[0][1]
        end_idx = sorted_element_list[-1][1]
        if start_idx > 6:
            new_start_idx, heading_flag = find_start_idx_with_heading(ac_tree, start_idx)
            new_end_idx = find_end_idx_with_heading(ac_tree, end_idx, heading_flag)
            selected_elements = ac_tree[new_start_idx:new_end_idx]
        else:
            new_start_idx, heading_flag = find_start_idx_with_heading(ac_tree, start_idx)
            new_end_idx = find_end_idx_with_heading(ac_tree, end_idx, heading_flag)
            selected_elements = ac_tree[0:new_end_idx]
    else:
        return []
    # except Exception as e:
    #     print(e)
    #     print()
        # print(111)
        # return []
    return selected_elements
    # print(selected_elements)
    
def checkbox_exists(form):
    final_list = []
    for each in form:
        if each['Element_Type'] in ['checkbox', 'radion']:
            final_list.append(each)
    if len(final_list) > 0:
        return final_list, True
    return final_list, False 
def combine_forms(ori_form, extracted_form):
    combined_form = []
    textbox_idx = 0  # Index to track textbox elements in form2
    button_idx = 0
    for i, element in enumerate(extracted_form):
        if element['Element_Type'] == 'textbox':
            while textbox_idx < len(ori_form) and ori_form[textbox_idx]['Element_Type'] != 'textbox':
                textbox_idx += 1
            if textbox_idx < len(ori_form) and ori_form[textbox_idx]['Element_Type'] == 'textbox':
                # Replace the text from form2
                element['Visual_Element_Text'] = ori_form[textbox_idx]['Element_Text']
                textbox_idx += 1
            else:
                element['Visual_Element_Text'] = ''
        elif element['Element_Type'] == 'button':
            # Find the corresponding button in form2
            while button_idx < len(ori_form) and ori_form[button_idx]['Element_Type'] != 'button':
                button_idx += 1
            if button_idx < len(ori_form) and ori_form[button_idx]['Element_Type'] == 'button':
                # Copy the icon from form2 if it exists
                if 'icon' in ori_form[button_idx]:
                    element['icon'] = ori_form[button_idx]['icon']
                else:
                    element['icon'] = ''
                element['Visual_Element_Text'] = ori_form[button_idx]['Element_Text']
                button_idx += 1
            else:
                element['icon'] = ''
                # element['Visual_Element_Text'] = ori_form[button_idx]['Element_Text']
        combined_form.append(element)

    checkbox_ori_list, checkbox_exists_ori_form = checkbox_exists(ori_form)
    checkbox_combine_list, checkbox_exists_combine_form = checkbox_exists(combined_form)

    if not checkbox_exists_combine_form and checkbox_exists_ori_form:
        combined_form.extend(checkbox_ori_list)
    

    return combined_form

def save_actree_trace(folder):
    with open(os.path.join(folder, 'overall2.pkl'), 'rb') as file:
        loaded_trajectory = pickle.load(file)
    # traces = loaded_trajectory[0::2]
    form_data = get_json(os.path.join(folder,"overall.json"))
    md5_array = generate_new_dict(form_data, "image")
    print(len(form_data) == len(md5_array))
    for trace in loaded_trajectory:
        image_md5 = get_image_md5(trace['image'])
        if image_md5 not in md5_array:
            continue
        form_info = md5_array[image_md5]
        
        processed_actree = ac_treeTolist(trace['ac_tree'])
        processed_actree.append(form_info)
        # write2json(trace['obs'], f"{image_md5}_tree.json")
        write2json(processed_actree, os.path.join(folder, "extracted_image", f"{image_md5}.json"))

def heading_in_tree(tree_data):
    for each in tree_data:
        if each['Element_Type'] in ['heading']:
            return True
    return False
def get_forms(folder):
    all_form_data = get_json(os.path.join(folder,"overall.json"))
    # print(len(form_data))
    for idx, each in enumerate(all_form_data):
        image_md5 = each['image']
        data = get_json(os.path.join(folder, "extracted_image", f"{image_md5}.json"))
        tree_data = data[:-1]
        form_result = []
        if not isinstance(data[-1]['result'], dict):
            continue
        for form_id, form_data in data[-1]['result'].items():
            # print('----------------------------------------------------------')
            form_ac_tree = form_actree_match(form_data, tree_data)
            # print(form_ac_tree)
            combined_form = combine_forms(form_data, form_ac_tree)
            form_result.append(get_textbox_blocks(combined_form))
        all_form_data[idx]['form_result'] = form_result
    # print(all_form_data)
    # exit()
    write2json(all_form_data, os.path.join(folder, f"overall_final.json"))


if __name__ == "__main__":
    # parent_folder = "/home/ying/projects/web_navigation/webarena/result_folders2"
    # folders = os.listdir(parent_folder)
    # folders = ['dotomi_com']

    parser = ArgumentParser(description="Process form properties")
    parser.add_argument('--folder', type=str, required=True, help='Path to the folder to process')
    args = parser.parse_args()

    folder = args.folder
    files = os.listdir(folder)
    image_actree_folder = os.path.join(folder,"extracted_image")
    os.makedirs(image_actree_folder, exist_ok=True)

    if "overall.json" in files:
        save_actree_trace(folder)
        get_forms(folder)
    # for each in tqdm(folders):
        
    #     # folder = os.path.join(parent_folder, each)
    #     folder = "/home/ying/projects/web_navigation/webarena/results_test/007_com"
    #     files = os.listdir(folder)
    #     image_actree_folder = os.path.join(folder,"extracted_image")
    #     os.makedirs(image_actree_folder, exist_ok=True)

    #     if "overall.json" in files:
    #         save_actree_trace(folder)
    #         get_forms(folder)
            # try:
            #     # save_actree_trace(folder)
            #     get_forms(folder)
            # except Exception as e:
            #     print(e)
            #     print(each)
            # try:
                
            # except Exception as e:
            #     # print(each)
            #     print(e)
            #     continue

    # save_actree_trace(folder)
    # get_forms(folder)
    