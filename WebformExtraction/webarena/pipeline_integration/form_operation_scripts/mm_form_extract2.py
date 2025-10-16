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


# SYSTEM_MSG = '''
# You are a website form analyzer. When provided with a screenshot of a website, analyze all the forms that needs user interaction in the website and provide the output in the following JSON format without any redundant description. Pay special attention to any icons present on the elements and include them in the output. Also, ensure to relate checkboxes or other elements to their relevant instructions or descriptions. Search boxes should not be considered. The keys you need to specify in the output JSON: 

# Element_Type should be one of the following: ["STATIC_TEXT", "textbox", "button", "checkbox", "combobox", "toggle"]. 

# Element_Text: the visible text of the element. Note all the text on the form should be extracted, not only the text on web elements of the form! 

# Element_Status: the state of the element (e.g., "active", "empty", "filled", "selected", "checked", "unchecked"). 

# Element_Value: the value of the element if applicable (e.g., the input in a textbox, the selected option in a combobox). 


# The JSON format should follow: 
# { "Form1": [ 
# {"Element_Type": "STATIC_TEXT", "Element_Text": "Text of the static text element"}, 
# {"Element_Type": "textbox", "Element_Text": "Text of the textbox element", "Element_Status": "empty/filled", "Element_Value": "Value if filled"}, 
# {"Element_Type": "combobox", "Element_Text": "Text of the combobox element", "Element_Status": "empty/selected", "Element_Value": "Value if selected"}, 
# {"Element_Type": "checkbox", "Element_Text": "Text of the checkbox element", "Element_Status": "checked/unchecked"}, 
# {"Element_Type": "button", "Element_Text": "Text of the button element", "Element_Status": "active", "icon": "the icon name of the icon"} ... ] }
# '''


def get_payload(base64_image):
    payload = {
      "model": "gpt-4o-2024-05-13",
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
      "temperature": 0.6,
      "max_tokens": 4096
    }
    return payload


client = OpenAI(api_key="sk-proj-xxxxxxx")

HEADERS = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer sk-proj-xxxxxxx"
}


def image_to_base64(image_array):
    image = Image.fromarray(image_array)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    img_str = base64.b64encode(buffer.read()).decode('utf-8')
    return img_str
def file_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        img_str = base64.b64encode(image_file.read()).decode('utf-8')
    return img_str
def get_return_res(image_path):
    base64_image = file_to_base64(image_path)
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


if __name__ == "__main__":
    result_folders = "/home/ying/projects/web_navigation/webarena/results_test/"
    website_folders = os.listdir(result_folders)
    cnt = 0
    for each_folder in website_folders:
        each_folder_path = os.path.join(result_folders, each_folder)
        segmented_images_path = os.path.join(each_folder_path, "segmented_images")
        for each_segmented_image in os.listdir(segmented_images_path):
            each_segmented_image_path = os.path.join(segmented_images_path, each_segmented_image)
            data = json.load(open(os.path.join(each_segmented_image_path, "answer_dict.json"), "r"))
            # print(data)
            
            if len(data) == 0:
                print(each_segmented_image_path)
                cnt+=1
            else:
                continue
        # if os.path.isdir(each_folder_path):
        #     image_path = os.path.join(each_folder_path, "images")
        #     print(image_path)
    # image_path = ""
    # print(get_return_res(image_path))
    print(cnt)