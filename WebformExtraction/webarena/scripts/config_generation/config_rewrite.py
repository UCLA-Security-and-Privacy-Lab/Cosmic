import os
import json

CONFIG_DIR = "/home/ying/projects/web_navigation/webarena/configure"

for dirs in os.listdir(CONFIG_DIR):
    tmp_dir = os.path.join(CONFIG_DIR, dirs)
    # for dir_ in dirs:
    for file in os.listdir(tmp_dir):
        if file.endswith(".json"):
            print(tmp_dir)
            with open(os.path.join(tmp_dir, file), "r") as f:
                config = json.load(f)
            config["storage_state"] = None
            config["geolocation"] = None
            # print(config)
            # # exit()
            try:
                with open(os.path.join(tmp_dir, file), "w") as f:
                    json.dump(config, f)
            except Exception as e:
                print(tmp_dir)
                print(e)
                exit()
