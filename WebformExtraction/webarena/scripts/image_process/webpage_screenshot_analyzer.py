import base64
import requests
import os
from typing import Optional
import json
from tqdm import tqdm
import argparse
class WebpageScreenshotAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = HEADERS = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer xxxxx"
        }

    def encode_image(self, image_path: str) -> str:
        """Convert image to base64 encoding."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_screenshot(self, image_path: str) -> Optional[dict]:
        """
        Analyze a screenshot using GPT-4-Vision to detect web forms.
        
        Args:
            image_path (str): Path to the screenshot image
            
        Returns:
            dict: Analysis results including whether a form was detected
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        base64_image = self.encode_image(image_path)
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that analyzes web page screenshots to determine if they contain any web forms."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this webpage screenshot and determine if it contains any web forms. "
                                  "A web form typically includes elements like input fields, text areas, "
                                  'checkboxes, radio buttons, or submit buttons. Please provide a Y/N answer and answer in JSON format: { "answer": "Y/N" }'
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.6
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "analysis": result["choices"][0]["message"]["content"]
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

def write_answer_dict(answer_dict, file_path):
    with open(file_path, 'w') as f:
        json.dump(answer_dict, f)       

def parse_args():
    parser = argparse.ArgumentParser(description='Analyze webpage screenshots to determine if they contain any web forms.')
    parser.add_argument('--input_folder', type=str, required=True, help='Path to the folder containing input images')
    return parser.parse_args()


def main():
    # Example usage
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")

    analyzer = WebpageScreenshotAnalyzer(api_key)
    args = parse_args()
    input_folder = args.input_folder

    for dir_name in os.listdir(input_folder):
        dir_path = os.path.join(input_folder, dir_name)
        if not os.path.isdir(dir_path):
            continue

        image_files= os.listdir(dir_path)
        answer_dict = {}
        try:
            answer_dict = json.load(open(os.path.join(dir_path, "answer_dict.json"), "r"))
            if len(answer_dict) > 0:
                continue
        except:
            pass
        for image_file in tqdm(image_files, desc=f"Processing {dir_name}"):
            image_path = os.path.join(dir_path, image_file)
            # print(image_path)
            if not image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            # if 'answer_dict.json' in os.listdir(dir_path) and len(json.load(open(os.path.join(dir_path, "answer_dict.json"), "r"))) > 0:
            #     continue
            try:
                result = analyzer.analyze_screenshot(image_path)
                if result["success"]:
                    answer_dict[image_file] = json.loads(result["analysis"].replace("```json", "").replace("```", ""))
                else:
                    print(f"Error processing {image_file}: {result['error']}")
            except Exception as e:
                # exit()
                print(f"An error occurred processing {image_file}: {str(e)}")
                answer_dict[image_file] = {"answer": "unknown"}
                exit()
        output_path = os.path.join(dir_path, "answer_dict.json")
        write_answer_dict(answer_dict, output_path)
        # print(f"Results written to {output_path}")

if __name__ == "__main__":
    main()
