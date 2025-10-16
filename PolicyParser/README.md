# Privacy Policy Parser

A Python toolset for extracting privacy policy links from websites and downloading privacy policy documents for consent analysis and RAG-based processing.

## Overview

This tool is designed to collect privacy policies for large-scale analysis of consent mechanisms. Privacy policies are typically lengthy documents that would be computationally expensive to process entirely with LLMs. Therefore, we use Retrieval Augmented Generation (RAG) to extract consent-related content. Specifically, we construct a knowledge base by embedding the collected privacy policies and indexing them into a vector database.

## Features

- 🔍 **Smart Link Extraction**: Uses Selenium WebDriver and BeautifulSoup to extract privacy policy links from websites
- 📁 **Batch Processing**: Supports batch processing of multiple domains from CSV files
- 💾 **Incremental Saving**: Saves results immediately after processing each domain to prevent data loss
- 📥 **Document Download**: Uses polipy library to download privacy policy documents
- 🗂️ **Auto Organization**: Creates subfolders by domain for easy file management
- ⚙️ **Flexible Configuration**: Supports JSON configuration files with customizable parameters

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

### 1. Install Dependencies
```bash
pip install selenium beautifulsoup4 requests polipy
```

### 2. Download Firefox and geckodriver
- Download Firefox browser
- Download geckodriver from [GitHub releases](https://github.com/mozilla/geckodriver/releases)
- Extract and place geckodriver in your PATH or update the path in `config.py`

### 3. Extract Privacy Policy Links
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
python3 batch_processor.py domains.csv --output batch_results.json
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

## Privacy Policy Terminology

The parser identifies privacy policy links using multiple terminologies to ensure comprehensive coverage:

- **"privacy policy"** - Most common terminology
- **"privacy statement"** - Alternative formal terminology  
- **"privacy notice"** - Legal/regulatory terminology
- **"data protection"** - GDPR-specific terminology
- **"terms"** - Often contains privacy-related content

## RAG-Based Consent Analysis

### Purpose
Privacy policies are typically lengthy documents that would be computationally expensive to process entirely with LLMs. This tool prepares documents for Retrieval Augmented Generation (RAG) analysis.

### Process
1. **Collection**: Extract and download privacy policy documents
2. **Embedding**: Convert documents to vector embeddings
3. **Indexing**: Store embeddings in a vector database
4. **Querying**: Use diverse prompts to extract consent-related information

### Consent Dimensions Covered
The RAG system uses diverse prompts to cover multiple consent dimensions:

- **"what user actions are required to give consent"**
- **"how users can withdraw consent"** 
- **"whether consent is cited as a legal basis"**
- **"for what purposes consent is requested"**

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

## License

This project is licensed under the MIT License.

## Contributing

Issues and Pull Requests are welcome to improve this project.

## Changelog

- **v1.0.0**: Initial version with basic privacy policy link extraction
- **v1.1.0**: Added batch processing functionality
- **v1.2.0**: Added incremental saving and JSONL format support
- **v1.3.0**: Added domain-based file organization for downloads

## Support

For questions or issues, please open an issue on the project repository.


