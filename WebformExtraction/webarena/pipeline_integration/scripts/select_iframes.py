import os
import subprocess
from tqdm import tqdm
import pickle
import json
def write_iframe_dict(iframe_dict, folder):
    with open(os.path.join(folder), 'w') as f:
            json.dump(iframe_dict, f)
            # f.write(iframe_dict)

def select_iframes(folder):
    iframes = []
    overall_pkl = os.path.join(folder, 'overall.pkl')
    with open(overall_pkl, 'rb') as f:
        overall = pickle.load(f)
    for idx, trajectory in enumerate(overall):
        if len(trajectory['iframes']) > 0:
            for iframe_idx, each_iframe in enumerate(trajectory['iframes']):
                
                # print(each_iframe)
                print(folder)
                write_iframe_dict(each_iframe, os.path.join(folder, f'iframe_pkl_{idx}_{iframe_idx}.json'))
                # iframes.append(each_iframe)
    return iframes



result_folder = "/home/ying/projects/web_navigation/webarena/results_test"
websites_folder = os.listdir(result_folder)

for website_folder in tqdm(websites_folder, total=len(websites_folder)):
    folder_files = os.listdir(os.path.join(result_folder, website_folder))
    iframe_files = [file for file in folder_files if file.startswith('iframe_pkl')]
    if len(iframe_files) > 0:
        continue
    select_iframes(os.path.join(result_folder, website_folder))
    # if 'overall.pkl' in os.listdir(os.path.join(result_folder, website_folder)):
    #     continue
    # subprocess.run(['python', 'select_same_page_structure.py', '--folder', os.path.join(result_folder, website_folder)])
