#!/usr/bin/env python3
"""
Batch processor for multiple domains from CSV file
"""

import csv
import json
import argparse
import os
from website_parser import WebsiteParser
from config import PrivacyPolicyConfig, DEFAULT_CONFIG

def process_domains_csv(csv_file, output_file="batch_results.json", config=None):
    """Process multiple domains from CSV file with incremental saving"""
    parser = WebsiteParser(config or DEFAULT_CONFIG)
    
    # Clear output file at start
    with open(output_file, 'w') as f:
        pass  # Create empty file
    
    print(f"Processing domains from {csv_file}...")
    print(f"Output will be saved incrementally to {output_file}")
    print("-" * 50)
    
    # Initialize counters
    successful = 0
    failed = 0
    total_links = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total_domains = sum(1 for row in reader)
        f.seek(0)  # Reset file pointer
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader, 1):
            domain = row['domain'].strip()
            
            # Add https:// if not present
            if not domain.startswith('http'):
                url = f"https://{domain}"
            else:
                url = domain
                
            print(f"[{i}/{total_domains}] Processing {domain}...")
            
            # Process domain
            try:
                links = parser.parse(url)
                result = {
                    'url': url,
                    'potential_privacy_policy_links': links,
                    'status': 'success',
                    'links_count': len(links)
                }
                successful += 1
                total_links += len(links)
                print(f"  ✓ Found {len(links)} privacy policy links")
            except Exception as e:
                result = {
                    'url': url,
                    'potential_privacy_policy_links': [],
                    'status': 'error',
                    'error': str(e),
                    'links_count': 0
                }
                failed += 1
                print(f"  ✗ Error: {str(e)}")
            
            # Save result immediately (append to file)
            save_single_result(domain, result, output_file)
    
    # Print final summary
    print("-" * 50)
    print(f"Batch processing completed!")
    print(f"Successful: {successful}/{total_domains}")
    print(f"Failed: {failed}/{total_domains}")
    print(f"Total privacy policy links found: {total_links}")
    print(f"Results saved incrementally to {output_file}")


def save_single_result(domain, result, output_file):
    """Save a single domain result to the output file"""
    # Create the result entry with the desired format
    single_result = {
        "url": result['url'],
        "potential_privacy_policy_links": result['potential_privacy_policy_links']
    }
    
    # Append to file (one JSON object per line)
    with open(output_file, 'a', encoding='utf-8') as f:
        json.dump(single_result, f, ensure_ascii=False)
        f.write('\n')  # Add newline for readability


def read_incremental_results(output_file):
    """Read results from incrementally saved file"""
    results = []
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    result = json.loads(line)
                    results.append(result)
    except FileNotFoundError:
        print(f"Output file {output_file} not found.")
    except json.JSONDecodeError as e:
        print(f"Error reading JSON from {output_file}: {e}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Batch process multiple domains from CSV file'
    )
    parser.add_argument(
        'csv_file',
        help='CSV file containing domains to process'
    )
    parser.add_argument(
        '--output',
        default='batch_results.json',
        help='Output JSON file for results (default: batch_results.json)'
    )
    parser.add_argument(
        '--config',
        help='Configuration file path'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' not found!")
        print("Please provide a valid CSV file with 'domain' column.")
        exit(1)
    
    # Load configuration if provided
    config = None
    if args.config:
        config = PrivacyPolicyConfig.from_file(args.config)
    
    # Process domains
    process_domains_csv(args.csv_file, args.output, config)
