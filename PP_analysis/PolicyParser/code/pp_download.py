import polipy
import argparse
from typing import Dict, List, Optional
import json
import os
from urllib.parse import urljoin, urlparse
from config import PrivacyPolicyConfig, DEFAULT_CONFIG

def read_privacy_policy_links(file_path):
    """Read privacy policy links from JSONL format (one JSON object per line)"""
    all_data = []  # Store both URL and links for each domain
    
    with open(file_path, "r", encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:  # Skip empty lines
                try:
                    result = json.loads(line)
                    all_data.append(result)
                    print(f"Line {line_num}: Found {len(result.get('potential_privacy_policy_links', []))} links from {result.get('url', 'unknown')}")
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON on line {line_num}: {e}")
                    continue
    
    print(f"Total domains collected: {len(all_data)}")
    return all_data

def download_privacy_policy_for_domain(domain_data, config: PrivacyPolicyConfig):
    """Download all privacy policy links for a specific domain using polipy"""
    domain_url = domain_data['url']
    links = domain_data.get('potential_privacy_policy_links', [])
    
    if not links:
        print(f"No privacy policy links found for {domain_url}")
        return 0
    
    # Create domain-specific folder
    parsed_url = urlparse(domain_url)
    domain_name = parsed_url.netloc.replace('www.', '').replace('.', '_')
    domain_folder = os.path.join(config.output.output_dir, domain_name)
    os.makedirs(domain_folder, exist_ok=True)
    
    print(f"Processing domain: {domain_url}")
    print(f"Domain folder: {domain_folder}")
    print(f"Found {len(links)} privacy policy links")
    
    successful_downloads = 0
    
    for i, link in enumerate(links, 1):
        try:
            # Use polipy to download the privacy policy
            url_result = polipy.get_policy(link, screenshot=config.output.enable_screenshots)
            
            # Save to domain-specific folder
            url_result.save(output_dir=domain_folder)
            
            print(f"  ✓ Downloaded {i}/{len(links)}: {link}")
            successful_downloads += 1
            
        except Exception as e:
            print(f"  ✗ Failed to download {link}: {str(e)}")
    
    print(f"Domain {domain_url}: {successful_downloads}/{len(links)} files downloaded")
    return successful_downloads

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Download privacy policy documents from extracted links'
    )
    parser.add_argument(
        '--input',
        type=str,
        default="privacy_policy_links.json",
        help='Input JSON file containing privacy policy links'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (JSON format)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for downloaded policies'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = PrivacyPolicyConfig.from_file(args.config)
    else:
        config = DEFAULT_CONFIG
    
    # Override output directory if specified
    if args.output_dir:
        config.output.output_dir = args.output_dir
    
    # Create main output directory if it doesn't exist
    os.makedirs(config.output.output_dir, exist_ok=True)
    
    # Read all domain data
    all_domains = read_privacy_policy_links(args.input)
    
    print(f"Found {len(all_domains)} domains to process")
    print(f"Main output directory: {config.output.output_dir}")
    print("-" * 60)
    
    total_successful = 0
    total_links = 0
    
    for i, domain_data in enumerate(all_domains, 1):
        print(f"\n[{i}/{len(all_domains)}] Processing domain...")
        successful = download_privacy_policy_for_domain(domain_data, config)
        total_successful += successful
        total_links += len(domain_data.get('potential_privacy_policy_links', []))
    
    print("\n" + "=" * 60)
    print(f"Download process completed!")
    print(f"Total domains processed: {len(all_domains)}")
    print(f"Total files downloaded: {total_successful}/{total_links}")
    print(f"Files organized in domain-specific folders under: {config.output.output_dir}")