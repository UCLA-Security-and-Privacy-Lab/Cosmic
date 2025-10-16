'''
This script is used to extract potential privacy policy links from a website.
'''


import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import time
import argparse
import json
from config import PrivacyPolicyConfig, DEFAULT_CONFIG

class WebsiteParser:
    def __init__(self, config: PrivacyPolicyConfig = None):
        self.config = config or DEFAULT_CONFIG
        
        # Firefox setup
        self.options = Options()
        self.options.binary_location = self.config.webdriver.firefox_binary_path
        if self.config.webdriver.headless:
            self.options.add_argument("--headless")
        self.user_agent = self.config.webdriver.user_agent
        self.options.add_argument(f"user-agent={self.user_agent}")
        self.service = Service(self.config.webdriver.geckodriver_path)
        self.driver = webdriver.Firefox(service=self.service, options=self.options)

        # Request settings
        self.proxies = self.config.proxy.proxies
        self.headers = {
            'User-Agent': self.user_agent
        }

       

    def parse(self, url, timeout=None):
        """Main method to parse website and find privacy links"""
        if not url.startswith("http"):
            url = "https://" + url

        timeout = timeout or self.config.parser.timeout
        privacy_links = []
        
        for attempt in range(self.config.parser.retry_attempts):
            try:
                # First attempt: Regular HTTP request
                privacy_links = self._parse_with_requests(url, timeout)
                
                # If no links found, try with Selenium
                if not privacy_links:
                    privacy_links = self._parse_with_selenium(url)
                
                if privacy_links:
                    break
                    
            except Exception as e:
                print(f"Error parsing {url} (attempt {attempt + 1}): {str(e)}")
                if attempt == self.config.parser.retry_attempts - 1:
                    print(f"All attempts failed for {url}")
            
        return list(set(privacy_links))

    def _parse_with_requests(self, url, timeout):
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout, proxies=self.proxies)
            if response.status_code == 200:
                return self._extract_privacy_links(response.text)
        except requests.exceptions.RequestException as e:
            print(f"Request failed for URL {url}: {str(e)}")
        return []

    def _parse_with_selenium(self, url):
        try:
            self.driver.get(url)
            time.sleep(self.config.webdriver.wait_time)
            return self._extract_privacy_links(self.driver.page_source)
        except Exception as e:
            print(f"Selenium parsing failed for URL {url}: {str(e)}")
        return []   
    
    def get_privacy_popup(self, url):
        """
        Specifically look for privacy links in popup content using Selenium
        """
        try:
            self.driver.get(url)
            time.sleep(self.config.webdriver.wait_time)
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            privacy_links = []
            
            for link in soup.find_all('a', href=True):
                text = link.get_text().lower().strip()
                tokens = text.split()
                if 'privacy' in tokens and len(tokens) < self.config.parser.popup_max_tokens:
                    privacy_links.append(link['href'])
                    
            return list(set(privacy_links))
        except Exception as e:
            print(f"Error in get_privacy_popup for URL {url}: {str(e)}")
            return []
    def _extract_privacy_links(self, html_content):
        privacy_links = []
        soup = BeautifulSoup(html_content, "html.parser")
        
        # First pass: English text
        for link in soup.find_all('a', href=True):
            text = link.get_text().lower().strip()
            tokens = text.split()
            if self._is_privacy_related(text, link['href']) and len(tokens) <= self.config.parser.max_tokens:
                privacy_links.append(link['href'])


        return privacy_links

    def _is_privacy_related(self, text, href):
        return ('privacy' in text or 
                href.endswith("privacy") or 
                'data protection' in text or 
                'terms' in text)

    def __del__(self):
        """Cleanup method"""
        if hasattr(self, 'driver'):
            self.driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extract privacy policy links from a website'
    )
    parser.add_argument(
        'url',
        type=str,
        help='The website URL to parse (e.g., www.google.com or https://www.google.com)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (JSON format)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default="privacy_policy_links.json",
        help='Output file path for privacy policy links'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = PrivacyPolicyConfig.from_file(args.config)
    else:
        config = DEFAULT_CONFIG
    
    website_parser = WebsiteParser(config)
    result = website_parser.parse(args.url)
    if len(result) == 0:
        result = website_parser.get_privacy_popup(args.url)

    save_dict = {}
    save_dict["url"] = args.url
    save_dict["potential_privacy_policy_links"] = result
    with open(args.output, "w") as f:
        json.dump(save_dict, f, indent=2)
    
    print(f"Found {len(result)} privacy policy links for {args.url}")
    print(f"Results saved to {args.output}")