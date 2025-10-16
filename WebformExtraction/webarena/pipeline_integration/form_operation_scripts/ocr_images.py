# import subprocess
# import os
# import json
# from tqdm import tqdm

# def read_json(json_path):
#     return json.load(open(json_path, "r"))

# def get_ocr_result(folder_path):
#     answer_dict = read_json(os.path.join(folder_path, "answer_dict.json"))
#     for image_file, answer in answer_dict.items():
#         # print(answer)
#         if answer['answer'] == "Y":
#             image_path = os.path.join(folder_path, image_file)
#             saved_ocr_path = os.path.join(folder_path, "ocr_images")
#             # print(saved_ocr_path)
#             if not os.path.exists(saved_ocr_path):
#                 os.makedirs(saved_ocr_path)
#             saved_ocr_file = os.path.join(saved_ocr_path, image_file.split(".")[0] + ".txt")
#             print(saved_ocr_file)
#             subprocess.run(["tesseract", image_path, saved_ocr_file])
#             # print(image_path)

# result_path = "/home/ying/projects/web_navigation/webarena/results_test"
# websites = os.listdir(result_path)
# for website in tqdm(websites, total=len(websites)):
#     website_path = os.path.join(result_path, website, "segmented_images")
#     segmented_folders = os.listdir(website_path)
#     for segmented_folder in segmented_folders:
#         segmented_folder_path = os.path.join(website_path, segmented_folder)
#         get_ocr_result(segmented_folder_path)
        # print(segmented_folder_path)
        # if os.path.isdir(segmented_folder_path):
        #     get_ocr_result(segmented_folder_path)
