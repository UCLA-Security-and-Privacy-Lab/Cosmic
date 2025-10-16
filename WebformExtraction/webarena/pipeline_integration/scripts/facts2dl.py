import os
import json
import argparse
from tqdm import tqdm
def facts2dl(facts_dict):
    final_dict = {}
    # print(facts_dict["element"])
    final_dict["element"] = [
        f"{elem.get('element_id')}\t{str(elem.get('element_type', 'None')).lower()}\t{str(elem.get('element_text', 'None')).lower()}" 
        for elem in facts_dict["element"]
    ]
    final_dict["element_required"] = [f"{elem['element_id']}\t{elem['element_required']}" for elem in facts_dict["required"]]
    # final_dict["crt"] = [f"{elem['sent_id']}\t{elem['data_controller'].lower()}\t{elem['action'].lower()}\t{elem['purpose'].lower()}\t{elem['neg']}\t{elem['element'].lower()}" for elem in facts_dict["crt_attr"]]
    final_dict['crt'] = []
    for elem in facts_dict["crt_attr"]:
        tmp_dict = {}
        tmp_dict['sent_id'] = elem['sent_id']
        tmp_dict['data_controller'] = elem['data_controller'].lower() if elem['data_controller'] else "None"
        tmp_dict['action'] = elem['action'].lower() if elem['action'] else "None"
        try:
            tmp_dict['neg'] = elem['neg']
        except:
            tmp_dict['neg'] = "None"
        tmp_dict['element'] = elem['element'].lower() if elem['element'] else "None"
        for each_purpose in elem['purpose']:
            tmp_dict['purpose'] = each_purpose.lower() if each_purpose else "None"
            str_tmp = f"{tmp_dict['sent_id']}\t{tmp_dict['data_controller']}\t{tmp_dict['action']}\t{tmp_dict['purpose']}\t{tmp_dict['neg']}\t{tmp_dict['element']}"
            final_dict['crt'].append(str_tmp)
      
    final_dict["element_status"] = [f"{elem['element_id']}\t{elem['element_status'].lower()}" for elem in facts_dict["status"]]
    final_dict['cluster_purposes'] = []
    for elem in facts_dict["cluster_purposes"]:
        if elem == 'cluster_unknown':
            continue
        # print(elem)
        label = elem['label'].lower()
        for item in elem['items']:
            tmp_dict = {}
            tmp_dict['sent_id'] = item['sent_id']
            tmp_dict['label'] = label
            tmp_dict['purpose'] = item['purpose'].lower()
            str_tmp = f"{tmp_dict['sent_id']}\t{tmp_dict['label']}\t{tmp_dict['purpose']}"
            final_dict['cluster_purposes'].append(str_tmp)
    
    final_dict['eid_sent_id'] = [f"{elem['element_id']}\t{elem['text']}\t{elem['sent_id']}" for elem in facts_dict["crt"]]

    final_dict['action_element'] = []
    for elem in facts_dict["action_element"]:
        sent_id = elem['sent_id']
        # print(elem)
        if elem['field_description']:
            field_description = elem['field_description'].lower()
        else:
            continue
            # field_description = ""
        if elem['match']:
            if len(elem['match']) > 0:
                matched_element_id = elem['match']['element_id']
            else:
                continue
        else:
            continue
        str_tmp = f"{sent_id}\t{field_description.lower()}\t{matched_element_id}"
        final_dict['action_element'].append(str_tmp)
        
    # final_dict['action_element'] = [f"{elem['sent_id']}\t{elem['field_description']}\t{elem['match']['element_id']}" for elem in facts_dict["action_element"]]

    final_dict['withdraw'] = [f"{elem['sent_id']}\t{elem['text']}" for elem in facts_dict["withdraw"]]

    final_dict['withdraw_method'] = [f"{elem['sent_id']}\t{elem['withdraw_method']}" for elem in facts_dict["withdraw_method"]]
    # final_dict["crt"] = [f"{elem['sent_id']}\t{elem['text']}" for elem in facts_dict["crt"]]
    return final_dict

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--websites_folder", type=str, default="adpearance_com")
    return parser.parse_args()
def deduplicate_forms(data):
   
    seen_structures = {}
    unique_forms = []
    
    for form in data:
        search_exist = [f for f in form['fields'] if 
            'search' in f['id'].lower() or 
            'search' in str(f['type']).lower() or 
            'search' in " ".join(f['class']) or 
            'search' in form.get('placeholder', '').lower()
        ]
        if len(search_exist) > 0:
            continue
        # 创建表单结构的指纹 - 忽略ID等唯一标识符
        form_fingerprint = {
            'method': form['method'],
            'action': form['action'],
            'field_types': tuple((f['placeholder'], f['type'], f.get('required', False)) 
                               for f in form['fields']),
            'text_content': tuple(t['text'] for t in form['text_content']) if form['text_content'] else ()
        }

        
        # 转换为字符串用作字典键
        fingerprint_key = str(form_fingerprint)
        # print(fingerprint_key)
        if fingerprint_key not in seen_structures:
            seen_structures[fingerprint_key] = form['id']
            # print(fingerprint_key)
            unique_forms.append(form)
    return unique_forms
if __name__ == "__main__":
    base_path = "/home/ying/projects/web_navigation/webarena/results_test"
    args = arg_parse()
    websites_folder = args.websites_folder

    websites_folders = os.listdir(base_path)
    websites_folders = ['www_metrixlab_com']
    for each_website in tqdm(websites_folders):
        website_path = os.path.join(base_path, each_website)
        aligned_form_path = os.path.join(website_path, "merged_images")
        facts_folder = os.path.join(website_path, "facts")
        os.makedirs(facts_folder, exist_ok=True)


        for aligned_form_file in os.listdir(aligned_form_path):
            aligned_form_path = os.path.join(aligned_form_path, aligned_form_file, 'aligned_form_data.json')
            tmp_facts_folder = os.path.join(facts_folder, aligned_form_file)


            for each_form in aligned_form_data['forms']:
                facts = each_form['facts']
                final_dict = facts2dl(facts)
                for key, value in final_dict.items():
        
    for each_website in tqdm(websites_folders):
        website_form_folder = os.path.join(base_path, each_website, "form_info")
        if not os.path.exists(website_form_folder):
            continue
        all_forms_file = os.listdir(website_form_folder)
        results_folder = os.path.join(base_path, each_website, "facts")
        if not os.path.exists(results_folder):
            os.makedirs(results_folder, exist_ok=True)
        
        
        forms = []

        for each_form in all_forms_file:
            with open(os.path.join(website_form_folder, each_form), "r") as f:
                form_info = json.load(f)
                forms.extend(form_info['forms'])
        unique_forms = deduplicate_forms(forms)
        for idx, each_form in enumerate(unique_forms):
            facts_folder = os.path.join(results_folder, f"{idx}")
            os.makedirs(facts_folder, exist_ok=True)
            # print(facts_folder)
            facts = each_form['facts']
            # print(facts)
            final_dict = facts2dl(facts)
            for key, value in final_dict.items():
                path = os.path.join(facts_folder, f"{key}.facts")
                with open(path, "w") as f:
                    f.write("\n".join(value))

        # for each_form in forms:
        #     facts = each_form['forms'][0]['facts']
            
    # with open(os.path.join(base_path, websites_folder, "form_info", "form_0.json"), "r") as f:
    #     facts_dict = json.load(f)
    # for idx, each in enumerate(facts_dict['forms']):
    #     facts = each['facts']
    #     facts_save_folder = f"/home/ying/projects/web_navigation/consent_management/compliance_check/code/test_forms/test_{idx+1}"
    #     os.makedirs(facts_save_folder, exist_ok=True)
    #     final_dict = facts2dl(facts)
    #     for key, value in final_dict.items():
    #         path = os.path.join(facts_save_folder, f"{key}.facts")
    #         with open(path, "w") as f:
    #             f.write("\n".join(value))
    #     print(final_dict)


