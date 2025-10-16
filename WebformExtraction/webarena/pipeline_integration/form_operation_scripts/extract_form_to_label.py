import sys
sys.path.append("/home/ying/projects/web_navigation/webarena")
from help_scripts import read_json, write2json, is_file_in_folder
import os
import pandas as pd
from PIL import Image
import hashlib
result_folder = "/home/ying/projects/web_navigation/webarena/result_folders"

dirs = os.listdir(result_folder)

def count_textbox_elements(element_list):
    count = 0
    for element in element_list:
        if element.get('Element_Type') == 'textbox':
            if element['Element_Text'].lower() not in ['search']:
                count += 1
    return count

save_list = []
for each_dir in dirs:
    res_folder = os.path.join(result_folder, each_dir)
    if is_file_in_folder("overall_final.json", res_folder):
        data = read_json(os.path.join(res_folder, "overall_final.json"))
        for each in data:
            # if 'textbox' not in str(each['total_form']).lower():
            #     continue
            if 'form_result' not in each:
                continue
            new_form_result = []
            for _ in each['form_result']:
                if count_textbox_elements(_)==0:
                    continue
                new_form_result.append(_)
            each['form_result'] = new_form_result
            each['home_url'] = each_dir
            # print("Image MD5 hash:", hash_md5)
            if isinstance(each['result'], dict):
                each['total_form'] = len(each['form_result'])
            else:
                each['total_form'] = 0
            
        save_list.extend(data)

df = pd.DataFrame(save_list)
df.to_csv('test.csv', index=False)