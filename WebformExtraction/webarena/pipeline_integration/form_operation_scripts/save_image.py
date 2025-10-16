from PIL import Image
import os
import hashlib
import pickle
from tqdm import tqdm
def save_image(image_array, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    image = Image.fromarray(image_array)
    image_bytes = image.tobytes()
    hash_md5 = hashlib.md5(image_bytes).hexdigest()
    image.save(f"{save_dir}/{hash_md5}.png")
    return hash_md5

def load_pkl(pkl_path):
    with open(pkl_path, "rb") as f:
        return pickle.load(f)

if __name__ == "__main__":
    result_folder = "/home/ying/projects/web_navigation/webarena/results_test"
    website_folders = os.listdir(result_folder)
    for website_folder in tqdm(website_folders, total=len(website_folders)):
        website_folder_path = os.path.join(result_folder, website_folder)
        if os.path.isdir(website_folder_path):
            image_pkl_path = os.path.join(website_folder_path, "overall.pkl")
            if not os.path.exists(image_pkl_path):
                continue
            pkl_data = load_pkl(image_pkl_path)
            for each in pkl_data:
                image_array = each['image']
                save_dir = os.path.join(website_folder_path, "images")
                if os.path.exists(save_dir):
                    continue
                # print(save_dir)
                # if os.path.exists(save_dir):
                #     continue
                # else:
            #     os.makedirs(save_dir)
                save_image(image_array, save_dir)
