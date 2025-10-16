import json
import os
from tqdm import tqdm
def merge_forms(folder_path):
    merged_forms = {}
    seen_forms = set()  # To track unique forms
    idx = 0
    
    for file in os.listdir(folder_path):
        if file.endswith('.json') and file.startswith('form_'):
            with open(os.path.join(folder_path, file), 'r') as f:
                forms = json.load(f)
                for key, value in forms.items():
                    # Create a tuple of (element_type, text) pairs for comparison
                    form_signature = tuple(
                        (element.get('Element_Type', ''), element.get('Element_Text', ''))
                        for element in value
                    )
                    # print(form_signature)
                    # Only add the form if we haven't seen this signature before
                    if form_signature not in seen_forms:
                        merged_forms[f"Form{idx+1}"] = value
                        seen_forms.add(form_signature)
                        idx += 1
    
    return merged_forms

if __name__ == "__main__":
    RESULTS_FOLDER = "/home/ying/projects/web_navigation/webarena/results_test"
    website_folder = os.listdir(RESULTS_FOLDER)
    # website_folder = ["www_metrixlab_com"]
    for website in tqdm(website_folder):
        merged_image_folder = os.path.join(RESULTS_FOLDER, website, "merged_images")
        if not os.path.exists(merged_image_folder):
            continue
        for image in os.listdir(merged_image_folder):
            image_folder = os.path.join(merged_image_folder, image)
            # print(image_folder)
            try:
                merged_forms = merge_forms(image_folder)
                # print(merged_forms)
            except:
                with open('error_merge_forms.txt', 'a') as f:
                    f.write(image_folder + '\n')
            with open(os.path.join(image_folder, 'merged_forms.json'), 'w') as f:
                json.dump(merged_forms, f)