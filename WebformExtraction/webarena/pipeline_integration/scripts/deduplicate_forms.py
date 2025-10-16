import json

def element_to_string(element):
    return json.dumps(element, sort_keys=True)

def form_to_string(form):
    return [element_to_string(element) for element in form if element.get("Element_Type") != "SENT_LIST"]

def is_sublist(form, subform):
    form_str_list = form_to_string(form)
    subform_str_list = form_to_string(subform)

    subform_length = len(subform_str_list)
    
    for i in range(len(form_str_list) - subform_length + 1):
        if form_str_list[i:i + subform_length] == subform_str_list:
            return True

    return False

def check_sublist_forms(forms_list):
    sublists = []

    for i, form_dict in enumerate(forms_list):
        form_results = form_dict.get('form_result', [])
        for form_idx, form in enumerate(form_results):
            if len(form)==1 and form[0]['Element_Type']== "SENT_LIST":
                continue
            for j, other_form_dict in enumerate(forms_list):
                if i != j:
                    other_form_results = other_form_dict.get('form_result', [])
                    for other_form_idx, other_form in enumerate(other_form_results):
                        if is_sublist(other_form, form):
                            sublists.append((i, form_idx, j, other_form_idx))
    
    if not sublists:
        print("No forms are sublists of other forms.")
    else:
        print("The following forms are sublists of other forms:")
        for subform_idx, subform_sub_idx, form_idx, form_sub_idx in sublists:
            print(f"Form at index {subform_idx} (form {subform_sub_idx}) is a sublist of form at index {form_idx} (form {form_sub_idx})")


def read_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
    path = "/home/ying/projects/web_navigation/webarena/result_folders/digitalocean_com/overall_final_with_link.json"
    data = read_json(path)
    check_sublist_forms(data)