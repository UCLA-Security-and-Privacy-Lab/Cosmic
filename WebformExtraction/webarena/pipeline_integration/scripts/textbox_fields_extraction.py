import pickle
import json
from bs4 import BeautifulSoup
import sys
sys.path.append("/home/ying/projects/web_navigation/webarena")
import re
import browser_env
# Init an environment
from browser_env import (
    StateInfo,
    Trajectory,
)
def read_pickle(filename):
    with open(filename, 'rb') as file:
        trajectory = pickle.load(file)
    return trajectory

def get_all_forms_and_parent_divs(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    forms = soup.find_all('form')
    results = []
    for form in forms:
        parent_div = form.find_parent('div')
        if parent_div:
            results.append({
                'form': form.prettify(),
                'parent_div': parent_div.prettify()
            })
    return results

# def get_labels_from_form(form_html):
def is_substring_in_list(target, string_list):
    # List to store the sublist of matching strings
    matching_sublist = []
    
    # Iterate through the list and check for the target substring
    for s in string_list:
        if target in s:
            matching_sublist.append(s)
    
    # Return True and the matching sublist if matches are found, otherwise return False and an empty list
    return bool(matching_sublist), matching_sublist

def is_stateinfo(element: dict) -> bool:
    """"""
    return 'observation' in element and 'info' in element

def count_stateinfo_elements(trajectory: Trajectory) -> int:
    """"""
    return sum(1 for element in trajectory if is_stateinfo(element))

def remove_hidden_elements(html):
    soup = BeautifulSoup(html, 'html.parser')
    for element in soup.find_all(style="display: none"):
        element.extract()
    for element in soup.find_all(style="display: none !important"):
        element.extract()
    for element in soup.find_all(['input', 'textarea'], type='hidden'):
        element.extract()
    # if str(soup)!= str(html):
    #     print(soup)
    return str(soup)

def clean_dict(original_dict):
    # Initialize a new dictionary to hold the cleaned data
    cleaned_dict = {}
    # Set to track seen sub-dict keys
    seen_keys = set()
    
    # Iterate through each id in the original dictionary
    for sub_dict in original_dict.values():
        # Iterate through the sub-dict
        for sub_key, value in sub_dict.items():
            # If the sub-key has not been seen, add it to the cleaned dictionary
            cleaned_sub_key = remove_hidden_elements(sub_key)
            if cleaned_sub_key  not in seen_keys:
                cleaned_dict[sub_key] = value
                seen_keys.add(cleaned_sub_key)
    return cleaned_dict

# Function to extract accessibility information
def extract_accessibility_info(element):
    return {
        'type': 'form_element',
        'tag': element.name,
        'id': element.get('id', ''),
        'name': element.get('name', ''),
        'placeholder': element.get('placeholder', ''),
        'aria-required': element.get('aria-required', ''),
        'required': element.get('required', ''),
        'type': element.get('type', ''),
        'label': element.find_previous('label').text if element.find_previous('label') else '',
        'text': element.get_text(strip=True) if element.name == 'button' else ''
    }
# Function to extract static text
def extract_static_text(element):
    return {
        'type': 'static_text',
        'text': element.strip()
    }

# Function to build accessibility tree
def build_accessibility_tree(html):
    soup = BeautifulSoup(html, 'html.parser')
    tree = []
    for element in soup.find_all(['input', 'textarea', 'button', 'p', 'span', 'label']):
        if element.name in ['input', 'textarea', 'button']:
            if element.get('type') != 'hidden':  # Skip hidden elements
                tree.append(extract_accessibility_info(element))
            # tree.append(extract_accessibility_info(element))
        elif element.name in ['p', 'span', 'label']:
            tree.append(extract_static_text(element.get_text()))
    return tree



def get_forms(trajectory):
    # ret_dict = set()
    trajectory = [_ for _ in trajectory if is_stateinfo(_)]
    missed_textboxes = {}
    traces = {}
    for idx,trace in enumerate(trajectory):
        try:
            html_content = trace['info']['page'].content
            accessibility_tree = trace['observation']['text']
            url = trace['info']['page'].url
        except:
            continue
        forms_parent_divs = [_['form'] for _ in get_all_forms_and_parent_divs(html_content)]
        trace_form_dict = {}
        for each_form in forms_parent_divs:
            trace_form_dict[each_form] = []
        
        missed_textboxes[idx] = []
        remain_textboxes = list()
        for line in accessibility_tree.split('\n')[2:]:
            line = line.strip()
            parts = line.split(" ", 2)
            node_id = int(parts[0].strip('[]'))
            role = parts[1]
            name = parts[2] if len(parts) > 2 else ""
            if role in ['textbox', 'checkbox']:
                tmp_name = re.findall(r"'([^']*)'", name)[0].strip()
                name_in_form, tmp_forms = is_substring_in_list(tmp_name, forms_parent_divs)
                for sub_form in tmp_forms:
                    trace_form_dict[sub_form].append({'nodeId': node_id, 'role': role, 'name': name, 'url': url, 'trace':idx})
                # if name_in_form:
                #     trace_form_dict[each_form].append({'nodeId': node_id, 'role': role, 'name': name})
                if not name_in_form:
                    remain_textboxes.append({'nodeId': node_id, 'role': role, 'name': name, 'url': url, 'trace':idx})
        trace_form_dict = {form: elements for form, elements in trace_form_dict.items() if len(elements) > 0}
        trace_form_dict = {form: [build_accessibility_tree(form), elements] for form, elements in trace_form_dict.items()}
        missed_textboxes[idx] = remain_textboxes
        traces[idx] = trace_form_dict
    # print(missed_textboxes)
    # print(traces)
    cleaned_traces = clean_dict(traces)
    ret_tree = tree_extraction(cleaned_traces, trajectory)
    with open("traces.json", "w") as f:
        json.dump(cleaned_traces, f)
    with open("return_tree.json", "w") as f:
        json.dump(ret_tree, f)
    return missed_textboxes

def parse_element(line):
    """Parse a single line to extract element information."""
    parts = line.split(" ", 2)
    node_id = int(parts[0].strip('[]'))
    role = parts[1]
    name = parts[2] if len(parts) > 2 else ""
    element = {'nodeId': node_id, 'role': role, 'name': name, 'children': []}
    return element

def parse_structure(data):
    """Parse the given structure and return a list of all elements."""
    elements = []
    stack = []
    current_parent = None

    for line in data.strip().split('\n'):
        depth = (len(line) - len(line.lstrip('\t'))) // 1
        element = parse_element(line.strip())
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if stack:
            parent = stack[-1][1]
            parent['children'].append(element)
        else:
            elements.append(element)
        stack.append((depth, element))

    return elements

def count_static_text_before_first_input(elements):
    count = 0
    for element in elements:
        if element.get("type") == "text" and element.get("tag") == "input":
            break
        if element.get("type") == "static_text":
            count += 1
    return count
        
def count_static_text_after_last_input(elements):
    # Find the position of the last input element
    last_input_index = -1
    for i, element in enumerate(elements):
        if element.get("type") == "text" and element.get("tag") == "input":
            last_input_index = i
    
    # Count static_text elements after the last input element
    count = 0
    if last_input_index != -1:
        for element in elements[last_input_index + 1:]:
            if element.get("type") == "static_text":
                count += 1
    
    return count

def find_substring_indices(substring, string_list):
    indices = [index for index, string in enumerate(string_list) if substring in string]
    return indices

def find_closest_index(idx, num_list):
    closest_index = -1
    min_diff = float('inf')
    
    for i, num in enumerate(num_list):
        diff = abs(idx - num)
        if diff < min_diff:
            min_diff = diff
            closest_index = i
            
    return closest_index
def process_lines(accessibility_tree, start_idx, end_idx, suffix, suffix_end_found=False, suffix_end=None, extra_lines=0):
    lines = accessibility_tree.split('\n')[start_idx:end_idx + extra_lines]
    if not lines:
        return suffix, suffix_end_found, suffix_end

    idx_offset = 0

    for idx, element in enumerate(lines):
        actual_idx = start_idx + idx + idx_offset
        line = element.strip()
        parts = line.split(" ", 2)
        if len(parts) < 2:
            continue
        role = parts[1]

        if role in ['StaticText', 'link']:
            suffix.append(actual_idx)
        elif role in ['heading']:
            suffix_end_found = True
            suffix_end = actual_idx
            break
        elif role in ['checkbox', 'button', 'combobox']:
            if actual_idx % 10 == 0:
                extra_suffix, suffix_end_found, suffix_end = process_lines(accessibility_tree, actual_idx + 1, actual_idx + 6, suffix, suffix_end_found, suffix_end)
                suffix.extend(extra_suffix)
                idx_offset += 5  # Adjust offset to account for the additional lines processed
            continue

    return suffix, suffix_end_found, suffix_end

def tree_extraction(traces, trajectory):
    trajectory = [_ for _ in trajectory if is_stateinfo(_)]
    ret = []
    for form_html, each_trace in traces.items():
        tmp_dict = {}
        tmp_dict['html'] = form_html
        textboxes = each_trace[1]
        tmp_dict['url'] = textboxes[0]['url']
        textboxes_id = [_['nodeId'] for _ in textboxes]
        accessibility_tree = trajectory[textboxes[-1]['trace']]['observation']['text']
        # tree_structure = parse_structure(accessibility_tree)
        return_tree_lines = []
        for idx, line in enumerate(accessibility_tree.split('\n')[:]):
            line = line.strip()
            parts = line.split(" ", 2)
            try:
                node_id = int(parts[0].strip('[]'))
            except:
                continue
            role = parts[1]
            name = parts[2] if len(parts) > 2 else ""
            # tmp_name = re.findall(r"'([^']*)'", name)[0].strip()
            # attr = name.replace(tmp_name, '').strip()
            if node_id in textboxes_id:
                return_tree_lines.append(idx)
        
        start_idx = return_tree_lines[0]
        if len(return_tree_lines) == 1:
            end_idx = return_tree_lines[0]
        else:
            end_idx = return_tree_lines[1]
        prefix = []
        suffix = []
        prefix_start_found = False
        suffix_end_found = False
        prefix_start = 0
        suffix_end = 0
        for idx,element in enumerate(accessibility_tree.split('\n')[start_idx-10:start_idx]):
            line = element.strip()
            parts = element.split(" ", 2)
            role = parts[1].strip()
            if role in ['StaticText','link']:
                prefix.append(idx)
            if role in ['checkbox', 'button', 'combobox']:
                continue
            if role in ['heading']:
                prefix_start_found = True
                prefix_start = idx
                break
        
        # for idx,element in enumerate(accessibility_tree.split('\n')[end_idx+1:end_idx+11]):
        #     line = element.strip()
        #     parts = element.split(" ", 2)
        #     role = parts[1]
        #     if role in ['StaticText','link']:
        #         suffix.append(idx)
        #     if role in ['checkbox', 'button', 'combobox']:
        #         continue
        #     if role in ['heading']:
        #         suffix_end_found = True
        #         suffix_end = idx
        #         break
        suffix, suffix_end_found, suffix_end = process_lines(accessibility_tree, start_idx, end_idx, suffix)
        return_tree = []

        if prefix_start_found and suffix_end_found:
            return_tree = accessibility_tree.split('\n')[start_idx-10+prefix_start: end_idx+suffix_end]
        elif prefix_start_found and not suffix_end_found:
            if len(suffix)>5:
                tmp_suffix_end = suffix[5]
            else:
                tmp_suffix_end = 10
            return_tree = accessibility_tree.split('\n')[start_idx-10+prefix_start: end_idx+tmp_suffix_end]
        elif not prefix_start_found and suffix_end_found:
            if len(prefix)>5:
                tmp_prefix_start = prefix[-5]
            else:
                tmp_prefix_start = 10
            return_tree = accessibility_tree.split('\n')[start_idx - tmp_prefix_start: end_idx+suffix_end]
        else:
            if len(prefix)>5:
                tmp_prefix_start = prefix[-5]
            else:
                tmp_prefix_start = 10
            if len(suffix)>5:
                tmp_suffix_end = suffix[5]
            else:
                tmp_suffix_end = 10
            
            return_tree = accessibility_tree.split('\n')[start_idx - tmp_prefix_start: end_idx+tmp_suffix_end]
        tmp_dict['tree'] = "\n".join(return_tree)
        # print(return_tree)
        ret.append(tmp_dict)
    return ret
        
        
with open('/home/ying/projects/web_navigation/webarena/result_folders/www_shippingschool_com/trajectory_3.pkl', 'rb') as file:
    loaded_trajectory = pickle.load(file)
get_forms(loaded_trajectory)