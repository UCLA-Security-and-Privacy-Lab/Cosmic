import pickle
import sys
import numpy as np
import re
sys.path.append("/home/ying/projects/web_navigation/webarena")
import os
from browser_env import (
    Action,
    ActionTypes,
    ScriptBrowserEnv,
    StateInfo,
    Trajectory,
    create_stop_action,
)

from help_scripts import select_unique_trees, process_accessibility_tree2, extract_accessibility_label,extract_textboxes
import argparse
# 1. get the accessibility tree to determine the same/similar structure for a filteration
# 2. select from one of the structures to determine which one to analyze
# 3. 
def parse_args():
    parser = argparse.ArgumentParser(
        description="Run filter on parsed web pages"
    )
    parser.add_argument('--folder', type=str)
    args = parser.parse_args()
    return args

def get_trajectory(pickle_file):
    with open(pickle_file, 'rb') as f:
        loaded_trajectory = pickle.load(f)
    return loaded_trajectory
def contain_any(element, list_):
    for _ in list_:
        if _ in element:
            return True
    return False
def get_info_from_trace(trajectory, pkl):
    ret_list = []
    action_info = trajectory[1::2]
    state_info_elements = trajectory[0::2]
    # print(len(action_info))
    # print(len(state_info_elements))
    # print(action_info)
    if len(action_info) != len(state_info_elements):
        try:
            action_info.append(action_info[-1])
        except:
            action_info = []
            action_info.append({"action_type": ActionTypes.GOTO_URL})
        # state_info_elements = state_info_elements[:-1]
    assert(len(action_info) == len(state_info_elements))
    for idx, each in enumerate(state_info_elements):
        try:
            if idx != 0:
                if action_info[idx-1]['action_type'] == ActionTypes.TYPE:
                    continue
            tmp_dict = {}
            tmp_dict['url'] = each['info']['page'].url
            if contain_any(tmp_dict['url'], ['googl','youtu.be','twitter','instagram', 'google','microsoft','youtube', 'stackoverflow', 'amazon', 'x.com', 'facebook', 'github', 'gitlab', 'apple','linkedin','bing', 'icloud','.ru','.jp','.kz','.tr','.ua','.pl','.de','.tw','.az']):
                continue

            tmp_dict['html'] = each['info']['page'].content
            tmp_dict['image'] = each['observation']['image']
            tmp_dict['ac_tree'] = "\n".join(process_accessibility_tree2(each['observation']['text']))
            tmp_dict['ac_tree_label'] = "\n".join(extract_accessibility_label(tmp_dict['ac_tree'].split('\n'))) 
            tmp_dict['textboxes'] = extract_textboxes(tmp_dict['ac_tree'].split('\n'))
            # tmp_dict['file'] = pkl
            # tmp_dict['index'] = idx
            tmp_dict['iframes'] = []
            for _ in each['info']['iframe']:
                sub_tmp_dict = {}
                if '<form' in _['frame_content']:
                    sub_tmp_dict['frame_content'] = _['frame_content']
                    sub_tmp_dict['title'] = _['title']
                    sub_tmp_dict['url'] = _['url']
                    tmp_dict['iframes'].append(sub_tmp_dict)
                
            # tmp_dict['iframe_textboxes']
            # tmp_dict['obs'] = each['info']['obs']
            if 'textbox' in tmp_dict['ac_tree'] or len(tmp_dict['iframes'])>0:
                ret_list.append(tmp_dict)
            else:
                continue
        except Exception as e:
            print(e)
            continue
    return ret_list

def make_hashable(obj, ignore_keys=None):
    """Recursively convert dictionary values to hashable types, ignoring specific keys."""
    if isinstance(obj, (list, tuple)):
        return tuple(make_hashable(e, ignore_keys) for e in obj)
    elif isinstance(obj, dict):
        # Exclude the keys in ignore_keys from the hashable conversion
        return tuple(sorted((k, make_hashable(v, ignore_keys)) for k, v in obj.items() if k not in ignore_keys))
    elif isinstance(obj, np.ndarray):
        return tuple(obj.tolist())  # Convert numpy array to list, then to tuple
    return obj

def tuple_to_dict(t, original_dict, ignore_keys=None):
    """Convert a hashable tuple back to a dictionary."""
    d = {}
    for k, v in t:
        if isinstance(v, tuple):
            try:
                # Attempt to convert back to numpy array if it was originally one
                v = np.array(v)
            except ValueError:
                # If conversion fails, leave it as tuple
                pass
        d[k] = v
    # Add the ignored keys back from the original dictionary if they exist
    if ignore_keys:
        for key in ignore_keys:
            if key in original_dict:
                d[key] = original_dict[key]
    return d


def get_unique_traces(trace_list):
    ignore_keys = ["image", "ac_tree_label"]

    unique_dict_set = set()
    original_dict_mapping = {}
    # 
    for d in trace_list:
        hashable = make_hashable(d, ignore_keys)
        if hashable not in unique_dict_set:
            unique_dict_set.add(hashable)
            original_dict_mapping[hashable] = d

    unique_dict_list = [tuple_to_dict(t, original_dict_mapping[t], ignore_keys) for t in unique_dict_set]
    return unique_dict_list

def make_hashable2(value):
    """Convert unhashable types to hashable types."""
    if isinstance(value, np.ndarray):
        return tuple(value.tolist())  # Convert numpy array to tuple
    if isinstance(value, (list, dict)):
        raise TypeError("The provided key cannot be a list or dict.")
    return value

# def remove_duplicates_by_key(dict_list, key):
#     """Remove duplicates in a list of dictionaries based on a specific key."""
#     seen = set()
#     unique_list = []
    
#     for d in dict_list:
#         key_value = make_hashable(d[key])
#         if key_value not in seen:
#             seen.add(key_value)
#             unique_list.append(d)
       
#     return unique_list

def remove_duplicates_by_key(dict_list, key):
    """Remove duplicates in a list of dictionaries based on a specific key."""
    seen = set()
    unique_list = []
    
    for d in dict_list:
        key_value = make_hashable(d[key])
        if key_value in seen:
            # Remove the old entry and add the new one
            unique_list = [item for item in unique_list if make_hashable(item[key]) != key_value]
            unique_list.append(d)
        else:
            seen.add(key_value)
            unique_list.append(d)
    
    return unique_list


def get_unique_textbox_pickle_trace(pickle_folder):

    pkls = [_ for _ in os.listdir(pickle_folder) if _.endswith('.pkl') and _!="overall.pkl"]

    trace_list = []
    for idx, pkl in enumerate(pkls):
        pickle_path = os.path.join(pickle_folder,pkl)
        # print(pickle_path)
        trajectory = get_trajectory(pickle_path)
        trace_list.extend(get_info_from_trace(trajectory, pkl))
    unique_ac_tree_labels = remove_duplicates_by_key(trace_list, "textboxes")
    return unique_ac_tree_labels


# pickle_folders = "/home/ying/projects/web_navigation/webarena/result_folders/3lift_com"

if __name__ == "__main__":
    args = parse_args()
    folder = args.folder
    # folder = "/home/ying/projects/web_navigation/webarena/result_folders/nginx_org"
    return_ac_tree = get_unique_textbox_pickle_trace(folder)
    save_file = os.path.join(folder, "overall.pkl")
    with open(save_file, 'wb') as f:
        pickle.dump(return_ac_tree, f)


