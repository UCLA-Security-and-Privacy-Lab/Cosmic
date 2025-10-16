# Privacy Policy Processing and Consent Analysis 

## Quick Start

### One-Click Analysis
Use the automated script to process HTML files and analyze consent patterns:

```bash
# Navigate to the processing directory
cd ../../PP_analysis/consent_indentification/

# Process all policies for a domain (requires OpenAI API key)
python run_analysis.py \
  --input-dir /bigtemp/fr3ya/cosmic/PP_analysis/PolicyParser/data/new_pp/007_com/

# Process a specific policy
python run_analysis.py \
  --input-dir /bigtemp/fr3ya/cosmic/PP_analysis/PolicyParser/data/new_pp/007_com/ \
  --specific /bigtemp/fr3ya/cosmic/PP_analysis/PolicyParser/data/new_pp/007_com/www_007_com_3872553642/
```

### Manual Step-by-Step
If you prefer to run each step separately:

```bash
# Step 1: Convert HTML to Markdown
python html_policy_processor.py \
  --input-dir /bigtemp/fr3ya/cosmic/PP_analysis/PolicyParser/data/new_pp/007_com/

# Step 2: Analyze consent patterns (requires OpenAI API key)
export OPENAI_API_KEY="your-api-key-here"
python consent_rag_analyzer.py \
  --policy-file /bigtemp/fr3ya/cosmic/PP_analysis/PolicyParser/data/new_pp/007_com/www_007_com_3872553642/policy.md \
  --output consent_rag_results.json

# Step 3: Extract specific purposes from consent sentences (optional)
python extract_purpose.py \
  --specific /bigtemp/fr3ya/cosmic/PP_analysis/PolicyParser/data/new_pp/007_com/www_007_com_3872553642/
```

## Overview

Process privacy policy documents collected by the PolicyParser and converts them from HTML to Markdown format for consent analysis. It includes both HTML processing and RAG-based consent analysis capabilities.

## Directory Structure

```
PP_analysis/consent_indentification/
├── html_policy_processor.py     # HTML to Markdown converter
├── consent_rag_analyzer.py      # RAG-based consent analysis
├── extract_purpose.py           # Extract specific purposes from consent sentences
├── run_analysis.py              # One-click analysis pipeline
├── html2md.py                   # Original HTML to Markdown converter
├── markdown_process.py          # Original markdown processor
└── README.md                    # This file

PolicyParser/data/new_pp/        # Privacy policy data directory
├── domain1_com/                 # Domain directory
│   ├── policy_subdir1/          # Policy subdirectory
│   │   ├── policy.html          # HTML file
│   │   ├── policy.json          # Metadata
│   │   └── policy.md            # Generated Markdown (output)
│   └── policy_subdir2/
│       ├── policy.html
│       └── policy.md
└── domain2_com/
    └── ...
```

## Prerequisites

## Usage

### 1. HTML to Markdown Processing

#### Process All Policies in a Domain
```bash
# Navigate to the processing directory
cd ../../PP_analysis/consent_indentification/

# Process all policies for a specific domain
python html_policy_processor.py \
  --input-dir ../../PolicyParser/data/new_pp/007_com/
```

#### Process a Specific Policy
```bash
# Process only one specific policy subdirectory
python html_policy_processor.py \
  --input-dir ../../PolicyParser/data/new_pp/007_com/ \
  --specific ../../PolicyParser/data/new_pp/007_com/www_007_com_3872553642/
```

#### Process with Custom Output Directory
```bash
# Specify a different output directory
python html_policy_processor.py \
  --input-dir ../../PolicyParser/data/new_pp/007_com/ \
  --output-dir ../../processed_policies/007_com/
```

#### Force Overwrite Existing Files
```bash
# Overwrite existing policy.md files
python html_policy_processor.py \
  --input-dir ../../PolicyParser/data/new_pp/007_com/ \
  --force
```

### 2. Consent Analysis with RAG

#### Basic Consent Analysis
```bash
# Analyze consent patterns in a specific policy file
python consent_rag_analyzer.py \
  --policy-file ../../PolicyParser/data/new_pp/007_com/www_007_com_3872553642/policy.md \
  --output consent_rag_results.json
```

### 3. Purpose Extraction from Consent Sentences

#### Extract Purposes from Specific Policy
```bash
# Extract specific purposes from consent sentences in a policy directory
python extract_purpose.py \
  --specific /bigtemp/fr3ya/cosmic/PP_analysis/PolicyParser/data/new_pp/007_com/www_007_com_3872553642/
```

#### Extract Purposes from All Policies in a Domain
```bash
# Extract purposes from all policies in a domain
python extract_purpose.py \
  --input-dir /bigtemp/fr3ya/cosmic/PP_analysis/PolicyParser/data/new_pp/007_com/
```

#### Extract Purposes with Custom Output File
```bash
# Use custom output filename
python extract_purpose.py \
  --specific /path/to/policy/ \
  --output my_purposes.json
```

## Output

### HTML Processing Output
For each processed policy directory, the tool generates:
- `policy.md` - Converted Markdown file from HTML

### Consent Analysis Output
The RAG analyzer generates:
- `consent_rag_results.json`

### Purpose Extraction Output
The purpose extractor generates:
- `purpose_extracted.json` - Contains extracted purposes for each consent sentence

## Purpose Extraction Features

The `extract_purpose.py` script uses GPT-4o-mini to extract specific purposes from consent sentences:

### Input Requirements:
- Requires `consent_rag_results.json` files (generated by `consent_rag_analyzer.py`)
- Uses OpenAI API for purpose extraction

### Output Format:
```json
[
  {
    "sentence": "Users must provide consent for processing their data for marketing purposes",
    "source": "/path/to/policy.md",
    "dimension": "consent_actions",
    "relevance_score": 0.85,
    "purpose": ["marketing"]
  }
]
```

## Configuration

### Environment Variables
Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```
