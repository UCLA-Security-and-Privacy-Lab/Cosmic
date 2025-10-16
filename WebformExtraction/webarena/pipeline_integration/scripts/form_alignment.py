import json
from typing import Dict, List, Any, Optional
import os
from tqdm import tqdm
class ElementMatcher:
    def __init__(self, html_elements: List[Dict], llm_elements: List[Dict]):
        """
        Initialize the element matcher
        
        Args:
            html_elements: List of elements extracted from HTML
            llm_elements: List of elements extracted by LLM from screenshot
        """
        self.html_elements = html_elements
        self.llm_elements = llm_elements
        self.matched_pairs = []
        self.unmatched_html = []
        self.unmatched_llm = []
        
    def match_elements(self) -> List[Dict]:
        """
        Match elements between HTML and LLM extracted data
        
        Returns:
            List of matched element pairs
        """
        # Filter out static text elements from LLM data
        form_llm_elements = [
            elem for elem in self.llm_elements
            if elem.get("Element_Type", "").upper() != "STATIC_TEXT"
        ]
        
        # Matching process
        for html_elem in self.html_elements:
            best_match = None
            best_score = 0.35  # Threshold for considering a match
            
            for llm_elem in form_llm_elements:
                # Skip already matched LLM elements
                if llm_elem in [pair["llm_element"] for pair in self.matched_pairs]:
                    continue
                
                # Calculate match score by checking all possible text attributes
                match_score = self._calculate_comprehensive_similarity(html_elem, llm_elem)
                
                if match_score > best_score:
                    best_score = match_score
                    best_match = llm_elem
            
            if best_match:
                self.matched_pairs.append({
                    "html_element": html_elem,
                    "llm_element": best_match,
                    "match_score": best_score
                })
            else:
                self.unmatched_html.append(html_elem)
        
        # Find unmatched LLM elements
        self.unmatched_llm = [
            elem for elem in form_llm_elements
            if elem not in [pair["llm_element"] for pair in self.matched_pairs]
        ]
        
        return self.matched_pairs
    
    def _calculate_comprehensive_similarity(self, html_elem: Dict, llm_elem: Dict) -> float:
        """
        Calculate comprehensive similarity between HTML and LLM elements
        considering multiple possible HTML attributes containing text
        
        Args:
            html_elem: HTML element
            llm_elem: LLM element
            
        Returns:
            Similarity score (0-1)
        """
        score = 0
        
        # 1. Type matching - handle None values safely
        html_tag = html_elem.get("tag", "").lower() if html_elem.get("tag") is not None else ""
        html_type = html_elem.get("type", "").lower() if html_elem.get("type") is not None else ""
        llm_type = llm_elem.get("Element_Type", "").lower() if llm_elem.get("Element_Type") is not None else ""
        
        if self._match_element_types(html_tag, html_type, llm_type):
            score += 0.3
        
        # 2. Text matching - check multiple possible HTML attributes
        llm_text = llm_elem.get("Element_Text", "").lower() if llm_elem.get("Element_Text") is not None else ""
        
        # Extract all HTML attributes that might contain text
        html_texts = []
        
        # placeholder attribute
        if html_elem.get("placeholder") is not None:
            html_texts.append(html_elem.get("placeholder", "").lower())
        
        # label attribute
        if html_elem.get("label") is not None:
            html_texts.append(html_elem.get("label", "").lower())
        
        # label_text attribute - 
        if html_elem.get("label_text") is not None:
            html_texts.append(html_elem.get("label_text", "").lower())
        
        # Button text or value
        if html_tag == "button" and html_elem.get("text") is not None:
            html_texts.append(html_elem.get("text", "").lower())
        elif html_type == "submit" and html_elem.get("value") is not None:
            html_texts.append(html_elem.get("value", "").lower())
        
        # name attribute (sometimes related to display text)
        if html_elem.get("name") is not None:
            name = html_elem.get("name", "").lower()
            # Convert name format, e.g., "first_name" -> "first name"
            formatted_name = name.replace("_", " ").replace("-", " ")
            html_texts.append(formatted_name)
        
        # Calculate the best match score with any attribute
        best_text_score = 0
        for html_text in html_texts:
            text_score = self._calculate_text_similarity(html_text, llm_text)
            best_text_score = max(best_text_score, text_score)
        
        score += best_text_score * 0.7  # Higher weight for text matching
        
        return score
    
    def _match_element_types(self, html_tag: str, html_type: str, llm_type: str) -> bool:
        """
        Check if element types match between HTML and LLM
        
        Args:
            html_tag: HTML tag
            html_type: HTML input type
            llm_type: LLM element type
            
        Returns:
            Boolean indicating if types match
        """
        # Type mapping
        if llm_type in ["textbox", "text field", "field", "input", "text"] and html_tag in ["input", "textarea"]:
            if html_type in ["text", "email", "password", "tel", "url", ""]:
                return True
        elif llm_type == "button" and (html_tag == "button" or html_type == "submit" or html_type == "button"):
            return True
        elif llm_type in ["dropdown", "select", "option", "menu"] and html_tag == "select":
            return True
        elif llm_type in ["checkbox", "check", "checkmark", "tick"] and html_type == "checkbox":
            return True
        elif llm_type in ["radio", "radio button", "option"] and html_type == "radio":
            return True
        elif llm_type in ["textarea", "text area", "multiline"] and html_tag == "textarea":
            return True
        elif llm_type in ["file", "upload", "attachment"] and html_type == "file":
            return True
        
        return False
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score (0-1)
        """
        # Normalize texts
        text1 = text1.lower().strip().replace("*", "")
        text2 = text2.lower().strip().replace("*", "")
        
        if not text1 or not text2:
            return 0
        
        # Exact match
        if text1 == text2:
            return 1.0
        
        # Substring match
        if text1 in text2 or text2 in text1:
            shorter = text1 if len(text1) < len(text2) else text2
            longer = text2 if len(text1) < len(text2) else text1
            return len(shorter) / len(longer) * 0.9
        
        # Word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        overlap = words1.intersection(words2)
        if not overlap:
            return 0
            
        return len(overlap) / max(len(words1), len(words2)) * 0.8
    
    def generate_merged_elements(self) -> List[Dict]:
        """
        Generate elements that merge information from both HTML and LLM sources
        Always prioritize HTML element type information
        
        Returns:
            List of merged elements
        """
        merged_elements = []
        
        # Process matched elements
        for pair in self.matched_pairs:
            html_elem = pair["html_element"]
            llm_elem = pair["llm_element"]
            
            # Create merged element, preserving all original attributes
            # IMPORTANT: We prioritize HTML element type information
            merged = html_elem.copy()
            
            # Add LLM-extracted information but don't override HTML type data
            merged.update({
                "visual_text": llm_elem.get("Element_Text", ""),
                "visual_type": llm_elem.get("Element_Type", ""),  # Just for reference but not used for final type
                "visual_status": llm_elem.get("Element_Status", ""),
                "visual_value": llm_elem.get("Element_Value", ""),
                "match_confidence": pair["match_score"],
                "source": "matched"
            })
            
            # If HTML lacks label but LLM has text, use LLM text as label
            if (not merged.get("label") or merged.get("label") == "") and llm_elem.get("Element_Text"):
                merged["label"] = llm_elem.get("Element_Text")
                
            # Check if required based on asterisk
            llm_text = llm_elem.get("Element_Text", "")
            placeholder = merged.get("placeholder", "")
            if (llm_text and "*" in llm_text) or (placeholder and "*" in placeholder):
                merged["required"] = True
                
            merged_elements.append(merged)
        
        # Add unmatched HTML elements
        for elem in self.unmatched_html:
            elem_copy = elem.copy()
            elem_copy["source"] = "html_only"
            elem_copy["match_confidence"] = 0
            merged_elements.append(elem_copy)
        
        # Add unmatched LLM elements but convert their types to HTML format
        for elem in self.unmatched_llm:
            element_type = elem.get("Element_Type", "") or ""
            element_text = elem.get("Element_Text", "") or ""
            
            merged = {
                "tag": self._map_llm_type_to_html_tag(element_type),
                "type": self._map_llm_type_to_html_type(element_type),
                "name": "",
                "id": "",
                "placeholder": element_text,
                "label": element_text,
                "visual_text": element_text,
                "visual_type": element_type,  # Original LLM type for reference
                "visual_status": elem.get("Element_Status", ""),
                "visual_value": elem.get("Element_Value", ""),
                "source": "llm_only",
                "match_confidence": 0,
                "required": "*" in element_text
            }
            merged_elements.append(merged)
        
        return merged_elements
    
    def _map_llm_type_to_html_tag(self, llm_type: str) -> str:
        """
        Map LLM element type to HTML tag
        
        Args:
            llm_type: Element type from LLM
            
        Returns:
            Corresponding HTML tag
        """
        if llm_type is None:
            return "input"
            
        llm_type = llm_type.lower() if isinstance(llm_type, str) else ""
        
        type_mapping = {
            "textbox": "input",
            "text field": "input",
            "text": "input",
            "field": "input",
            "input": "input",
            "button": "button",
            "checkbox": "input",
            "check": "input",
            "checkmark": "input",
            "tick": "input",
            "radio": "input",
            "radio button": "input",
            "select": "select",
            "dropdown": "select",
            "option": "select",
            "menu": "select",
            "textarea": "textarea",
            "text area": "textarea",
            "multiline": "textarea",
            "file": "input",
            "upload": "input",
            "attachment": "input"
        }
        return type_mapping.get(llm_type, "input")
    
    def _map_llm_type_to_html_type(self, llm_type: str) -> str:
        """
        Map LLM element type to HTML input type attribute
        
        Args:
            llm_type: Element type from LLM
            
        Returns:
            Corresponding HTML input type
        """
        if llm_type is None:
            return "text"
            
        llm_type = llm_type.lower() if isinstance(llm_type, str) else ""
        
        type_mapping = {
            "textbox": "text",
            "text field": "text",
            "text": "text",
            "field": "text",
            "input": "text",
            "button": "submit",
            "checkbox": "checkbox",
            "check": "checkbox",
            "checkmark": "checkbox",
            "tick": "checkbox",
            "radio": "radio",
            "radio button": "radio",
            "select": None,
            "dropdown": None,
            "option": None,
            "menu": None,
            "textarea": None,
            "text area": None,
            "multiline": None,
            "file": "file",
            "upload": "file",
            "attachment": "file"
        }
        return type_mapping.get(llm_type, "text")
    
    def extract_static_texts(self) -> List[str]:
        """
        Extract text content from LLM's STATIC_TEXT elements
        
        Returns:
            List of static text strings
        """
        static_texts = []
        
        for elem in self.llm_elements:
            if elem.get("Element_Type") == "STATIC_TEXT" and elem.get("Element_Text"):
                static_texts.append(elem.get("Element_Text"))
                
        return static_texts
    
    def generate_final_form(self, html_form_data: Dict) -> Dict:
        """
        Generate the final form representation with HTML elements as the source of truth for types
        Integrate LLM-detected static text into text_content if not already present
        
        Args:
            html_form_data: Original HTML form data that includes text_content
            
        Returns:
            Complete form representation
        """
        # Process all elements first
        merged_elements = self.generate_merged_elements()
        
        # Extract static text from LLM
        llm_static_texts = self.extract_static_texts()
        
        # Get existing text_content from HTML form
        existing_text_content = html_form_data.get("text_content", [])
        
        # Combine text content, avoiding duplicates
        existing_text_set = set()
        if isinstance(existing_text_content, list):
            for item in existing_text_content:
                if isinstance(item, str):
                    existing_text_set.add(item.lower())
        
        # Add new static text that isn't already in text_content
        combined_text_content = existing_text_content.copy() if isinstance(existing_text_content, list) else []
        for text in llm_static_texts:
            if text.lower() not in existing_text_set:
                combined_text_content.append(text)
                existing_text_set.add(text.lower())
        
        # Create final form structure
        final_form = {
            "id": html_form_data.get("id", ""),
            "method": html_form_data.get("method", ""),
            "action": html_form_data.get("action", ""),
            "fields": merged_elements,
            "text_content": combined_text_content,  # Combined text content
            "surrounding_text": html_form_data.get("surrounding_text", []),
            "stats": {
                "total_html_elements": len(self.html_elements),
                "total_llm_elements": len([e for e in self.llm_elements if e.get("Element_Type") != "STATIC_TEXT"]),
                "matched_elements": len(self.matched_pairs),
                "unmatched_html": len(self.unmatched_html),
                "unmatched_llm": len(self.unmatched_llm),
                "static_text_count": len(llm_static_texts)
            }
        }
        
        return final_form


def process_form_data(html_form_data, llm_elements, match_info=None):
    """
    Process form data and return matching and merging results
    
    Args:
        html_form_data: Form data extracted from HTML
        llm_elements: Form elements from LLM
        match_info: Optional matching information for this form
        
    Returns:
        Dictionary with processing results
    """
    # Extract HTML elements
    html_elements = html_form_data.get("fields", [])
    
    # Create matcher
    matcher = ElementMatcher(html_elements, llm_elements)
    
    # Match elements
    matcher.match_elements()
    
    # Generate final form
    final_form = matcher.generate_final_form(html_form_data)
    
    # Add form matching information
    if match_info:
        final_form.update({
            "form_match_info": {
                "source": match_info.get("source", "unknown"),
                "match_score": match_info.get("match_score", 0),
                "html_form_index": match_info.get("html_form_index"),
                "llm_form_key": match_info.get("llm_form_key"),
                "match_status": match_info.get("match_status", "unknown")
            }
        })
    
    return final_form


def _calculate_form_similarity(html_form: Dict, llm_form: List[Dict]) -> float:
    """
    Calculate similarity score between an HTML form and LLM form
    
    Args:
        html_form: HTML form data
        llm_form: LLM form elements
        
    Returns:
        Similarity score (0-1)
    """
    score = 0
    total_matches = 0
    html_fields = html_form.get('fields', [])
    
    # Skip static text elements from LLM form
    llm_fields = [elem for elem in llm_form if elem.get("Element_Type") != "STATIC_TEXT"]
    
    if not html_fields or not llm_fields:
        return 0
    
    # Compare each HTML field with LLM fields
    for html_field in html_fields:
        for llm_field in llm_fields:
            # Use existing similarity calculation
            matcher = ElementMatcher([], [])
            similarity = matcher._calculate_comprehensive_similarity(html_field, llm_field)
            if similarity > 0.35:  # Using same threshold as element matching
                total_matches += 1
                break
    
    # Calculate final score based on matched fields ratio
    if html_fields and llm_fields:
        score = total_matches / max(len(html_fields), len(llm_fields))
    
    return score

def find_best_form_matches(html_forms: List[Dict], llm_forms: Dict) -> List[Dict]:
    """
    Find best matching pairs between HTML and LLM forms using a greedy approach
    
    Args:
        html_forms: List of HTML forms
        llm_forms: Dictionary of LLM forms
        
    Returns:
        List of matched pairs with scores
    """
    matches = []
    used_llm_keys = set()
    
    # Create similarity matrix
    for html_idx, html_form in enumerate(html_forms):
        form_matches = []
        for llm_key, llm_form in llm_forms.items():
            if llm_key not in used_llm_keys:
                similarity = _calculate_form_similarity(html_form, llm_form)
                if similarity > 0.35:  # Threshold for considering a match
                    form_matches.append({
                        'html_idx': html_idx,
                        'llm_key': llm_key,
                        'score': similarity
                    })
        
        # Sort matches by score and take the best one
        if form_matches:
            best_match = max(form_matches, key=lambda x: x['score'])
            matches.append(best_match)
            used_llm_keys.add(best_match['llm_key'])
    
    return matches

def aligned_form(html_form_data, llm_form_data):
    results = []
    html_forms = html_form_data.get('forms', [])
    best_matches = find_best_form_matches(html_forms, llm_form_data)

    processed_html_indices = set()
    processed_llm_keys = set()
        
    # Process matched forms first
    for match in best_matches:
        html_idx = match['html_idx']
        llm_key = match['llm_key']
            
        match_info = {
            "source": "matched",
            "match_score": match['score'],
            "html_form_index": html_idx,
            "llm_form_key": llm_key,
            "match_status": "best_match" if match['score'] > 0.6 else "partial_match"
        }
            
        result = process_form_data(
            html_forms[html_idx], 
            llm_form_data[llm_key],
            match_info
        )
        results.append(result)
            
        processed_html_indices.add(html_idx)
        processed_llm_keys.add(llm_key)
    
    # Process remaining unmatched HTML forms
    for idx, html_form in enumerate(html_forms):
        if idx not in processed_html_indices:
            match_info = {
                "source": "html_only",
                "match_score": 0,
                "html_form_index": idx,
                "llm_form_key": None,
                "match_status": "no_llm_match"
            }
            
            result = process_form_data(
                html_form,
                [],  # Empty LLM elements
                match_info
            )
            results.append(result)
    
    # Process remaining unmatched LLM forms
    for llm_key, llm_form in llm_form_data.items():
        if llm_key not in processed_llm_keys:
            match_info = {
                "source": "llm_only",
                "match_score": 0,
                "html_form_index": None,
                "llm_form_key": llm_key,
                "match_status": "no_html_match"
            }
            
            empty_html_form = {
                "id": "",
                "method": "",
                "action": "",
                "fields": [],
                "text_content": [],
                "surrounding_text": []
            }
            
            result = process_form_data(
                empty_html_form,
                llm_form,
                match_info
            )
            results.append(result)
    
    # Sort results
    results.sort(key=lambda x: (
        0 if x.get("form_match_info", {}).get("source") == "matched" 
        else (1 if x.get("form_match_info", {}).get("source") == "html_only" else 2),
        x.get("form_match_info", {}).get("html_form_index", float('inf')),
        x.get("form_match_info", {}).get("llm_form_key", "")
    ))
       
    return results

def main():
    try:
        with open("./tests/form_3/html_form_data.json", "r", encoding="utf-8") as f:
            html_form_data = json.load(f)
        
        with open("./tests/form_3/llm_form_data.json", "r", encoding="utf-8") as f:
            llm_form_data = json.load(f)
        
        results = []
        html_forms = html_form_data.get('forms', [])
        
        # Find best matches between HTML and LLM forms
        best_matches = find_best_form_matches(html_forms, llm_form_data)
        processed_html_indices = set()
        processed_llm_keys = set()
        
        # Process matched forms first
        for match in best_matches:
            html_idx = match['html_idx']
            llm_key = match['llm_key']
            
            match_info = {
                "source": "matched",
                "match_score": match['score'],
                "html_form_index": html_idx,
                "llm_form_key": llm_key,
                "match_status": "best_match" if match['score'] > 0.6 else "partial_match"
            }
            
            result = process_form_data(
                html_forms[html_idx], 
                llm_form_data[llm_key],
                match_info
            )
            results.append(result)
            
            processed_html_indices.add(html_idx)
            processed_llm_keys.add(llm_key)
        
        # Process remaining unmatched HTML forms
        for idx, html_form in enumerate(html_forms):
            if idx not in processed_html_indices:
                match_info = {
                    "source": "html_only",
                    "match_score": 0,
                    "html_form_index": idx,
                    "llm_form_key": None,
                    "match_status": "no_llm_match"
                }
                
                result = process_form_data(
                    html_form,
                    [],  # Empty LLM elements
                    match_info
                )
                results.append(result)
        
        # Process remaining unmatched LLM forms
        for llm_key, llm_form in llm_form_data.items():
            if llm_key not in processed_llm_keys:
                match_info = {
                    "source": "llm_only",
                    "match_score": 0,
                    "html_form_index": None,
                    "llm_form_key": llm_key,
                    "match_status": "no_html_match"
                }
                
                # Create empty HTML form structure
                empty_html_form = {
                    "id": "",
                    "method": "",
                    "action": "",
                    "fields": [],
                    "text_content": [],
                    "surrounding_text": []
                }
                
                result = process_form_data(
                    empty_html_form,
                    llm_form,
                    match_info
                )
                results.append(result)
        
        # Sort results by source type and indices/keys
        results.sort(key=lambda x: (
            0 if x.get("form_match_info", {}).get("source") == "matched" 
            else (1 if x.get("form_match_info", {}).get("source") == "html_only" else 2),
            x.get("form_match_info", {}).get("html_form_index", float('inf')),
            x.get("form_match_info", {}).get("llm_form_key", "")
        ))
        
        with open("./tests/form_3/aligned_form_data.json", "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        # Print all results
        # for idx, result in enumerate(results):
        #     print(f"\nForm {idx + 1}:")
        #     match_info = result.get("form_match_info", {})
        #     print(f"Match Status: {match_info.get('match_status')}")
        #     print(f"Source: {match_info.get('source')}")
        #     if match_info.get('match_score') > 0:
        #         print(f"Match Score: {match_info.get('match_score'):.2f}")
        #     print(json.dumps(result, indent=2, ensure_ascii=False))
            
        # print("\nProcessing complete")
        
    except Exception as e:
        print(f"Error: {e}")


def test_with_example():
    # HTML form data example (based on your provided format)
    html_form_data = [{
            "id": "",
            "method": "post",
            "action": "/#wpcf7-f387-p1471-o1",
            "fields": [
                {
                    "tag": "input",
                    "name": "your-name",
                    "type": "text",
                    "id": "",
                    "placeholder": "Your Name",
                    "required": False,
                    "class": [
                        "wpcf7-form-control",
                        "wpcf7-text",
                        "wpcf7-validates-as-required",
                        "input-border"
                    ],
                    "disabled": False,
                    "label": ""
                },
                {
                    "tag": "input",
                    "name": "your-email",
                    "type": "email",
                    "id": "",
                    "placeholder": "Your Email",
                    "required": False,
                    "class": [
                        "wpcf7-form-control",
                        "wpcf7-text",
                        "wpcf7-email",
                        "wpcf7-validates-as-required",
                        "wpcf7-validates-as-email",
                        "input-border"
                    ],
                    "disabled": False,
                    "label": ""
                },
                {
                    "tag": "input",
                    "name": "your-website",
                    "type": "text",
                    "id": "",
                    "placeholder": "Your Website",
                    "required": False,
                    "class": [
                        "wpcf7-form-control",
                        "wpcf7-text",
                        "wpcf7-validates-as-required",
                        "input-border"
                    ],
                    "disabled": False,
                    "label": ""
                },
                {
                    "tag": "textarea",
                    "name": "your-message",
                    "type": None,
                    "id": "",
                    "placeholder": "Your Message",
                    "required": False,
                    "class": [
                        "wpcf7-form-control",
                        "wpcf7-textarea",
                        "input-border",
                        "txtarea"
                    ],
                    "disabled": False,
                    "label": ""
                },
                {
                    "tag": "button",
                    "name": "",
                    "type": "submit",
                    "id": "",
                    "placeholder": "",
                    "required": False,
                    "class": [
                        "btn"
                    ],
                    "disabled": False,
                    "text": "Submit",
                    "label": ""
                },
                {
                    "tag": "textarea",
                    "name": "_wpcf7_ak_hp_textarea",
                    "type": None,
                    "id": "",
                    "placeholder": "",
                    "required": False,
                    "class": [],
                    "disabled": False,
                    "label": ""
                }
            ]
    }]
    
    # LLM form data example (based on your provided format)
    llm_form_data = {
       "Form1": [
                {
                    "Element_Type": "STATIC_TEXT",
                    "Element_Text": "Get In Touch"
                },
                {
                    "Element_Type": "STATIC_TEXT",
                    "Element_Text": "Request your account for free or ask any question. Reach out to us and we'll get back to you shortly."
                },
                {
                    "Element_Type": "textbox",
                    "Element_Text": "Your Name",
                    "Element_Status": "empty",
                    "Element_Value": ""
                },
                {
                    "Element_Type": "textbox",
                    "Element_Text": "Your Email",
                    "Element_Status": "empty",
                    "Element_Value": ""
                },
                {
                    "Element_Type": "textbox",
                    "Element_Text": "Your Website",
                    "Element_Status": "empty",
                    "Element_Value": ""
                },
                {
                    "Element_Type": "textbox",
                    "Element_Text": "Your Message",
                    "Element_Status": "empty",
                    "Element_Value": ""
                },
                {
                    "Element_Type": "button",
                    "Element_Text": "SUBMIT",
                    "Element_Status": "active",
                    "icon": "submit_icon"
                }
        ]
    }
    
    html_form_data = {
        'forms': html_form_data  # Wrap the list in a dictionary with 'forms' key
    }
    
    results = []
    html_forms = html_form_data.get('forms', [])
    
    # Find best matches between HTML and LLM forms
    best_matches = find_best_form_matches(html_forms, llm_form_data)
    processed_html_indices = set()
    processed_llm_keys = set()
    
    # Use the same matching logic as main()
    # ... (copy the matching logic from main() here)
    
    # Print results
    for idx, result in enumerate(results):
        print(f"\nForm {idx + 1}:")
        match_info = result.get("form_match_info", {})
        print(f"Match Status: {match_info.get('match_status')}")
        print(f"Source: {match_info.get('source')}")
        if match_info.get('match_score') > 0:
            print(f"Match Score: {match_info.get('match_score'):.2f}")
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # If files don't exist, run test example
    RESULTS_FOLDER = "/home/ying/projects/web_navigation/webarena/results_test/"
    website_folder = os.listdir(RESULTS_FOLDER)
    # website_folder = ["www_metrixlab_com"]
    for website in tqdm(website_folder):
        form_info_folder = os.path.join(RESULTS_FOLDER, website, "form_info")
        if not os.path.exists(form_info_folder):
            continue
        form_info_files = os.listdir(form_info_folder)
        for form_info_file in form_info_files:
            if form_info_file.endswith(".json"):
                form_info_path = os.path.join(form_info_folder, form_info_file)
                form_info_data = json.load(open(form_info_path, "r"))
                image = form_info_data['image']
                merged_data_folder = os.path.join(RESULTS_FOLDER, website, "merged_images", image)
                merged_data_file = os.path.join(merged_data_folder, "merged_forms.json")
                if not os.path.exists(merged_data_file):
                    with open("error_form_alignment.txt", "a") as f:
                        f.write(merged_data_file + '\n')
                    continue
                merged_data = json.load(open(merged_data_file, "r"))
                aligned_data = aligned_form(form_info_data, merged_data)
                save_data = {"forms": aligned_data, "url": form_info_data['url'], "image": image}
                with open(os.path.join(merged_data_folder, "aligned_form_data.json"), "w") as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)
                # print(aligned_data)
    #     if not (os.path.exists(f"{RESULTS_FOLDER}/{folder}/form_info/form_0.json") and os.path.exists(f"{RESULTS_FOLDER}/{folder}/form_info/form_1.json")):
    #         print("Input files not found, testing with example data...")
    #         test_with_example()
    # else:
    #     main()