import json
import spacy

ELEMENT_PROPERTY = {
    "element": "element({element_id}, {element_type}, {element_text}).",
    "element_required": "element_required({element_id}, {element_required}).",
    "element_checked": "element_checked({element_id}, {element_checked}).",
    "element_editable": "element_editable({element_id}, {element_editable}).",
    "text": "text({sent_id}, {text})."
}

nlp = spacy.load("en_core_web_sm")

properties = []

def read_json(filepath):
    with open(filepath, "r") as f:
        data = json.load(f)
    f.close()
    return data

def write2json(data, filepath):
    with open(filepath, "w") as f:
        json.dump(data, f)
    f.close()
def property_extraction(form_list):
    for each in form_list:
        nodes = each['nodes']
        for node in nodes:
            node.pop('chromeRole')
            properties = node['properties']
            new_properties = {}
            for each_property in properties:
                property_value = each_property["value"].get("value", None)
                new_properties[each_property["name"]] = property_value
            node['new_properties'] = new_properties
    return form_list

# def preprocess_sent(paragraph):


# def element_property_facts(new_form_list):
#     property_lists = []
#     sent_id = 0
#     for each in new_form_list:
#         element_type = list(each.keys())[0]
#         element_value = list(each.values())[0]
#         if element_type in ['text', 'checkbox', 'toggle']:
#             sentences = [sent.text for sent in element_value.sents]
#             for sent in sentences:
#                 property_lists.append(ELEMENT_PROPERTY["text"].format(sent_id, sent))
#                 sent_id += 1
#         elif element_type in ['']:
            


filepath = "/home/ying/projects/web_navigation/webarena/test_form.json"
form_list_json = read_json(filepath)
new_form = property_extraction(form_list_json)
write2json(new_form, "/home/ying/projects/web_navigation/webarena/test_new_form.json")
print(new_form)
