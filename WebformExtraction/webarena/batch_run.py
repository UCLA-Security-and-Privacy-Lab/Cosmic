import os
import subprocess

configure_dir = "./config" # replace with the path to the configure folder (e.g., ./config) 

configure_dirs = os.listdir(configure_dir)
# print(configure_dirs)
for sub_dir in configure_dirs:
    print(sub_dir)
    config_path = os.path.join(sub_dir)
    subprocess.run(["./pipeline_run.sh", "-c", config_path])