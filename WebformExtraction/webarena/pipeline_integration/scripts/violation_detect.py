import os
import subprocess
from tqdm import tqdm
websites_folders = os.listdir("/home/ying/projects/web_navigation/webarena/results_test")
websites_folders = ["www_metrixlab_com"]
for each_website in tqdm(websites_folders):
    each_website_path = os.path.join("/home/ying/projects/web_navigation/webarena/results_test", each_website)
    
    all_facts_folder = os.path.join(each_website_path, "facts")
    results_folder = os.path.join(each_website_path, "results")
    if os.path.exists(all_facts_folder):
        os.makedirs(results_folder, exist_ok=True)
    else:
        continue
    facts_folders = os.listdir(os.path.join(each_website_path, "facts"))
    for fact_folder in facts_folders:
        fact_folder_path = os.path.join(each_website_path, "facts", fact_folder)
        results_facts_folder = os.path.join(results_folder, fact_folder)
        os.makedirs(results_facts_folder, exist_ok=True)
        # print(results_facts_folder)
        # switch to a path
        os.chdir("/home/ying/projects/web_navigation/consent_management/compliance_check/code/violation")
        cmd = ["souffle","-w", "-F", fact_folder_path, "-D", results_facts_folder, "violation_rules.datalog"]
        subprocess.run(cmd, check=True)
        print(results_facts_folder)