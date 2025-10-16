from PIL import Image
import numpy as np
import os
import json
def extract_continuous_images(answer_dict):
    
    sorted_items = sorted(answer_dict.items(), 
                         key=lambda x: int(x[0].split('_')[1].split('.')[0]))
    
    continuous_groups = []
    current_group = []
    
    for filename, info in sorted_items:
        if info['answer'] == 'Y':
            current_group.append(filename)
        else:
            if len(current_group) >= 1:  # 
                continuous_groups.append(current_group)
            current_group = []
    
    
    if len(current_group) >= 1:
        continuous_groups.append(current_group)
    
    return continuous_groups

def merge_continuous_images(image_groups, image_dir):
    merged_results = []
    
    for group in image_groups:
        images = []
        for img_name in group:
            img_path = os.path.join(image_dir, img_name)
            img = Image.open(img_path)
            images.append(img)
            
        if len(images) == 1:
            # 如果只有一张图片，直接添加
            merged_results.append(images[0])
        else:
            # 多张图片需要合并
            total_height = sum(img.height for img in images)
            max_width = max(img.width for img in images)
            
            merged_img = Image.new('RGB', (max_width, total_height))
            
            y_offset = 0
            for img in images:
                merged_img.paste(img, (0, y_offset))
                y_offset += img.height
            
            merged_results.append(merged_img)
    
    return merged_results

results_folder = "/home/ying/projects/web_navigation/webarena/results_test"
websites_folder = os.listdir(results_folder)
# websites_folder = ['e-volution_ai']
for website_folder in websites_folder:
    website_path = os.path.join(results_folder, website_folder)
    if 'segmented_images' in os.listdir(website_path):
        segmented_images_path = os.path.join(website_path, 'segmented_images')
        for segmented_image_folder in os.listdir(segmented_images_path):
            if 'answer_dict.json' in os.listdir(os.path.join(segmented_images_path, segmented_image_folder)):
                answer_dict = json.load(open(os.path.join(segmented_images_path, segmented_image_folder, 'answer_dict.json'), 'r'))
                image_groups = extract_continuous_images(answer_dict)
                merged_images = merge_continuous_images(image_groups, os.path.join(segmented_images_path, segmented_image_folder))
                merged_images_path = os.path.join(website_path, 'merged_images', segmented_image_folder)
                print(merged_images_path)
                os.makedirs(merged_images_path, exist_ok=True)
                for i, merged_image in enumerate(merged_images):
                    merged_image.save(os.path.join(merged_images_path, f'merged_{i}.png'))
