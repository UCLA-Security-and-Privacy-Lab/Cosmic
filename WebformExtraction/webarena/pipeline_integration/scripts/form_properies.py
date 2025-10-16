'''
extract form properties from form_info
'''
import sys
import argparse
import json
import os
from tqdm import tqdm
def form_process(form_info):
    form_properties = {'ELEMENT':[], 'TEXT':[], 'ELEMENT_STATUS':[]}
    text = []
    for idx,_ in enumerate(form_info['fields']):
        if _['type'] is None:
            continue
        tmp_dict = {}
        tmp_dict['element_id'] = idx
        if _['tag'] in ['input','textarea'] and _['type'] in ['text', 'email', 'tel','textarea']:
            tmp_dict['element_type'] = 'textbox'
        elif _['tag'] in ['input'] and _['type'] not in ['text']:
            tmp_dict['element_type'] = _['type']
        else:
            tmp_dict['element_type'] = _['tag']  
        if tmp_dict['element_type'] in ['checkbox', 'radio', 'option']:
            all_text = ''
            # Extract type and class values
            if 'type' in _:
                all_text += f"type: {_['type']} "
            if 'class' in _:
                class_value = _['class']
                if isinstance(class_value, list):
                    class_value = ' '.join(class_value)
                all_text += f"class: {class_value}"
            if 'id' in _:
                all_text += f"id: {_['id']}"
            if ('checked' in all_text and 'unchecked' not in all_text):
                tmp_dict['element_status'] = 'checked'
            elif ('checked' not in all_text and 'unchecked' in all_text):
                tmp_dict['element_status'] = 'unchecked'
            else:
                tmp_dict['element_status'] = 'unchecked'
        
        tmp_dict['element_required'] = 'required' if _['required'] else 'optional'
        tmp_text = (_['text'] if 'text' in _ and _['text']!=''
                   else _['label_text'] if 'label_text' in _ and _['label_text']!=''
                   else _['label'] if 'label' in _ and _['label']!=''
                   else _['visual_text'] if 'visual_text' in _ and _['visual_text']!=''
                   else _['id'] if 'id' in _ and _['id']!='' else '')
        tmp_dict['element_text'] = tmp_text
        if tmp_dict ['element_text'] == '':
            element_text = _['placeholder'] if 'placeholder' in _ else ''
            tmp_dict['element_text'] = element_text
        tmp_dict['placeholder'] = _['placeholder'] if 'placeholder' in _ else ''
        form_properties['ELEMENT'].append(tmp_dict)
        text.append(tmp_text)
    for _ in form_info['text_content']:
        text = [_.replace(' .', '.') for _ in text]
        if isinstance(_, str):
            filtered_content = [_] if _ not in text and not any(_.startswith(t) for t in text) else []
        else:
            filtered_content = [
                i['text'] if isinstance(i, dict) else i 
                for i in _['text'] 
                if (i['text'] if isinstance(i, dict) else i) not in text 
                and not any((i['text'] if isinstance(i, dict) else i).startswith(t) for t in text)
            ]

        sentences = []
        current_sentence = []

        for content in filtered_content:
            if content.strip().endswith('.'):
                # 
                if current_sentence:
                    sentences.append(" ".join(current_sentence))
                    current_sentence = []
                # 直接添加以句号结尾的句子
                sentences.append(content.strip())
            else:
                current_sentence.append(content.strip())

        # 处理最后可能剩余的未以句号结尾的内容
        if current_sentence:
            combined = " ".join(current_sentence)
            if "   " in combined:
                sentences.extend([s.strip() for s in combined.split("   ") if s.strip()])
            else:
                sentences.append(combined)

        # 过滤空字符串
        sentences = [_ for _ in sentences if _ != '']
        form_properties['TEXT'].extend(sentences)
    for _ in form_info['surrounding_text']:
        # print(_)
        sentences = " ".join(_['text'])
        sentences = sentences.split("   ") if "   " in sentences else sentences.split(".")
        sentences = [_.strip() for _ in sentences if _.strip() != '']
        form_properties['TEXT'].extend(sentences)
    form_properties['TEXT'] = list(set(form_properties['TEXT']))
    return form_properties

def read_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def write_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--websites_folder', type=str, default='38degrees_org_uk')
    return parser.parse_args()

if __name__ == '__main__':
    form_info = read_json('/home/ying/projects/web_navigation/webarena/results_test/5top100_com/form_info/form_0.json')
    # form_properties = form_process(form_info['forms'][0])
    result_folder = "/home/ying/projects/web_navigation/webarena/results_test"
    websites_folder = os.listdir(result_folder)
    
    # args = arg_parse()
    # websites_folder = [args.websites_folder]
    # websites_folder = ['shop_sandisk_com']
    # websites_folder = ['www_metrixlab_com']
    for website_folder in tqdm(websites_folder):
        website_path = os.path.join(result_folder, website_folder)
        merged_images = os.path.join(website_path, "merged_images")
        if not os.path.exists(merged_images):
            continue
        for _ in os.listdir(merged_images):
            image_folder = os.path.join(merged_images, _)
            aligned_form_path = os.path.join(image_folder, "aligned_form_data.json")
            if not os.path.exists(aligned_form_path):
                with open("error_form_properties.txt", "a") as f:
                    f.write(aligned_form_path + '\n')
                continue
            aligned_form_data = read_json(aligned_form_path)
            for each_form in aligned_form_data['forms']:
                # if 'properties' in each_form:
                #     continue
                form_properties = form_process(each_form)
                each_form['properties'] = form_properties
            # filter forms that don't have any textbox elements
            aligned_form_data['forms'] = [
                form for form in aligned_form_data['forms']
                if any(element['element_type'] == 'textbox' 
                      for element in form['properties']['ELEMENT'])
            ]
            write_json(aligned_form_data, aligned_form_path)
    # for website_folder in tqdm(websites_folder):
    #     website_path = os.path.join(result_folder, website_folder)
    #     form_info_path = os.path.join(website_path, 'form_info')
    #     if not os.path.exists(form_info_path):
    #         continue
    #     form_files = os.listdir(form_info_path)
    #     for form_file in form_files:
    #         form_info = read_json(os.path.join(form_info_path, form_file))
    #         for each_form in form_info['forms']:
    #             # if 'properties' in each_form:
    #             #     continue
    #             form_properties = form_process(each_form)
    #             each_form['properties'] = form_properties
    #         # filter forms that don't have any textbox elements
    #         form_info['forms'] = [
    #             form for form in form_info['forms']
    #             if any(element['element_type'] == 'textbox' 
    #                   for element in form['properties']['ELEMENT'])
    #         ]
    #         # print(os.path.join(form_info_path, form_file))
    #         write_json(form_info, os.path.join(form_info_path, form_file))
            # print(website_path)
            # print(form_info)
    
    # print(form_properties)
    # write_json(form_properties, 'results_test/5g_nttdata_com/form_properties/form_0.json')
