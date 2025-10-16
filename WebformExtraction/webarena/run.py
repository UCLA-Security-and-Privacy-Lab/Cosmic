"""Script to run end-to-end evaluation on the benchmark"""
import argparse
import glob
import json
import logging
import os
import random
import subprocess
import tempfile
import time
from pathlib import Path
from bs4 import BeautifulSoup
# from polyglot.detect import Detector
import openai
import os 

import numpy as np

import pickle
import re

os.environ[
    "SHOPPING"
] = "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:7770"
os.environ[
    "SHOPPING_ADMIN"
] = "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:7780/admin"
os.environ[
    "REDDIT"
] = "http://metis.lti.cs.cmu.edu:9999/"
os.environ[
    "GITLAB"
] = "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:8023"
os.environ[
    "MAP"
] = "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:3000"
os.environ[
    "misc"
] = "https://us.shein.com/"
os.environ[
    "WIKIPEDIA"
] = "http://ec2-3-131-244-37.us-east-2.compute.amazonaws.com:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing"
os.environ[
    "HOMEPAGE"
] = "PASS"


from agent import (
    Agent,
    PromptAgent,
    TeacherForcingAgent,
    construct_agent,
)
from agent.prompts import *
from browser_env import (
    Action,
    ActionTypes,
    ScriptBrowserEnv,
    StateInfo,
    Trajectory,
    create_stop_action,
)
from browser_env.actions import is_equivalent, create_goto_url_action, create_modal_close_action, create_id_based_action
from browser_env.auto_login import get_site_comb_from_filepath
from browser_env.helper_functions import (
    RenderHelper,
    get_action_description,
)
from evaluation_harness import evaluator_router

from help_scripts import process_accessibility_tree, get_close_id, extract_accessibility_label, select_unique_trees, url_process, get_visited_links,get_visited_links_this_folder

LOG_FOLDER = "log_files"
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)
LOG_FILE_NAME = f"{LOG_FOLDER}/log_{time.strftime('%Y%m%d%H%M%S', time.localtime())}_{random.randint(0, 10000)}.log"

logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(LOG_FILE_NAME)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# Set the log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
    
def config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run end-to-end evaluation on the benchmark"
    )
    parser.add_argument(
        "--render", action="store_true", help="Render the browser"
    )
    parser.add_argument(
        "--slow_mo",
        type=int,
        default=0,
        help="Slow down the browser by the specified amount",
    )
    parser.add_argument(
        "--action_set_tag", default="id_accessibility_tree", help="Action type"
    )
    parser.add_argument(
        "--observation_type",
        choices=["accessibility_tree", "html", "image"],
        default="accessibility_tree",
        help="Observation type",
    )
    parser.add_argument(
        "--current_viewport_only",
        action="store_true",
        help="Only use the current viewport for the observation",
    )
    parser.add_argument("--viewport_width", type=int, default=1280)
    parser.add_argument("--viewport_height", type=int, default=720)
    parser.add_argument("--save_trace_enabled", action="store_true")
    parser.add_argument("--sleep_after_execution", type=float, default=0.0)
    parser.add_argument("--max_steps", type=int, default=20)

    # agent config
    parser.add_argument("--agent_type", type=str, default="prompt")
    parser.add_argument(
        "--instruction_path",
        type=str,
        default="agents/prompts/state_action_agent.json",
    )
    parser.add_argument(
        "--parsing_failure_th",
        help="When concesecutive parsing failure exceeds this threshold, the agent will stop",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--repeating_action_failure_th",
        help="When concesecutive repeating action exceeds this threshold, the agent will stop",
        type=int,
        default=5,
    )

    # lm config
    parser.add_argument("--provider", type=str, default="openai")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo-0613")
    parser.add_argument("--mode", type=str, default="chat")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--context_length", type=int, default=0)
    parser.add_argument("--max_tokens", type=int, default=2048)
    parser.add_argument("--stop_token", type=str, default=None)
    parser.add_argument(
        "--max_retry",
        type=int,
        help="max retry times to perform generations when parsing fails",
        default=1,
    )
    parser.add_argument(
        "--max_obs_length",
        type=int,
        help="when not zero, will truncate the observation to this length before feeding to the model",
        default=1920,
    )
    parser.add_argument(
        "--model_endpoint",
        help="huggingface model endpoint",
        type=str,
        default="",
    )

    # example config
    parser.add_argument("--test_start_idx", type=int, default=0)
    parser.add_argument("--test_end_idx", type=int, default=1000)
    parser.add_argument("--config_folder", type=str, default="config_files")
    # logging related
    parser.add_argument("--result_dir", type=str, default="")
    args = parser.parse_args()

    # check the whether the action space is compatible with the observation space
    if (
        args.action_set_tag == "id_accessibility_tree"
        and args.observation_type != "accessibility_tree"
    ):
        raise ValueError(
            f"Action type {args.action_set_tag} is incompatible with the observation type {args.observation_type}"
        )

    return args


def early_stop(
    trajectory: Trajectory, max_steps: int, thresholds: dict[str, int], visited_links: list
) -> tuple[bool, str]:
    """Check whether need to early stop"""

    # reach the max step
    num_steps = (len(trajectory) - 1) / 2
    if num_steps >= max_steps:
        return True, f"Reach max steps {max_steps}"

    last_k_actions: list[Action]
    last_k_traces: list[StateInfo]
    action_seq: list[Action]

    # Case: parsing failure for k times
    k = thresholds["parsing_failure"]
    last_k_actions = trajectory[1::2][-k:]  # type: ignore[assignment]
    
    if len(last_k_actions) >= k:
        if all(
            [
                action["action_type"] == ActionTypes.NONE
                for action in last_k_actions
            ]
        ):
            return True, f"Failed to parse actions for {k} times"

    # Case: same action for k times
    k = thresholds["repeating_action"]
    last_k_actions = trajectory[1::2][-k:]  # type: ignore[assignment]
    action_seq = trajectory[1::2]  # type: ignore[assignment]
    trace_seq = trajectory[0::2]
    
    # Check if staying on the same page for more than 1 minute
    if len(trace_seq) >= 2:
        current_time = time.time()
        last_trace = trace_seq[-1]
        if 'timestamp' in last_trace['info']:
            page_url = last_trace['info']['page'].url
            time_on_page = current_time - last_trace['info']['timestamp']
            if time_on_page > 60:
                return True, f"Stayed on page {page_url} for more than 1 minute"
    
    # Check if the same trajectory has occurred twice
    # if len(trajectory) >= 6:
    #     for i in range(0, len(trajectory) - 5, 2):
    #         current_obs = re.sub(r'\[\d+\]', '', trajectory[i]['observation']['text'])
    #         current_action = trajectory[i+1]
            
    #         for j in range(i+2, len(trajectory) - 3, 2):
    #             compare_obs = re.sub(r'\[\d+\]', '', trajectory[j]['observation']['text'])
    #             compare_action = trajectory[j+1]
                
    #             if (current_obs == compare_obs and 
    #                 is_equivalent(current_action, compare_action)):
    #                 return True, f"Same trajectory pattern detected twice"
    
    last_link = trace_seq[-1]['info']['page'].url
    if last_link in visited_links:
        return True, f"The link has been visited"
    if len(trace_seq) >= 3:
        last_k_traces = trace_seq[-3:]
        last_k_trajectory_text = [_['observation']['text'] for _ in last_k_traces[-3:]]
                    
        clean_trees = select_unique_trees(last_k_trajectory_text)
        if len(clean_trees) == 1:
            return True, f"Same page structure for 3 times"
    
    if len(action_seq) == 0:
        return False, ""

    last_action: Action = action_seq[-1]

    if last_action["action_type"] != ActionTypes.TYPE:
        if len(last_k_actions) >= k:
            if all(
                [
                    is_equivalent(action, last_action)
                    for action in last_k_actions
                ]
            ):
                return True, f"Same action for {k} times"

    else:
        if (
            sum([is_equivalent(action, last_action) for action in action_seq])
            >= k
        ):
            return True, f"Same typing action for {k} times"
        else:
            if len(trace_seq) <= 3:
                return False, ""

    return False, ""


def test(
    args: argparse.Namespace,
    agent: Agent | PromptAgent | TeacherForcingAgent,
    config_file_list: list[str],
) -> None:
    scores = []
    max_steps = args.max_steps

    early_stop_thresholds = {
        "parsing_failure": args.parsing_failure_th,
        "repeating_action": args.repeating_action_failure_th,
    }

    # visited_links = get_visited_links(os.path.dirname(args.result_dir))
    visited_links = []
    with open("visited_link.txt", "r") as f:
        for line in f.readlines():
            visited_links.append(line.strip())
    visited_links.extend(get_visited_links_this_folder(args.result_dir))
    env = ScriptBrowserEnv(
        # headless=not args.render,
        headless= True,
        slow_mo=args.slow_mo,
        observation_type=args.observation_type,
        # observation_type="html",
        # current_viewport_only=args.current_viewport_only,
        current_viewport_only=False,
        viewport_size={
            "width": args.viewport_width,
            "height": args.viewport_height,
        },
        # save_trace_enabled=args.save_trace_enabled,
        save_trace_enabled = True,
        sleep_after_execution=args.sleep_after_execution,
    )

    for config_file in config_file_list:
        try:
            render_helper = RenderHelper(
                config_file, args.result_dir, args.action_set_tag
            )
            

            # get intent
            with open(config_file) as f:
                _c = json.load(f)
                intent = _c["intent"]
                task_id = _c["task_id"]
                url = _c["start_url"]
                # automatically login
                if _c["storage_state"]:
                    cookie_file_name = os.path.basename(_c["storage_state"])
                    comb = get_site_comb_from_filepath(cookie_file_name)
                    temp_dir = tempfile.mkdtemp()
                    # subprocess to renew the cookie
                    subprocess.run(
                        [
                            "python",
                            "browser_env/auto_login.py",
                            "--auth_folder",
                            temp_dir,
                            "--site_list",
                            *comb,
                        ]
                    )
                    _c["storage_state"] = f"{temp_dir}/{cookie_file_name}"
                    assert os.path.exists(_c["storage_state"])
                    # update the config file
                    config_file = f"{temp_dir}/{os.path.basename(config_file)}"
                    with open(config_file, "w") as f:
                        json.dump(_c, f)

            logger.info(f"[Config file]: {config_file}")
            logger.info(f"[Intent]: {intent}")

            agent.reset(config_file)
            trajectory: Trajectory = []
            obs, info = env.reset(options={"config_file": config_file})
            obs['text']= process_accessibility_tree(obs['text'])
            page_source = info["page"].content
            
            # try:
            #     page_content = BeautifulSoup(page_source, 'html.parser')
            #     if len(page_source)>0 and Detector(page_content.get_text()) not in ['en']:
            #         action = create_stop_action(f"Early stop: Not in English")
            # except:
            #     pass
            state_info: StateInfo = {"observation": obs, "info": info}
            trajectory.append(state_info)

            meta_data = {"action_history": ["None"]}
            action = create_goto_url_action(url)
            visited_xpaths = []
            render_helper.render(
                    action, state_info, meta_data, args.render_screenshot
                )
            trajectory_file = Path(args.result_dir) / f"trajectory_{config_file.split('/')[-1]}.pkl"
            with open(trajectory_file, 'wb') as file:
                pickle.dump(trajectory, file)
            meta_data_path = Path(args.result_dir) / f"metadata_{config_file.split('/')[-1]}"
            with open(meta_data_path, 'w') as f:
                json.dump(meta_data, f)
            while True:
                # print(trajectory[-1]['info'].keys())  
                if len(trajectory[-1]['info']['closes_ele']) > 0:
                    try:
                        todo_paths = [_ for _ in trajectory[-1]['info']['closes_ele'] if _ not in visited_xpaths]
                        if len(todo_paths)>0:
                            closed_xpaths, visited_xpath, msg = env.modal_close(todo_paths)
                            visited_xpaths.extend(visited_xpath)
                            action_str = ""
                            for _ in closed_xpaths:
                                action_str += f'self.page.locator(f"xpath={_}").click()\n'
                            state_info= {"observation": msg[0], "info": msg[-1]}
                            action = create_modal_close_action(closed_xpaths)
                            meta_data["action_history"].append(action_str)
                            render_helper.render(
                                action, state_info, meta_data, args.render_screenshot
                            )
                    except:
                        pass
                # visited_urls.append(trajectory[-1]['info']['page']['url'])
                if trajectory[-1]['info']['popup'] is True:
                    close_id = get_close_id(trajectory[-1]['observation']['text'])
                    if len(close_id)>0:
                        trajectory[-1]['observation'],_,_,_, trajectory[-1]['info'] = env.step(create_id_based_action(f"click {close_id}"))
                    else:
                        trajectory[-1]['observation'],_,_,_, trajectory[-1]['info'] = env._remove_popups()
                    trajectory[-1]['observation']['text'] = process_accessibility_tree(trajectory[-1]['observation']['text'])
                early_stop_flag, stop_info = early_stop(
                    trajectory, max_steps, early_stop_thresholds, visited_links
                )

                if early_stop_flag:
                    action = create_stop_action(f"Early stop: {stop_info}")
                else:
                    try:
                        action = agent.next_action(
                            trajectory, intent, meta_data=meta_data
                        )
                    except ValueError as e:
                        # get the error message
                        action = create_stop_action(f"ERROR: {str(e)}")

                trajectory.append(action)
                # print(state_info)
                action_str = get_action_description(
                    action,
                    state_info["info"]["observation_metadata"],
                    action_set_tag=args.action_set_tag,
                    prompt_constructor=agent.prompt_constructor
                    if isinstance(agent, PromptAgent)
                    else None,
                )
                render_helper.render(
                    action, state_info, meta_data, args.render_screenshot
                )
                meta_data["action_history"].append(action_str)

                if action["action_type"] == ActionTypes.STOP:
                    break

                obs, _, terminated, _, info = env.step(action)
                obs['text'] = process_accessibility_tree(obs['text'])
                state_info = {"observation": obs, "info": info}
                trajectory.append(state_info)

                if terminated:
                    # add a action place holder
                    trajectory.append(create_stop_action(""))
                    break
                trajectory_file = Path(args.result_dir) / f"trajectory_{config_file.split('/')[-1]}.pkl"
                with open(trajectory_file, 'wb') as file:
                    pickle.dump(trajectory, file)
                meta_data_path = Path(args.result_dir) / f"metadata_{config_file.split('/')[-1]}"
                with open(meta_data_path, 'w') as f:
                    json.dump(meta_data, f)
            
            trajectory_file = Path(args.result_dir) / f"trajectory_{config_file.split('/')[-1]}.pkl"
            with open(trajectory_file, 'wb') as file:
                pickle.dump(trajectory, file)
            
            meta_data_path = Path(args.result_dir) / f"metadata_{config_file.split('/')[-1]}"
            with open(meta_data_path, 'w') as f:
                json.dump(meta_data, f)
            # trajectory_json = json.dumps(trajectory, cls=NumpyEncoder)
            # dump_trajectory(trajectory_json)
            # evaluator = evaluator_router(config_file)
            # score = evaluator(
            #     trajectory=trajectory,
            #     config_file=config_file,
            #     page=env.page,
            #     client=env.get_page_client(env.page),
            # )

            # scores.append(score)

            # if score == 1:
            #     logger.info(f"[Result] (PASS) {config_file}")
            # else:
            #     logger.info(f"[Result] (FAIL) {config_file}")

            if args.save_trace_enabled:
                env.save_trace(
                    Path(args.result_dir) / "traces" / f"{task_id}.zip"
                )

        except openai.error.OpenAIError as e:
            logger.info(f"[OpenAI Error] {repr(e)}")
        except Exception as e:
            logger.info(f"[Unhandled Error] {repr(e)}]")
            import traceback

            # write to error file
            with open(Path(args.result_dir) / "error.txt", "a") as f:
                f.write(f"[Config file]: {config_file}\n")
                f.write(f"[Unhandled Error] {repr(e)}\n")
                f.write(traceback.format_exc())  # write stack trace to file
        visited_links.extend(_['info']['page'].url for _ in trajectory[0::2])
        render_helper.close()

    env.close()
    # logger.info(f"Average score: {sum(scores) / len(scores)}")


def prepare(args: argparse.Namespace) -> None:
    # convert prompt python files to json
    from agent.prompts import to_json

    to_json.run()

    # prepare result dir
    result_dir = args.result_dir
    if not result_dir:
        result_dir = (
            f"cache/results_{time.strftime('%Y%m%d%H%M%S', time.localtime())}"
        )
    if not Path(result_dir).exists():
        Path(result_dir).mkdir(parents=True, exist_ok=True)
        args.result_dir = result_dir
        logger.info(f"Create result dir: {result_dir}")

    if not (Path(result_dir) / "traces").exists():
        (Path(result_dir) / "traces").mkdir(parents=True)

    # log the log file
    with open(os.path.join(result_dir, "log_files.txt"), "a+") as f:
        f.write(f"{LOG_FILE_NAME}\n")


def get_unfinished(config_files: list[str], result_dir: str) -> list[str]:
    result_files = glob.glob(f"{result_dir}/*.html")
    task_ids = [
        os.path.basename(f).split(".")[0].split("_")[1] for f in result_files
    ]
    unfinished_configs = []
    for config_file in config_files:
        task_id = os.path.basename(config_file).split(".")[0]
        if task_id not in task_ids:
            unfinished_configs.append(config_file)
    return unfinished_configs


def dump_config(args: argparse.Namespace) -> None:
    config_file = Path(args.result_dir) / "config.json"
    if not config_file.exists():
        with open(config_file, "w") as f:
            json.dump(vars(args), f, indent=4)
            logger.info(f"Dump config to {config_file}")
def dump_trajectory(trajectory) -> None:
    trajectory_file = Path(args.result_dir) / "trajectory.json"
    with open(trajectory_file, "w") as f:
        json.dump(trajectory, f)
        # json.dump(vars(args), f, indent=4)
        # logger.info(f"Dump config to {config_file}")

if __name__ == "__main__":
    args = config()
    args.sleep_after_execution = 2.0
    prepare(args)

    test_file_list = []
    st_idx = args.test_start_idx
    ed_idx = args.test_end_idx
    config_folder = args.config_folder
    for i in range(st_idx, ed_idx):
        test_file_list.append(f"{config_folder}/{i}.json")
    if "debug" not in args.result_dir:
        test_file_list = get_unfinished(test_file_list, args.result_dir)

    if len(test_file_list) == 0:
        logger.info("No task left to run")
    else:
        print(f"Total {len(test_file_list)} tasks left")
        args.render = False
        args.render_screenshot = True
        args.save_trace_enabled = False

        args.current_viewport_only = False
        dump_config(args)

        agent = construct_agent(args)
        test(args, agent, test_file_list)
