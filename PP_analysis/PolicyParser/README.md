# Privacy Policy Parser

A Python toolset for extracting privacy policy links from websites and downloading privacy policy documents.


## Project Structure

```
PolicyParser/
├── code/
│   ├── website_parser.py      # Website parser
│   ├── batch_processor.py     # Batch processor
│   ├── pp_download.py         # Privacy policy downloader
│   ├── config.py              # Configuration file
│   └── config_example.json    # Configuration example
├── data/
│   └── new_pp/                # Downloaded privacy policy files
└── webdriver/
    └── firefox/               # Firefox browser files
```

## Quick Start

### 0. Download Dependency
wget -O firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US"

tar -xjf firefox.tar.bz2


wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz

tar -xzf geckodriver-v0.34.0-linux64.tar.gz


### 1. Extract Privacy Policy Links
```bash
# Single website
python3 website_parser.py https://example.com --output results.json

# Batch processing
python3 batch_processor.py domains.csv --output batch_results.json
```

### 4. Download Privacy Policy Documents
```bash
python3 pp_download.py --input batch_results.json
```

That's it! Your privacy policy documents will be organized in domain-specific folders under `../data/new_pp/`.

## Installation

### Prerequisites
- Firefox browser
- geckodriver

### Install Dependencies
```bash
pip install selenium beautifulsoup4 requests polipy
```

## Configuration

### 1. Firefox Setup
Ensure Firefox browser and geckodriver paths are correct:

```python
# In config.py
firefox_binary_path: str = "/path/to/firefox"
geckodriver_path: str = "/path/to/geckodriver"
```

### 2. Output Configuration
```python
output_dir: str = "../data/new_pp"  # Output directory
enable_screenshots: bool = True     # Enable screenshots
```

## Usage

### 1. Single Website Parsing

```bash
python3 website_parser.py https://example.com --output results.json
```

### 2. Batch Processing Multiple Domains

Create a CSV file `domains.csv`:
```csv
domain
google.com
example.com
test.org
```

Run batch processing:
```bash
```

### 3. Download Privacy Policy Documents

```bash
python3 pp_download.py --input batch_results.json --output-dir ./downloads
```

## Output Formats

### Single Website Parsing Output
```json
{
  "url": "https://example.com",
  "potential_privacy_policy_links": [
    "https://example.com/privacy",
    "https://example.com/privacy-policy"
  ]
}
```

### Batch Processing Output (JSONL Format)
One JSON object per line:
```json
{"url": "https://google.com", "potential_privacy_policy_links": ["https://policies.google.com/privacy", "https://policies.google.com/terms"]}
{"url": "https://example.com", "potential_privacy_policy_links": ["/privacy", "/privacy-policy"]}
```


## Configuration Parameters

### WebDriver Configuration
- `firefox_binary_path`: Firefox browser path
- `geckodriver_path`: geckodriver path
- `headless`: Run in headless mode
- `user_agent`: User agent string
- `wait_time`: Page load wait time

### Parser Configuration
- `timeout`: HTTP request timeout
- `max_tokens`: Maximum token count for privacy link text
- `popup_max_tokens`: Maximum token count for popup privacy link text
- `retry_attempts`: Number of retry attempts

### Proxy Configuration
- `enabled`: Enable proxy
- `http_proxy`: HTTP proxy address
- `https_proxy`: HTTPS proxy address

## Advanced Usage

### Using Custom Configuration
```bash
python3 website_parser.py https://example.com --config custom_config.json
```

### Batch Processing with Configuration
```bash
python3 batch_processor.py domains.csv --config custom_config.json --output results.json
```

### Download to Specific Directory
```bash
python3 pp_download.py --input results.json --output-dir /path/to/downloads
```