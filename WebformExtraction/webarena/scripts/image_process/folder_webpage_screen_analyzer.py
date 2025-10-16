import os
import subprocess
from tqdm import tqdm
result_folder = "/home/ying/projects/web_navigation/webarena/results_test"
websites_folder = os.listdir(result_folder)

for website_folder in tqdm(websites_folder, total=len(websites_folder)):
    website_path = os.path.join(result_folder, website_folder)
    if 'segmented_images' in os.listdir(website_path):
        image_folders = os.path.join(website_path, 'segmented_images')
        if 'answer_dict.json' in os.listdir(image_folders):
            continue
        subprocess.run(['python', 'webpage_screenshot_analyzer.py', '--input_folder', image_folders])
        # for segmented_folder in os.listdir(image_folders):
        #     if 'answer_dict.json' in os.listdir(os.path.join(image_folders, segmented_folder)):
        #         continue
        #     image_folder = os.path.join(image_folders, segmented_folder)
        #     print(image_folder)
        #     subprocess.run(['python', 'webpage_screenshot_analyzer.py', '--input_folder', image_folder])

