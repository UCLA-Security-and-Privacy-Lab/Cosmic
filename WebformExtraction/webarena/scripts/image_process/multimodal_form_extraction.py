from pathlib import Path
import openai
from openai import OpenAI
import requests
from tqdm import tqdm
from argparse import ArgumentParser
import pickle
from PIL import Image
import io
import base64
import sys
import json
import os
import hashlib
from urllib.parse import urlparse
import tldextract


sys.path.append("/home/ying/projects/web_navigation/webarena")

SYSTEM_MSG = '''
You are a website form analyzer. When provided with a screenshot of a website, analyze all the forms in the website and provide the output in the following JSON format without any redundant description. Pay special attention to any icons present on the elements and include them in the output. The keys you need to specify in the output JSON:

Element_Type should be one of the following: ["STATIC_TEXT", "textbox", "button", "checkbox", "combobox", "toggle", "option"].
Element_Text: the visible text of the element. Note all the text on the form should be extracted, not only the text on web elements of the form!
Element_Status: the state of the element (e.g., "active", "empty", "filled", "selected", "checked", "unchecked").
Element_Value: the value of the element if applicable (e.g., the input in a textbox, the selected option in a combobox).
icon: describes the icon on the button of a form if present. If no icon is present, just leave "".

The JSON format should follow:
{
"Form1": [
{"Element_Type": "STATIC_TEXT", "Element_Text": "Text of the static text element", "Element_Status": "active"},
{"Element_Type": "textbox", "Element_Text": "Text of the textbox element", "Element_Status": "empty/filled", "Element_Value": "Value if filled"},
{"Element_Type": "combobox", "Element_Text": "Text of the combobox element", "Element_Status": "empty/selected", "Element_Value": "Value if selected"},
{"Element_Type": "checkbox", "Element_Text": "Text of the checkbox element", "Element_Status": "checked/unchecked"},
{"Element_Type": "button", "Element_Text": "Text of the button element", "Element_Status": "active", "icon": "the icon name of the icon"}
...
]
}

Here is an example:
{
"Form1": [
{"Element_Type": "STATIC_TEXT", "Element_Text": "Subscribe to Snippets", "Element_Status": "active"},
{"Element_Type": "STATIC_TEXT", "Element_Text": "Keep up in a fast-moving industry with relevant, bite-sized insights.", "Element_Status": "active"},
{"Element_Type": "textbox", "Element_Text": "Email address", "Element_Status": "empty"},
{"Element_Type": "button", "Element_Text": "", "Element_Status": "active", "icon": "Arrow"},
{"Element_Type": "STATIC_TEXT", "Element_Text": "By clicking the arrow above, you agree to the processing of your personal data by Transcend as described in our Data Practices and Privacy Policy. You can unsubscribe at any time.", "Element_Status": "active"}
],
"Form2": [...]
}

'''


SYSTEM_MSG = '''
You are a website form analyzer. When provided with a screenshot of a website, analyze all the forms that needs user interaction in the website and provide the output in the following JSON format without any redundant description. Pay special attention to any icons present on the elements and include them in the output. Also, ensure to relate checkboxes or other elements to their relevant instructions or descriptions. Search boxes should not be considered. The keys you need to specify in the output JSON: 

Element_Type should be one of the following: ["STATIC_TEXT", "textbox", "button", "checkbox", "combobox", "toggle"]. 

Element_Text: the visible text of the element. Note all the text on the form should be extracted, not only the text on web elements of the form! 

Element_Status: the state of the element (e.g., "active", "empty", "filled", "selected", "checked", "unchecked"). 

Element_Value: the value of the element if applicable (e.g., the input in a textbox, the selected option in a combobox). 


The JSON format should follow: 
{ "Form1": [ 
{"Element_Type": "STATIC_TEXT", "Element_Text": "Text of the static text element"}, 
{"Element_Type": "textbox", "Element_Text": "Text of the textbox element", "Element_Status": "empty/filled", "Element_Value": "Value if filled"}, 
{"Element_Type": "combobox", "Element_Text": "Text of the combobox element", "Element_Status": "empty/selected", "Element_Value": "Value if selected"}, 
{"Element_Type": "checkbox", "Element_Text": "Text of the checkbox element", "Element_Status": "checked/unchecked"}, 
{"Element_Type": "button", "Element_Text": "Text of the button element", "Element_Status": "active", "icon": "the icon name of the icon"} ... ] }
'''


def get_payload(base64_image):
    payload = {
      "model": "gpt-4o-mini",
      "messages": [
          {"role": "system", "content": SYSTEM_MSG},
        {
          "role": "user",
          "content": [
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/png;base64,{base64_image}"
              }
            }
          ]
        }
      ],
      "temperature": 0.3,
      "max_tokens": 4096
    }
    return payload


client = OpenAI(api_key="xxxxx")

HEADERS = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer xxxxx"
}


def image_to_base64(image_array):
    # If image_array is already a PIL Image object
    if isinstance(image_array, Image.Image):
        image = image_array
    else:
        # If it's a numpy array, convert to PIL Image
        image = Image.fromarray(image_array)
        
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    img_str = base64.b64encode(buffer.read()).decode('utf-8')
    return img_str 

def is_same_main_domain(url1, url2):
    ext1 = tldextract.extract(url1)
    ext2 = tldextract.extract(url2)
    
    return (ext1.domain == ext2.domain) and (ext1.suffix == ext2.suffix)


def get_return_res(image_array):
    base64_image = image_to_base64(image_array)
    payload = get_payload(base64_image=base64_image)
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=payload)
    response_ori = response.json()
    try:
      return_res = response_ori['choices'][0]['message']['content'].replace('```json\n','').replace('```','')
    except Exception as e:
      print(e)
      print(response_ori)
      return {}
    try:
      return_res = json.loads(return_res)
    except:
      print(return_res)
    return return_res

def write2json(data, file):
    with open(file, 'w') as f:
        json.dump(data,f, ensure_ascii=False)
    f.close()

def write2pkl(data, file):
   with open(file, 'wb') as f:
        pickle.dump(data, f)

def get_pkl_with_form(result_folder):
    trace_file_name = "overall.pkl"
    with open(os.path.join(result_folder, trace_file_name), 'rb') as file:
      loaded_trajectory = pickle.load(file)
    file_name = os.path.basename(result_folder)
    base_url = file_name.replace("_",".")
    # try:
    #   base_url = loaded_trajectory[0]['url']
    # except:
    #   return []
    final_results = []
    for idx, each in enumerate(tqdm(loaded_trajectory)):
      url = each['url']
      if "github" in url or "gitlab" in url or "youtube" in url or "google" in url:
          continue
      # if not is_same_main_domain(url, base_url):
      #     continue
      image_array = each['image']
      result = get_return_res(image_array)
      # try:
        
      # except:
      #   print(result_folder, idx)
      #   result = {}
      each['index'] = idx
      each['result'] = result
      final_results.append(each)
      # print(result)
    return final_results


def save_image(image_array, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    image = Image.fromarray(image_array)
    image_bytes = image.tobytes()
    hash_md5 = hashlib.md5(image_bytes).hexdigest()
    image.save(f"{save_dir}/{hash_md5}.png")
    return hash_md5

def url_and_form(trajectory_with_form, result_dir):
    ret_list = []
    for each in tqdm(trajectory_with_form):
        tmp_dict = {}
        tmp_dict['url'] = each['url']
        tmp_dict['result'] = each['result']
        image_array = each['image']
        md5 = save_image(image_array, os.path.join(result_dir, 'images'))
        tmp_dict['image'] = md5
        # tmp_dict['file'] = each['file']
        tmp_dict['index'] = each['index']
        ret_list.append(tmp_dict)
    return ret_list

def is_file_in_folder(filename, folder_path):
    """Check if a file with a given name exists in a folder or its subfolders."""
    # Walk through the directory tree
    for root, dirs, files in os.walk(folder_path):
        if filename in files:
            return True
    return False


if __name__ == "__main__":
   RESULTS_DIR = "/home/ying/projects/web_navigation/webarena/results_test"
   websites_folder = os.listdir(RESULTS_DIR)
  #  websites_folder = ['zupee_com']
   for website_folder in tqdm(websites_folder):
      website_path = os.path.join(RESULTS_DIR, website_folder)
      if 'merged_images' in os.listdir(website_path):
          image_folders = os.path.join(website_path, 'merged_images')
          for image_folder in os.listdir(image_folders):
            image_folder_path = os.path.join(image_folders, image_folder)
            images = [_ for _ in os.listdir(image_folder_path) if _.endswith('.png')]
            for image in images:
              save_path = os.path.join(image_folder_path, f'form_{image.split(".")[0].split("_")[1]}.json')
              
              if os.path.exists(save_path):
                continue
              image_path = os.path.join(image_folder_path, image)
              img = Image.open(image_path)
              res = get_return_res(img)
              with open(os.path.join(image_folder_path, f'form_{image.split(".")[0].split("_")[1]}.json'), 'w') as f:
                json.dump(res, f, ensure_ascii=False)
              print(save_path)
              # print(res)
              # exit()
         
    # parser = ArgumentParser(description="Process result folder path.")
    # parser.add_argument("result_folder", type=str, help="Path to the result folder")
    # args = parser.parse_args()

    # result_folder = args.result_folder
    # # dirs = os.listdir(result_parent_folder)
    # if is_file_in_folder('overall.pkl', result_folder):
    #   loaded_trajectory = get_pkl_with_form(result_folder)
    #   write2pkl(loaded_trajectory, os.path.join(result_folder, 'overall2.pkl'))
    #   results = url_and_form(loaded_trajectory, result_folder)
    #   # print(len(results))
    #   write2json(results, os.path.join(result_folder, 'overall.json'))

    # result_parent_folder = "/home/ying/projects/web_navigation/webarena/result_folders2"
    # dirs = os.listdir(result_parent_folder)

    # dirs = ['digitalspy_com']

# for subdir in tqdm(dirs):
#   # result_folder = os.path.join(result_parent_folder,subdir)
#   result_folder = "/home/ying/projects/web_navigation/webarena/results_2"
#   if not is_file_in_folder('overall.pkl', result_folder):
#       print(subdir)
#       continue
#   # if is_file_in_folder('overall.json', result_folder):
#   #     continue
#   loaded_trajectory = get_pkl_with_form(result_folder)
#   write2pkl(loaded_trajectory, os.path.join(result_folder, 'overall2.pkl'))
#   results = url_and_form(loaded_trajectory, result_folder)
#   # print(len(results))
#   write2json(results, os.path.join(result_folder, 'overall.json'))


