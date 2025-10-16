import openai
import re
import json
import os
import argparse
from tqdm import tqdm
from pathlib import Path

SYSTEM_PROMPT = """
Task: Extract all distinct purposes **for which consent** is requested.

Given a sentence that may request user consent, extract all distinct purposes for which consent is requested. For each purpose, extract a short phrase quoted directly from the original sentence, retaining the verb + object structure.

Instructions:

- For each purpose, extract a short phrase quoted directly from the original sentence, retaining the verb + object structure (e.g., "agree to the Terms of Use").

- Do not infer or paraphrase—only use phrases explicitly stated in the sentence.

- Exclude generic consent-granting expressions such as "give my consent to...", "consent to...", "I hereby consent...", "I allow...", "I authorize..."

- For phrases like "process your data for X", only extract X as the purpose (e.g., "provide you the content requested").

- If multiple purposes are present, list each as a separate entry.

- If no explicit purpose is found, return an empty list.

Input format: Single consent request sentence 
Output format: {"purpose": ["<purpose 1>", "<purpose 2>", ...]} 
Please only reply the formatted json without any other text.
"""

def extract_answer(response):
    # Find pattern matching {"purpose": [...]} or {"purpose": "..."}
    pattern = r'{"purpose":\s*(\[.*?\]|".*?")}' 
    matches = re.finditer(pattern, response)
    
    # Get the last match
    last_match = None
    for match in matches:
        last_match = match
    
    if last_match:
        try:
            # Parse the matched JSON string
            return json.loads(last_match.group(0))
        except json.JSONDecodeError:
            return {"purpose": []}
    
    return {"purpose": []}

def chat_with_gpt4o_mini(input_text, api_key=None):
    """Chat with GPT-4o-mini using OpenAI API"""
    if api_key:
        client = openai.OpenAI(api_key=api_key)
    else:
        client = openai.OpenAI()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": input_text},
            ],
            temperature=0.1
        )
        return extract_answer(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {"purpose": []}

def extract_sentences_from_consent_results(consent_data):
    """Extract all sentences from consent_rag_results.json format"""
    sentences = []
    
    # Extract sentences from all consent dimensions
    for dimension_name, dimension_data in consent_data.get("consent_dimensions", {}).items():
        if "retrieved_sentences" in dimension_data:
            for sentence_data in dimension_data["retrieved_sentences"]:
                sentences.append({
                    "sentence": sentence_data["sentence"],
                    "source": sentence_data.get("source", ""),
                    "dimension": dimension_name,
                    "relevance_score": sentence_data.get("relevance_score", 0.0)
                })
    
    return sentences

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Extract purposes from consent sentences using GPT-4o-mini")
    parser.add_argument(
        "--input-dir", 
        type=str, 
        help="Input directory containing policy directories with consent_rag_results.json files"
    )
    parser.add_argument(
        "--specific", 
        type=str, 
        help="Process a specific policy directory instead of all directories"
    )
    parser.add_argument(
        "--api-key", 
        type=str, 
        help="OpenAI API key (optional, can also use OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="purpose_extracted.json",
        help="Output filename (default: purpose_extracted.json)"
    )
    return parser.parse_args()

def process_single_policy(policy_path, api_key, output_filename):
    """Process a single policy directory"""
    purposes = []
    consent_file = "consent_rag_results.json"
    
    # Skip if purpose already extracted
    if os.path.exists(os.path.join(policy_path, output_filename)):
        print(f"Purpose already extracted in {policy_path}, skipping...")
        return True
    
    # Skip if consent file doesn't exist
    if not os.path.exists(os.path.join(policy_path, consent_file)):
        print(f"No consent_rag_results.json found in {policy_path}, skipping...")
        return False
    
    try:
        with open(os.path.join(policy_path, consent_file), 'r', encoding='utf-8') as f:
            consent_data = json.load(f)
    except Exception as e:
        print(f"Error loading consent data from {policy_path}: {e}")
        return False
    
    # Extract sentences from consent_rag_results.json
    sentences_data = extract_sentences_from_consent_results(consent_data)
    
    if not sentences_data:
        print(f"No consent sentences found in {policy_path}")
        return False
    
    print(f"Processing {len(sentences_data)} consent sentences in {policy_path}")
    
    for sentence_data in sentences_data:
        tmp_dict = {
            "sentence": sentence_data["sentence"],
            "source": sentence_data["source"],
            "dimension": sentence_data["dimension"],
            "relevance_score": sentence_data["relevance_score"]
        }
        result = chat_with_gpt4o_mini(sentence_data["sentence"], api_key)
        tmp_dict["purpose"] = result["purpose"]
        purposes.append(tmp_dict)
    
    # Save results
    output_file = os.path.join(policy_path, output_filename)
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(purposes, f, ensure_ascii=False, indent=2)
    print(f"Saved purpose extraction results to {output_file}")
    return True

def main():
    args = parse_arguments()
    
    # Set your OpenAI API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable or use --api-key argument")
        return
    
    if args.specific:
        # Process specific policy directory
        policy_path = Path(args.specific)
        if not policy_path.exists():
            print(f"Policy directory not found: {policy_path}")
            return
        
        print(f"Processing specific policy directory: {policy_path}")
        success = process_single_policy(policy_path, api_key, args.output)
        if success:
            print("Purpose extraction completed successfully!")
        else:
            print("Purpose extraction failed!")
    
    elif args.input_dir:
        # Process all policy directories in input directory
        input_dir = Path(args.input_dir)
        if not input_dir.exists():
            print(f"Input directory not found: {input_dir}")
            return
        
        print(f"Processing all policy directories in: {input_dir}")
        
        # Find all policy directories
        policy_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
        
        if not policy_dirs:
            print("No policy directories found in input directory")
            return
        
        successful = 0
        failed = 0
        
        for policy_dir in tqdm(policy_dirs, desc="Processing policy directories"):
            if process_single_policy(policy_dir, api_key, args.output):
                successful += 1
            else:
                failed += 1
        
        print(f"\nProcessing completed!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
    
    else:
        print("Please specify either --input-dir or --specific argument")
        print("Use --help for more information")

if __name__ == "__main__":
    main()
