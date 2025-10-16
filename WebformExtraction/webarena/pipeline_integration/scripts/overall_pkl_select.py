import os
import subprocess
from tqdm import tqdm
import shutil
RESULT_FOLDER = "/home/ying/projects/web_navigation/webarena/results_test"

def is_file_in_folder(filename, folder_path):
    """Check if a file with a given name exists in a folder or its subfolders."""
    # Walk through the directory tree
    for root, dirs, files in os.walk(folder_path):
        if filename in files:
            return True
    return False


dirs = os.listdir(RESULT_FOLDER)
# dirs = ['digitalspy_com']
error_dirs = []
no_pkl_dirs = []
for dir_ in tqdm(dirs):
    dir_path = os.path.join(RESULT_FOLDER, dir_)
    # dir_path = "/home/ying/projects/web_navigation/webarena/results_2"
    # if is_file_in_folder("overall.pkl",dir_path):
    #     continue
    if os.path.exists(os.path.join(dir_path, "overall.pkl")):
        # if the file is empty, append to no_pkl_dirs
        # if os.path.getsize(os.path.join(dir_path, "overall.pkl")) == 5:
        #     cmd = f"python select_same_page_structure.py --folder {dir_path}"
        #     print(cmd)
        #     result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        #     print(result.stdout)
        #     print(result.stderr)
        #     if len(result.stderr) > 10:
        #         print(result.stderr)
        #         exit()
        #     no_pkl_dirs.append(dir_path)
        continue

    # if not os.path.exists(os.path.join(dir_path, "trajectory_0.json.pkl")):
    #     no_pkl_dirs.append(dir_path)
    #     # delete the directory and all its contents
    #     # shutil.rmtree(dir_path)
    #     continue
    if os.path.exists(os.path.join(dir_path, "trajectory_0.json.pkl")):
        cmd = f"python select_same_page_structure.py --folder {dir_path}"
        print(cmd)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print("Standard Output:")
        print(result.stdout)

    # print error output
        print("Error Output:")
        print(result.stderr)
        if len(result.stderr) > 10:
            exit()
    #     error_dirs.append(dir_path)
        # error_dirs.append(dir_path)
# print(error_dirs)
# print(len(error_dirs))
print(no_pkl_dirs)
print(len(no_pkl_dirs))
    
    # else:
    #     print(dir_path)
        