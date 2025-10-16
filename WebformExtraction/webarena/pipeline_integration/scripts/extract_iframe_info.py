import os
import subprocess
from tqdm import tqdm
import pickle
import json
from bs4 import BeautifulSoup
import argparse
import hashlib
from PIL import Image
import shutil

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
                # print(folder)
                write_iframe_dict(each_iframe, os.path.join(folder, f'iframe_pkl_{idx}_{iframe_idx}.json'))
                # iframes.append(each_iframe)
    return iframes

def extract_form_from_iframe(html_content):
    # Parse the JSON string if needed
    # if isinstance(iframe_json, str):
    #     iframe_data = json.loads(iframe_json)
    # else:
    #     iframe_data = iframe_json
    # print(iframe_json)
    # iframe_data = json.loads(iframe_json)
    
    # Get the HTML content from the frame_content
    # html_content = iframe_data.get('frame_content', '')
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the form
    form = soup.find('form')
    if not form:
        return None
    
    # Extract form details
    form_details = {
        'id': form.get('id', ''),
        'method': form.get('method', ''),
        'action': form.get('action', ''),
        'fields': [],
        'text_content': []  # 新增字段存储文本内容
    }
    
    # 提取表单中的所有文本内容，只保存直接包含文本的元素
    for text_element in form.find_all(['p', 'span','div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        # 只获取直接文本内容，不包括子元素的文本
        direct_text = text_element.find_all(string=True, recursive=False)
        if direct_text:
            texts = [_.strip() for _ in direct_text.split("\n") if _.strip() != '']
            
            for _ in texts:
                form_details['text_content'].append({
                    'tag': text_element.name,
                    'text': _,
                    'class': text_element.get('class', [])
                })
    
    # Find all input fields
    for field in form.find_all(['input', 'textarea', 'select']):
        field_type = field.get('type', '')
        # Skip submit and hidden fields
        if field_type in ['hidden']:
            continue
            
        field_info = {
            'name': field.get('name', ''),
            'type': field_type,
            'id': field.get('id', ''),
            'placeholder': field.get('placeholder', ''),
            'required': field.has_attr('required'),
            'class': field.get('class', [])
        }
        
        # Get label if it exists - only search by 'for' if id is present
        if field.get('id'):
            label = soup.find('label', {'for': field.get('id')})
        else:
            label = None
        if label:
            field_info['label'] = label.text.strip().replace('\n', ' ').replace('  ', ' ')
        
        form_details['fields'].append(field_info)
    
    # Find submit button
    submit_button = form.find('input', {'type': 'submit'})
    if submit_button:
        form_details['submit_button'] = {
            'value': submit_button.get('value', ''),
            'class': submit_button.get('class', [])
        }
    
    return form_details
def deduplicate_forms(data):
   
    seen_structures = {}
    unique_forms = []
    
    for form in data:
        search_exist = [f for f in form['fields'] if 'search' in f['id'].lower() or 'search' in str(f['type']).lower() or 'search' in " ".join(f['class']) or 'search' in form.get('placeholder', '').lower()]
        if len(search_exist) > 0:
            continue
        # print(form['fields'])
        form_fingerprint = {
            'method': form['method'],
            'action': form['action'],
            'field_types': tuple((f['placeholder'], f['type'], f.get('text',''), f.get('label_text', ''), f.get('label', ''), f.get('placeholder', ''), f.get('required', False)) 
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

def extract_forms_with_iframe(html_content):
    """Extract form information from iframe content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    forms = []
    for form in soup.find_all('form'):
        if form.find('input') is not None:
            form_details = {
                'id': form.get('id', ''),
                'method': form.get('method', ''),
                'action': form.get('action', ''),
                'fields': [],
                'text_content': [],
                'surrounding_text': []
            }
            
            # Skip search forms
            if 'search' in form_details['id'].lower():
                continue
            is_search_form = False
            
            # Process form fields
            for field in form.find_all(['input', 'textarea', 'select', 'button']):
                field_type = field.get('type')
                
                if field_type in ['hidden']:
                    continue
                    
                field_info = {
                    'tag': field.name,
                    'name': field.get('name', ''),
                    'type': field_type,
                    'id': field.get('id', ''),
                    'placeholder': field.get('placeholder', ''),
                    'required': field.has_attr('required'),
                    'class': field.get('class', []),
                    'disabled': field.has_attr('disabled')
                }
                
                if 'search' in field_info['name'].lower():
                    is_search_form = True
                    continue

                if field.name == 'button' or field_type in ['submit', 'button']:
                    field_info['text'] = field.text.strip() if field.text.strip() else field.get('value', '')
                
                # Get label
                if field.get('id') != '' and field.get('id') is not None:
                    label = soup.find('label', {'for': field.get('id')})
                    if not label:
                        label = field.find_parent('label')
                    field_info['label'] = label.text.strip().replace('\n', ' ').replace('  ', ' ') if label else ''
                else:
                    field_info['label'] = ''
                    
                form_details['fields'].append(field_info)

            if is_search_form:
                continue

            # Collect all text content from the iframe
            all_text = []
            for text_element in soup.find_all(['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a']):
                # 只获取直接文本内容，不包括子元素的文本
                direct_text = text_element.find_all(string=True, recursive=False)
                if direct_text:
                    remain_text = [i for i in direct_text if i.strip() != '']
                    if len(remain_text) > 0:
                        all_text.append({
                            'tag': text_element.name,
                            'text': remain_text,
                            'class': text_element.get('class', [])
                        })
            
            # Add all text as surrounding text
            form_details['surrounding_text'] = [{
                'position': 'iframe_content',
                'tag': item['tag'],
                'text': item['text']
            } for item in all_text]

            forms.append(form_details)
    
    return forms

def extract_forms_with_input(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    def get_full_sentence(element):
        """获取包含链接的完整句子，保持链接前后的空格"""
        result = []
        current_text = []
        
        for content in element.contents:
            if isinstance(content, str):
                text = content.strip()
                if text:
                    current_text.append(text)
            elif content.name == 'a':
                # 如果当前有累积的文本，先处理它
                if current_text:
                    result.append(' '.join(current_text)+ " ")
                    current_text = []
                # 添加链接文本
                result.append(content.get_text(strip=False))
            else:
                text = content.get_text(strip=False)
                # print(content.name)
                # print(text)
                if text:
                    current_text.append(text.strip())
        # print(current_text)
        # 处理剩余的文本
        if current_text:
            result.extend(current_text)
        
    
        # final_text = ' '.join(result)
        return result
        # return ' ' + final_text if not final_text.startswith(' ') else final_text

    def should_extract_full_sentence(element):
        """Check if element contains links or is a form label"""
        return (element.find('a') is not None or 
                element.name == 'a' or 
                (element.name == 'label' and element.get('for') is not None))

    def get_deepest_elements_with_links(form):
        elements = []
        processed = set()
        
        for element in form.find_all(['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'label', 'aside']):
            if any(parent in processed for parent in element.parents):
                continue
                
            if element.get_text(strip=False):  # 如果元素包含任何非空文本
                elements.append(element)
                processed.add(element)
                
        return elements

    forms = []
    for form in soup.find_all('form'):
        if form.find('input') is not None:
            form_details = {
                'id': form.get('id', ''),
                'method': form.get('method', ''),
                'action': form.get('action', ''),
                'fields': [],
                'text_content': [],
                'surrounding_text': []
            }
            
            if 'search' in form_details['id'].lower():
                continue
            is_search_form = False
            # 处理表单字段（包括按钮）
            for field in form.find_all(['input', 'textarea', 'select', 'button']):
                field_type = field.get('type','').lower()
                
                if field_type in ['hidden']:
                    continue
                    
                field_info = {
                    'tag': field.name,
                    'name': field.get('name', ''),
                    'type': field_type,
                    'id': field.get('id', ''),
                    'placeholder': field.get('placeholder', ''),
                    'required': field.has_attr('required'),
                    'class': field.get('class', []),
                    'disabled': field.has_attr('disabled')
                }
                
                # Enhanced label handling for checkboxes
                if field_type in ['checkbox', 'radio', 'option', 'select']:
                    # Try to find label by 'for' attribute
                    if field.get('id') is None or field.get('id') == '':
                        label = field.find_parent('label')
                    else:
                        label = soup.find('label', {'for': field.get('id')})
                    
                    # If no label found by 'for', check if input is inside a label
                    # if not label or label.text.strip() == '':
                    #     label = field.find_parent('label')
                    
                    if label:
                        texts = []
                        for content in label.descendants:
                            if isinstance(content, str):
                                texts.append(content.strip())
                            elif content.name == 'a':
                                link_text = content.get_text(strip=True)
                                texts.append(link_text)
                        
                        field_info['label_text'] = ' '.join(texts)
                    else:
                        # If no label, check for text in sibling elements
                        sibling_texts = []
                        for sibling in field.find_next_siblings():
                            if sibling.name in ['span', 'font']:
                                sibling_texts.extend(sibling.stripped_strings)
                        field_info['label_text'] = ' '.join(sibling_texts)

                if 'search' in field_info['name'].lower():
                    is_search_form = True
                    continue
                # 获取按钮文本
                if field.name == 'button' or field_type in ['submit', 'button']:
                    field_info['text'] = field.text.strip() if field.text.strip() else field.get('value', '')
                
                # Get label if it exists - only search by 'for' if id is present
                if field.get('id') !='' and field.get('id') is not None:
                    # First try to find label by 'for' attribute
                    label = soup.find('label', {'for': field.get('id')})
                    if not label:
                        # If no label found by 'for', check if input is inside a label
                        label = field.find_parent('label')
                        # If still no label, look for the closest preceding label in DOM order
                        if not label:
                            current = field
                            while current.previous_element:
                                if hasattr(current.previous_element, 'name') and current.previous_element.name == 'label':
                                    label = current.previous_element
                                    break
                                current = current.previous_element
                    
                    field_info['label'] = label.text.strip().replace('\n', ' ').replace('  ', ' ') if label else ''
                else:
                    field_info['label'] = ''
                form_details['fields'].append(field_info)

            if is_search_form:
                continue
            # 处理表单内的文本内容
            processed_texts = []
            for text_element in get_deepest_elements_with_links(form):
                text = get_full_sentence(text_element)
                
                if text and text not in processed_texts:
                    # processed_texts.add(text.strip())
                    all_texts = []
                    for _ in text:
                        tmp_text = _.strip().split("\n")
                        for tmp_tmp_text in tmp_text:
                            if tmp_tmp_text.strip() == '':
                                continue
                            all_texts.append(tmp_tmp_text)
                    
                    form_details['text_content'].append({
                        'tag': text_element.name,
                        'text': all_texts,
                        'class': text_element.get('class', [])
                    })

            # Modified code: Only extract siblings if parent is a div
            if form.parent and form.parent.name == 'div':
                for sibling in form.parent.children:
                    if sibling == form:  # Skip the form itself
                        continue
                    
                    if isinstance(sibling, str):
                        text = sibling.strip()
                        if text:
                            form_details['surrounding_text'].append({
                                "position": "parent_content",
                                "tag": "text",
                                "text": [text]
                            })
                    elif hasattr(sibling, 'name'):
                        # Process elements like headings, paragraphs, links, etc.
                        if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'a', 'span', 'font', 'aside']:
                            if should_extract_full_sentence(sibling):
                                text = get_full_sentence(sibling)
                            else:
                                text = [t.strip() for t in sibling.stripped_strings if t.strip()]
                            
                            if text:
                                form_details['surrounding_text'].append({
                                    "position": "parent_content",
                                    "tag": sibling.name,
                                    "text": text,
                                    "class": sibling.get('class', [])
                                })

            forms.append(form_details)
    
    return forms


def delete_search_form(form_info):
    filtered_forms = []
    for form in form_info:
        is_search_form = False
        
        # 检查表单级别的搜索标识
        if ('search' in (form['id'] or '').lower() or 
            'search' in (form['method'] or '').lower() or 
            'search' in (form['action'] or '').lower()):
            is_search_form = True
            
        # 检查所有字段是否包含搜索相关标识
        for field in form['fields']:
            if ('search' in (field['id'] or '').lower() or 
                'search' in (field['name'] or '').lower() or 
                'search' in (field['placeholder'] or '').lower() or 
                'search' in (field['type'] or '').lower() or 
                'search' in ' '.join(field['class']).lower() or
                'search' in (field['label'] or '').lower()):
                is_search_form = True
                break
        
        if not is_search_form:
            filtered_forms.append(form)
            
    return filtered_forms

def delete_cookie_form(form_info):
    filtered_forms = []
    for form in form_info:
        is_cookie_form = False
        if ('cookie' in (form['id'] or '').lower() or 
            'cookie' in (form['method'] or '').lower() or 
            'cookie' in (form['action'] or '').lower()):
            is_cookie_form = True
        for field in form['fields']:
            if ('cookie' in (field['id'] or '').lower() or 
                'cookie' in (field['name'] or '').lower() or 
                'cookie' in (field['placeholder'] or '').lower() or 
                'cookie' in (field['type'] or '').lower()):
                is_cookie_form = True
                break
        if not is_cookie_form:
            filtered_forms.append(form)
    return filtered_forms

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--websites_folder', type=str, default='38degrees_org_uk')
    return parser.parse_args()

result_folder = "/home/ying/projects/web_navigation/webarena/results_test"
websites_folder = os.listdir(result_folder)
# args = arg_parse()
# websites_folder = [args.websites_folder]
# websites_folder = ['www_hitachivantara_com']
# websites_folder = ['5g_nttdata_com']
for website_folder in tqdm(websites_folder, total=len(websites_folder)):
    folder_files = os.listdir(os.path.join(result_folder, website_folder))
    iframe_files = [file for file in folder_files if file.startswith('iframe_pkl') and file.endswith('.json') and not file.endswith('_form.json')]
    overall_pkl = os.path.join(result_folder, website_folder, 'overall.pkl')
    if not os.path.exists(overall_pkl):
        continue
    pkl_data = pickle.load(open(overall_pkl, 'rb'))
    for idx, _ in enumerate(pkl_data):
        html = _['html']
        image = _['image']
        image = Image.fromarray(image)
        image_bytes = image.tobytes()
        image_hash = hashlib.md5(image_bytes).hexdigest()
        iframe = _['iframes']
        forms = []
        for each in iframe:
            form_info = extract_forms_with_iframe(each['frame_content'])
            forms.extend(form_info)
        forms.extend(extract_forms_with_input(html))
        form_dict = {}
        form_dict['forms'] = delete_search_form(delete_cookie_form(deduplicate_forms(forms)))
        form_dict['url'] = _['url']
        form_dict['image'] = image_hash
        directory = os.path.join(result_folder, website_folder, 'form_info')
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, f'form_{idx}.json'), 'w') as f:
            json.dump(form_dict, f, ensure_ascii=False)
        
    
    # if len(iframe_files) == 0:
    #     for idx, _ in enumerate(pkl_data):
    #         form_dict = {}
    #         # print(_['iframes'][0].keys())
    #         # try:
    #         #     html = _['iframes'][0]['frame_content']
    #         # except:
    #         #     continue

    #         html = _['html']
    #         image = _['image']
    #         image = Image.fromarray(image)
    #         image_bytes = image.tobytes()
    #         image_hash = hashlib.md5(image_bytes).hexdigest()
    #         # form_info = extract_forms_with_iframe(html)
    #         form_info = extract_forms_with_input(html)
    #         # form_dict['image'] = hash
    #         form_dict['forms'] = form_info
    #         form_dict['url'] = _['url']
    #         form_dict['image'] = image_hash
    #         directory = os.path.join(result_folder, website_folder, 'form_info')
            
    #         os.makedirs(directory, exist_ok=True)
    #         with open(os.path.join(directory, f'form_{idx}.json'), 'w') as f:
    #             form_dict['forms'] = delete_search_form(deduplicate_forms(form_info))

    #             print(form_dict['forms'])
    #             json.dump(form_dict, f, ensure_ascii=False)
    #     # print(form_info)
    # # if len(iframe_files) == 0:
    # #     continue
    # else:
    #     final_idx = 0
    #     for idx, each in enumerate(iframe_files):
    #         with open(os.path.join(result_folder, website_folder, each), 'r') as f:
    #             iframe_dict = json.load(f)
    #         form_dict = {}
    #         form_info = extract_forms_with_iframe(iframe_dict['frame_content'])
    #         form_dict['forms'] = form_info
    #         form_dict['url']  = iframe_dict['url']
    #         directory = os.path.join(result_folder, website_folder, 'form_info')
    #         os.makedirs(directory, exist_ok=True)
    #         with open(os.path.join(directory, f'form_{idx}.json'), 'w') as f:
    #             form_dict['forms'] = delete_search_form(deduplicate_forms(form_info))
    #             final_idx += 1
                
   
       