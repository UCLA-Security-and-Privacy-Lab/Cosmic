import os
import subprocess
from tqdm import tqdm
result_folder = "/home/ying/projects/web_navigation/webarena/results_test"
websites_folder = os.listdir(result_folder)

for website_folder in tqdm(websites_folder, total=len(websites_folder)):
    if 'overall.pkl' in os.listdir(os.path.join(result_folder, website_folder)):
        continue
    subprocess.run(['python', 'select_same_page_structure.py', '--folder', os.path.join(result_folder, website_folder)])

