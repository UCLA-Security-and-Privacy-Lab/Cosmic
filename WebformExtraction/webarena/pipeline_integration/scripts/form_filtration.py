import json
import os
from tqdm import tqdm

def search_login_filter(form_info):
    for form in form_info['forms']:
        if 'login' in form['action'].lower() or 'search' in form['action'].lower():
            #  delete the current form
            form_info['forms'].remove(form)
            continue
        for each in form['fields']:
            if 'search' in each['placeholder'].lower() or 'search' in each['id'].lower():
                form_info['forms'].remove(form)
                break
            
    return form_info

result_folder = "/home/ying/projects/web_navigation/webarena/results_test"
websites_folder = os.listdir(result_folder)
# websites_folder = ['adorethemes_com']
for website_folder in tqdm(websites_folder):
    form_info_folder = os.path.join(result_folder, website_folder, 'form_info')
    if not os.path.exists(form_info_folder):
        continue
    for form_info_file in os.listdir(form_info_folder):
        with open(os.path.join(form_info_folder, form_info_file), 'r') as f:
            form_info = json.load(f)
        form_info = search_login_filter(form_info)
        with open(os.path.join(form_info_folder, form_info_file), 'w') as f:
            json.dump(form_info, f, ensure_ascii=False)
