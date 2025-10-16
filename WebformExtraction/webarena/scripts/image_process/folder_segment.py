import os
import subprocess
from tqdm import tqdm
result_folder = "/home/ying/projects/web_navigation/webarena/results_test"
websites_folder = os.listdir(result_folder)

for website_folder in tqdm(websites_folder, total=len(websites_folder)):
    website_path = os.path.join(result_folder, website_folder)
    if 'images' in os.listdir(website_path):
        image_folder = os.path.join(website_path, 'images')
        subprocess.run(['python', 'segment.py', '--input_folder', image_folder])

