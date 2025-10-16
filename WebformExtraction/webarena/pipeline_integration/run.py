
import argparse
import os
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description='Extract links from navigation')   
    # parser.add_argument('-u','--url', default='https://www.cabi.org/')
    parser.add_argument('--config_dir', type=str)
    parser.add_argument('--result_dir', type=str)
    return parser.parse_args()

def run(config_dir, result_dir):
    files = os.listdir(config_dir)
    files_cnt = len(files)
    command = f"python run.py --instruction_path agent/prompts/jsons/p_cot_id_actree_2s.json --test_start_idx 0 --test_end_idx {files_cnt-1} --config_folder {config_dir} --model gpt-4o --result_dir {result_dir}"
    subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

if __name__ == "__main__":
    args = parse_args()
    config_dir = args.config_dir
    result_dir = args.result_dir
    run(config_dir, result_dir)

    