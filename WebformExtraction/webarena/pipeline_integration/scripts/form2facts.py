import json
import os
import openai
import argparse
from tqdm import tqdm
openai.api_key = 'sk-proj-xxxxxx'

TEXTBOX_TYPE = ["email", "tel"]
SELECT_TYPE = ["checkbox", "radio", "switch", "option"]
CRT_SYSTEM_MSG = """
Task: Classify a sentence as a consent request text or not.
Website administrators often need to collect user data to enable certain features or services. To comply with regulations and ensure transparency, it's essential to obtain user consent before collecting data or providing such services.
Consent can appear in the following forms:
1. Explicit Consent Request Texts: These are clear statements where the website asks for user consent. For example: "By clicking the button, I agree to xxx."
2. Consent Preference Expressions: These statements reflect the user's choice or preference regarding data collection or service usage. For example: "I want to receive promotional emails." / "Please tick this box if you'd rather not receive these emails."
3. Implicit Consent Expressions: These are typically imperative sentences that suggest user consent through actions (e.g., filling out a form, clicking a button) with a clear purpose. For example: "Join the newsletter"; "Subscribe to our newsletter to receive discounts and updates"; "Keep up all updates".
Instruction:
Given a sentence, determine if it serves as (a) a consent request, (b) a preference expression, or (c) implies consent through a clear call-to-action with stated purpose.
If so (any of the above applies), output: { "crt": "Y" }
If not (the sentence is unrelated to consent request), output: { "crt": "N" }
Please only reply the formatted json without any other text.
"""

CONTROLLER_SYSTEM_MSG = """
You are an NLP model specialized in extracting the GDPR data controller from web form text.

Definition:
- A data controller is the entity (e.g., company, organization, individual) that determines the purposes and means of processing personal data.

Task:
Given a list of text segments from a single web form, identify the data controller according to the following rules:

Identification Rules:
1. If the name of an organization, business, or domain explicitly appears (e.g., "DataCorp Ltd.", "example.com"), extract and return that exact name.
2. If no explicit organization name appears, but the text uses pronouns like "we", "our", or "us" (e.g., contact us), indicating an implicit reference to the website operator, return "IMPLICIT_WEBSITE_OWNER".
3. If neither explicit names nor pronouns appear in the provided texts, return null.

Input format (LIST):
[
    "<text segment 1>",
    "<text segment 2>",
    "... additional segments ..."
]

Output format (JSON):
{
    "data_controller": "<Explicit controller name | IMPLICIT_WEBSITE_OWNER | null>"
}
"""

CRT_ATTR_SYSTEM_MSG = """
You are an NLP model tasked with extracting structured information from sentences that request user consent. For each sentence, extract the following fields in **JSON format**:

- data_controller: The organization or entity controlling the data, if mentioned (e.g., domain names like blogs.davita.com, our, we, etc.). For exmaple, "we will contact you shortly" should be "we". Otherwise, return null.
- action: The explicit user action required (e.g., "click the subscribe button"). Use the **original verb form**, omit pronouns, and include the relevant UI element (e.g., "enter email", "check box").
- purpose: A list of all distinct purposes for which consent is requested. Each entry should:
    - Be a short phrase **quoted directly from the original text**, retaining the verb + object structure (e.g., "agree to the Terms of Use").
    - Data Processing purpose should be ignored
    - Include one verb-object pair per entry, even if multiple objects share the same verb.
    - For example, "agree to the Terms of Use and Privacy Policy" should yield:
      ["agree to the Terms of Use", "agree to the Privacy Policy"]
    - Do not infer or paraphrase—only use phrases explicitly stated in the sentence.
    - Explicitly **exclude** generic consent-granting expressions such as:
        - "give my consent to..."
        - "consent to..."
        - "I hereby consent..."
        - "I allow..."
        - "I authorize..."
    - For purposes that with phrases like "process your data for X", treat only X as the actual purpose when determining semantic similarity. For example, "store and process the personal information submitted above to provide you the content requested", the purpose is only ["provide you the content requested"] instead of ['store the personal information', 'process the personal information', 'provide you the content requested']; "consent to receive marketing communications" should be ["receive marketing communications"] instead of ["consent to receive marketing communications"]; "store my information to receive newsletter" should be ["receive newsletter"]; the purpose of "given consent to xxx" should be ignored.
- Negation (neg): Set to true if the user's action expresses refusal, withdrawal, or denial of consent. This includes:
    - Sentences that directly negate the purpose (e.g., "Do not sell my personal information").
    - Sentences where a positive action (e.g., "check box") is used to deny consent (e.g., "Check the box if you don't want to...").
    - Double Negation Rule: If the sentence contains multiple negations (e.g., "do not want to opt out"), determine the actual intent of the user action. If the final outcome indicates consent is granted, then set neg: false. Only set neg: true when the result of the action is a denial or withdrawal of consent.
- neg_reason: A brief reason for the value of neg, chosen from one of the following:
    - "direct negation": purpose is explicitly negated (e.g., "Do not sell my personal information").
    - "action implies refusal": the user action expresses refusal (e.g., "click to unsubscribe", "disable tracking").
    - "positive action with negative intent": action like "check" or "click" is used to express refusal (e.g., "check the box if you don't want...").
    - "double negation = consent": multiple negations cancel out and imply acceptance (e.g., "do not want to opt out").
    - "consent": action clearly expresses agreement (e.g., "click to agree", "enter email to receive updates").
    - null: use when negation is not discernible or applicable.
- element: The UI element that the user must act on (e.g., button, checkbox).
    - If the element is **explicitly mentioned**, extract it directly (e.g., "check the box" → "checkbox").
    - If the element is **not mentioned but clearly implied by the verb**, infer as follows:
        - "click" → "button"
        - "check"/"uncheck" → "checkbox"
        - "enter" → "textbox"
    - Otherwise, return null.
**Important rules:**
- Do not infer or rephrase information that is not explicitly present in the sentence.
- If any field is not explicitly discernible from the sentence, return null for that field.
- Output only the JSON object—no extra text.

### Examples:
Sentence: "By clicking the subscribe button, I certify that I have read and agree to the Terms of Use and Privacy Policy for blogs.davita.com."  
Response: { "data_controller": "blogs.davita.com", "action": "click the subscribe button", "purpose": ["read the Terms of Use", "agree to the Terms of Use", "read the Privacy Policy", "agree to the Privacy Policy"], "neg": false, "neg_reason": "consent", "element": "button"}

Sentence: "Uncheck the box if you do not want to opt out of personalized ads."   
Response: {"data_controller": null, "action": "uncheck the box", "purpose": ["opt out of personalized ads"], "neg": false, "neg_reason": "double negation = consent", "element": "checkbox"}

Sentence: "Check the box if you don't want your data shared with third parties."   
Response: {"data_controller": null, "action": "check the box", "purpose": ["your data shared with third parties"], "neg": true, "neg_reason": "direct negation", "element": "checkbox"}  

Sentence: "Sign up for our newsletter"
Response: {"data_controller": our, "action": "sign up", "purpose": ["our newsletter"], "neg": false, "neg_reason": "consent", "element": "null"}

Sentence: "you agree to our Terms of Service"
Response: {"data_controller": our, "action": "agree to our Terms of Service", "purpose": ["our Terms of Service"], "neg": false, "neg_reason": "consent", "element": "null"}

Sentence: "I allow the company to store and process the personal information submitted above to provide you the content requested"
Response: {"data_controller": "the company", "action": "allow", "purpose": ["provide you the content requested"], "neg": false, "neg_reason": "consent", "element": "null"}

Sentence: "I hereby give my consent to Questpass Sp. z o.o. to process the data I have provided in the above form, concerning my phone number or e-mail address, respectively, in order to receive commercial information through the communication channels made available by me in the above form."  
Response: { "data_controller": "Questpass Sp. z o.o.", "action": null, "purpose": ["receive commercial information"], "neg": false, "neg_reason": "consent", "element": null }
"""

WITHDRAWAL_SYSTEM_MSG = """
Task: Classify a sentence as related to withdrawing consent or not.
Websites and services must provide users with a way to withdraw their consent at any time, in a clear and accessible manner. Withdrawal texts inform users how they can revoke previously given consent.

Withdrawal statements can appear in the following forms:
1. Explicit Withdrawal Instructions: These are direct instructions or options provided to users to withdraw their consent. For example: "You can unsubscribe at any time"; "Click here to revoke your consent."
2. Implicit Withdrawal Options: These are imperatives or options associated with ending or opting out of services, often without using the word "withdraw". For example: "Unsubscribe"; "Opt out of promotional emails".
3. Informational Statements about Withdrawal: These statements notify users about their right or ability to withdraw consent. For example: "Users can change their consent preferences in the settings"; "You may withdraw your consent at any time without affecting service."

Instruction:
Given a sentence, determine if it serves as (a) a withdrawal instruction, (b) an option to opt out, or (c) an informative statement about the right to withdraw consent.
If so (any of the above applies), output: { "withdraw": "Y" }
If not (the sentence is unrelated to withdrawing consent), output: { "withdraw": "N" }
Please only reply the formatted json without any other text.
"""

WITHDRAWAL_METHOD_SYSTEM_MSG = """
Task: Extract the method by which a user can withdraw consent from a sentence.

Websites must provide users with a way to withdraw previously given consent. This withdrawal method may be expressed as a direct action (e.g., clicking a link or button), navigating to a settings page, contacting support, or other mechanisms.

Common withdrawal methods include but are not limited to:
- Clicking a specific button or link (e.g., "click here to unsubscribe")
- Visiting a settings or preferences page (e.g., "manage your preferences in settings")
- Contacting the service via email or support form (e.g., "email us at privacy@example.com")
- Selecting an option or unchecking a checkbox (e.g., "uncheck this box to stop receiving updates")

Instruction:
Given a sentence, identify and extract the **specific action or method** users are instructed to perform to withdraw consent.
If no withdrawal method is found, return: { "withdraw_method": null }
Otherwise, return the extracted method in plain text, for example:
{ "withdraw_method": "Click the unsubscribe link" }

Please only reply the formatted json without any other text.
"""

SYSTEM_MSG_CLUSTER_PURPOSES = """
You are a language model that clusters user consent purposes into semantically related groups.

You will receive a list of short purpose phrases, each with an associated sentence ID (sent_id). Your task is to:
1. Group semantically similar purposes together.
2. Assign a clear and concise label to each group (e.g., "Policy agreement", "Marketing subscription").
3. For each group, list the original purposes along with their associated sent_id.

Guidelines:
- Do not rephrase, merge, or modify the purpose text. Keep the original text exactly as provided.
- Do not include anything related to Data Processing/Storage in the purpose
- Purposes that involve the same kind of user intention (e.g., agreeing to or reading a policy) should be grouped together.
    - For example, "read/review the Privacy Policy" and "agree to the Privacy Policy" should both go into a group labeled "Policy agreement".
    - If a purpose does not semantically fit with any other, place it in its own group with an appropriate label.
- You must preserve the sent_id with each purpose.

Format your output as a JSON array of groups, like this:

[
  {
    "label": "Group Name",
    "items": [
      {"sent_id": <int>, "purpose": "<original purpose>"},
      ...
    ]
  },
  ...
]

Now, cluster the following purposes:

"""

ACTION_ELEMENT_SYSTEM_MSG =  """"
You are an assistant that matches a user-facing field description to the **single most likely** UI element on a web form.

You will be given:
- A field description: a short user-facing phrase (e.g., "input your business email")
- A list of UI elements. Each element has:
  - element_id: integer
  - element_type: (e.g., "textbox", "button")
  - element_text: label or visible text

Your task is to:
1. Choose the **one most likely matching element**, based on the field description and element_text/type.
2. Return it in JSON format with:
   - element_id
   - element_text
   - element_type
   - reason: why this matches

3. If no element clearly matches, return an empty list.

Rules:
- Do NOT return multiple elements.
- You MUST choose from the given list. Do not make up or guess new element_ids.
- Only return the top match with strong semantic similarity.
- If the match is weak or uncertain, return "match": {}

### Output Format:
{
  "field_description": "<original field description>",
  "match": 
    {
      "element_id": <int>,
      "element_text": "<text>",
      "element_type": "<type>",
      "reason": "<reason>",
    }
  }
}

If no element matches, return:
{
  "field_description": "<original field description>",
  "match": {}
}
"""

def validate_and_fix_match_single(field_description, elements, llm_output):
    
    match = llm_output.get("match")
    # print(match)
    if match:
        target_text = match.get("element_text")
        target_type = match.get("element_type")

        for el in elements:
            if el["element_text"].lower() == target_text.lower() and el["element_type"].lower() == target_type.lower():
                return {
                    "field_description": field_description,
                    "match": {
                        "element_id": el["element_id"],
                        "element_text": el["element_text"],
                        "element_type": el["element_type"],
                        "reason": match.get("element_type")
                    }
                }

    # 
    return {
        "field_description": field_description,
        "match": None
    }



def get_cluster_purposes(input_sent_list):
    completion = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"{SYSTEM_MSG_CLUSTER_PURPOSES}"},
        {"role": "user", "content": f"{input_sent_list}"}
    ])
    try:
        ret_content = completion.choices[0].message.content 
        ret_content = ret_content.replace('```','').replace("'''",'')
        ret_content = json.loads(ret_content)
    except:
        ret_content = {"cluster_unknown": "unknown"}
    return ret_content

def get_controller(input_sent_list):
    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"{CONTROLLER_SYSTEM_MSG}"},
            {"role": "user", "content": f"{input_sent_list}"}
        ])
    try:
        ret_content = completion.choices[0].message.content 
        ret_content = ret_content.replace('```','').replace("'''",'')
        ret_content = json.loads(ret_content)
    except Exception as e:
        print(e)
        print(ret_content)
        ret_content = {"data_controller": "unknown"}
    return ret_content
def get_crt_label(input_sent):
    completion = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"{CRT_SYSTEM_MSG}"},
        {"role": "user", "content": f"{input_sent}"}
    ])
    try:
        ret_content = completion.choices[0].message.content 
        ret_content = ret_content.replace('```','').replace("'''",'')
        ret_content = json.loads(ret_content)
    except:
        ret_content = {"crt": "unknown"}
    return ret_content

def get_withdraw_label(input_sent):
    completion = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"{WITHDRAWAL_SYSTEM_MSG}"},
        {"role": "user", "content": f"{input_sent}"}
    ])
    try:
        ret_content = completion.choices[0].message.content 
        ret_content = ret_content.replace('```','').replace("'''",'')
        ret_content = json.loads(ret_content)
    except:
        ret_content = {"withdraw": "unknown"}
    return ret_content

def get_crt_attr(input_sent):
    completion = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"{CRT_ATTR_SYSTEM_MSG}"},
        {"role": "user", "content": f"{input_sent}"}
    ])
    try:
        ret_content = completion.choices[0].message.content 
        ret_content = ret_content.replace('```','').replace("'''",'')
        ret_content = json.loads(ret_content)
    except:
        ret_content = {"data_controller": "unknown",  "action": "unknown",  "purpose": "unknown",  "element": "unknown"}
    return ret_content

def get_withdraw_method(input_sent):
    completion = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"{WITHDRAWAL_METHOD_SYSTEM_MSG}"},
        {"role": "user", "content": f"{input_sent}"}
    ])
    try:
        ret_content = completion.choices[0].message.content 
        ret_content = ret_content.replace('```','').replace("'''",'')
        ret_content = json.loads(ret_content)
    except:
        ret_content = {"withdraw_method": "unknown"}
    return ret_content

def get_action_element(input_sent):
    completion = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"{ACTION_ELEMENT_SYSTEM_MSG}"},
        {"role": "user", "content": f"{input_sent}"}
    ])
    try:
        ret_content = completion.choices[0].message.content 
        ret_content = ret_content.replace('```','').replace("'''",'')
        ret_content = json.loads(ret_content)
    except:
        ret_content = {"field_description": "unknown", "match": {}}
    return ret_content

def parse_form(form_dict):
    form_facts = {"element":[], "required":[], "status":[], "crt":[], "crt_attr":[], "withdraw":[], "withdraw_method":[], "text":[], "action_element":[]}
    sent_id = 0
    for each in form_dict['properties']['ELEMENT']:
        if each['element_text'] == "" and each['placeholder'] == "":
            continue
        element_dict = {}
        element_dict['element_id'] = each['element_id']
        if each['element_type'] == "submit":
            element_dict['element_type'] = "button"
        elif each['element_type'] in TEXTBOX_TYPE:
            element_dict['element_type'] = "textbox"
        elif each['element_type'] in SELECT_TYPE:
            tmp_text = each['element_text'].strip("*").strip()
            element_dict['element_type'] = each['element_type']
            form_facts["crt"].append({"sent_id":sent_id, "text":tmp_text, "element_id":each['element_id']})
            sent_id += 1
        else:
            element_dict['element_type'] = each['element_type']
        element_dict['element_text'] = each['element_text'].strip("*").strip() if each["element_text"] != "" else each["placeholder"].stirp("*").strip()
        form_facts["element"].append(element_dict)
        if 'element_required' in each:
            required_dict = {}
            required_dict['element_id'] = each['element_id']
            required_dict['element_required'] = each['element_required']
            form_facts["required"].append(required_dict)
        if 'element_status' in each:
            element_status_dict = {}
            element_status_dict['element_id'] = each['element_id']
            element_status_dict['element_status'] = each['element_status']
            form_facts["status"].append(element_status_dict)
    
    form_dict['properties']['TEXT'] = process_text_to_dict_list(form_dict['properties']['TEXT'])
    added_sents = [_['text'] for _ in form_facts['crt']]
    for each in form_dict['properties']['TEXT']:
        FLAG = False
        sentence = each['text'].strip().replace("  ", " ")
        if sentence in added_sents:
            withdraw_label = get_withdraw_label(sentence)
            if withdraw_label['withdraw'] == "Y":
                form_facts["withdraw"].append({"sent_id":sent_id, "text":sentence})
                FLAG = True
        else:        
            crt_label = get_crt_label(sentence)
            if crt_label['crt'] == "Y":
                form_facts["crt"].append({"sent_id":sent_id, "text":sentence, "element_id":-1})
            withdraw_label = get_withdraw_label(sentence)
            if withdraw_label['withdraw'] == "Y":
                form_facts["withdraw"].append({"sent_id":sent_id, "text":sentence})
            FLAG = True
            
        if FLAG:
            sent_id += 1

    crt_sent_id = {_.get('sent_id'):_.get('element_id') for _ in form_facts['crt'] if _.get('element_id') != -1}
    crt_sent_text = {_.get('sent_id'):_.get('text') for _ in form_facts['crt']}
    for each in form_facts['crt']:
        crt_attr = get_crt_attr(each['text'])
        crt_attr['sent_id'] = each['sent_id']
        if crt_attr['purpose'] is None:
            crt_attr['purpose'] = [crt_sent_text[each['sent_id']]]
        if len(crt_attr['purpose']) == 0:
            crt_attr['purpose'] = [crt_sent_text[each['sent_id']]]
        form_facts['crt_attr'].append(crt_attr)
    for each in form_facts['withdraw']:
        withdraw_method = get_withdraw_method(each['text'])
        withdraw_method['sent_id'] = each['sent_id']
        form_facts['withdraw_method'].append(withdraw_method)
    # get all the purposes and corresponding sent_id
    sent_purpose_list = []
    for each in form_facts['crt_attr']:
        for each_purpose in each['purpose']:
            sent_purpose_list.append({"sent_id":each['sent_id'], "purpose":each_purpose})
    cluster_purposes = get_cluster_purposes(sent_purpose_list)
    form_facts['cluster_purposes'] = cluster_purposes
    

    for each in form_facts['crt_attr']:
        # get all of the crt sent id, if the each['sent_id'] in crt_sent_id and element_id!=-1, then add the element_id to the tmp_dict['element']
        element_id_dict = {_.get('element_id'):_ for _ in form_facts['element']}
        if each['sent_id'] in crt_sent_id:
            tmp_action_element = {}
            tmp_action_element["field_description"] = each['action']
            tmp_action_element['match'] = element_id_dict[crt_sent_id[each['sent_id']]]
            tmp_action_element['sent_id'] = each['sent_id']
            form_facts['action_element'].append(tmp_action_element)
        else:
            tmp_dict = {}
            tmp_dict['field_description'] = each['action']
            tmp_dict['element'] = [_ for _ in form_facts['element'] if _.get('element_type') != "select"]
            action_element = get_action_element(tmp_dict)
            action_element = validate_and_fix_match_single(each['action'], form_facts['element'], action_element)
            action_element['sent_id'] = each['sent_id']
            form_facts['action_element'].append(action_element)
    
    all_text = []
    all_text.extend([_['text'] for _ in form_dict['properties']['TEXT']])
    all_text.extend([_['element_text'] for _ in form_dict['properties']['ELEMENT']])
    all_text = list(set(all_text))

    form_facts['data_controller'] = get_controller(all_text)
    return form_facts

def process_text_to_dict_list(text_list):
    # If input is already a list of dictionaries, return as is
    if text_list and isinstance(text_list[0], dict):
        return text_list
        
    # Otherwise convert text list to dictionary list
    return [
        {
            "sent_id": i,
            "text": text.strip()
        }
        for i, text in enumerate(text_list)
    ]

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--websites_folder', type=str, default='38degrees_org_uk')
    return parser.parse_args()

def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

dir_path = "/home/ying/projects/web_navigation/webarena/results_test"

website_dirs = os.listdir(dir_path)
# args = arg_parse()
# website_dirs = [args.websites_folder]
# website_dirs = ['www_metrixlab_com']
for website_folder in tqdm(website_dirs):
    website_path = os.path.join(dir_path, website_folder)
    aligned_form_path = os.path.join(website_path, "merged_images")
    if not os.path.exists(aligned_form_path):
        continue
    for aligned_form_file in os.listdir(aligned_form_path):
        # print(aligned_form_file)
        tmp_aligned_form_path = os.path.join(aligned_form_path, aligned_form_file, 'aligned_form_data.json')
        if not os.path.exists(tmp_aligned_form_path):
            with open("error_form2facts.txt", "a") as f:
                f.write(tmp_aligned_form_path + '\n')
            continue
        # print(tmp_aligned_form_path)
            # aligned_form_data = read_json(tmp_aligned_form_path)
        aligned_form_data = read_json(tmp_aligned_form_path)
        for each_form in aligned_form_data['forms']:
            form_facts = parse_form(each_form)
            each_form['facts'] = form_facts
            with open(tmp_aligned_form_path, "w") as f:
                json.dump(aligned_form_data, f, ensure_ascii=False)
# for website_folder in tqdm(website_dirs):
#     website_path = os.path.join(dir_path, website_folder)
#     form_path = os.path.join(website_path, "form_info")
#     if not os.path.exists(form_path):
#         continue
#     form_files = os.listdir(form_path)
#     for form_file in form_files:
#         tmp_form_path = os.path.join(form_path, form_file)
#         with open(tmp_form_path, "r") as f:
#             form_dict = json.load(f)
#         for each_form in form_dict['forms']:
#             # if 'facts' in each_form:
#             #     continue
#             form_facts = parse_form(each_form)
#             # print(form_facts)
            
#             each_form['facts'] = form_facts
#             # print(form_facts)
#         with open(tmp_form_path, "w") as f:
#             json.dump(form_dict, f, ensure_ascii=False)
