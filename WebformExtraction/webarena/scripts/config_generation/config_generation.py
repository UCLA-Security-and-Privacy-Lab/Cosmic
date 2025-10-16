import json
website_purpose_dict = json.load(open("default_website_purpose.json"))
import os
TEMPLATE_CONFIG ={
    "sites": [
        "test"
    ],
    "task_id": "0",
    "start_url": "{}",
    "storage_state": None,
    "geolocation": None,
    "intent": "Please navigate to the web forms for the purpose of '{}'. As long as you find all the webforms with above purposes, you can stop. If you explored but did not find, please stop.",
    "require_reset": False
}

template_config = TEMPLATE_CONFIG.copy()

for website, purposes in website_purpose_dict.items():
    directory = f"/bigtemp/fr3ya/webarena/configure/{website.replace('.', '_')}"
   
    template_config["start_url"] = "http://"+ website
    if "market" not in " ".join(purposes).lower():
        purposes.append("marketing")
    template_config["intent"] = TEMPLATE_CONFIG["intent"].format(", ".join(purposes))
    template_config["task_id"] = "0"
    # print(template_config)
    if os.path.exists("/bigtemp/fr3ya/webarena/results_test/"+website.replace('.', '_')):
        # print(directory)
        continue
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    # print(directory)
    with open(f"{directory}/0.json", "w") as f:
        json.dump(template_config, f)
