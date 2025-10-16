# Web Form Extraction and Analysis Pipeline

This pipeline provides a comprehensive solution for extracting, analyzing, and processing web forms for compliance checking and accessibility analysis. The system combines multimodal form extraction with automated fact extraction and violation detection.

Note the webagent is modified based on WebArena.
## Overview

The pipeline consists of several interconnected components that work together to:

1. **Extract forms** from web pages using multimodal analysis (screenshots + HTML)
2. **Align form elements** between HTML structure and visual representation
3. **Extract facts** about form elements, consent requests, and data controllers
4. **Detect violations** using formal logic rules
5. **Generate compliance reports** and accessibility assessments

## Directory Structure

```
pipeline_integration/
├── run.py                          # Main pipeline runner
├── scripts/                        # Core processing scripts
│   ├── form_alignment.py          # Align HTML and visual form elements
│   ├── form2facts.py             # Extract facts from forms
│   ├── facts2dl.py                # Convert facts to datalog format
│   ├── violation_detect.py        # Detect compliance violations
│   ├── form_properies.py         # Extract form properties
│   ├── form_filtration.py        # Filter and deduplicate forms
│   ├── extract_iframe_info.py    # Extract iframe information
│   ├── deduplicate_forms.py      # Remove duplicate forms
│   └── ...                       # Additional utility scripts
└── form_operation_scripts/        # Form extraction and processing
    ├── multimodal_form_extraction.py  # Main multimodal extraction
    ├── extract_form_to_label.py       # Extract form labels
    ├── ocr_images.py                  # OCR processing
    └── ...                           # Additional form operations
```

## Quick Start

### Prerequisites

1. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY=your_api_key_here
```

2. Install required dependencies:
```bash
conda activate py310  
```

### Basic Usage

1. **Run the main pipeline:**
```bash
python run.py --config_dir /path/to/config --result_dir /path/to/results
```

2. **Extract forms from specific pages:**
```bash
cd scripts
python overall_pkl_select.py
```

3. **Perform multimodal form extraction:**
```bash
cd form_operation_scripts
python multimodal_form_extraction.py
```

## Detailed Pipeline Steps

### 1. Form Discovery and Selection

**Script:** `scripts/overall_pkl_select.py`

- Filters forms from navigation results
- Skips forms where the last action is "TYPE"
- Outputs `overall.pkl` with selected forms

### 2. Multimodal Form Extraction

**Script:** `form_operation_scripts/multimodal_form_extraction.py`

- Analyzes screenshots using GPT-4 Vision
- Extracts form elements, text, status, and icons
- Generates `overall.json` with structured form data
- Saves associated images for further processing

**Key Features:**
- Element type classification (textbox, button, checkbox, etc.)
- Text extraction from all form elements
- Status detection (active, empty, filled, checked, etc.)
- Icon identification and description

### 3. Form Alignment

**Script:** `scripts/form_alignment.py`

- Matches HTML elements with visually extracted elements
- Uses comprehensive similarity scoring
- Handles mismatches and missing elements
- Ensures data consistency between HTML and visual analysis

### 4. Form Properties Extraction

**Script:** `scripts/form_properies.py`

- Extracts detailed properties from form information
- Processes element types, text content, and status
- Handles different input types (text, email, tel, etc.)
- Outputs structured form properties

### 5. Facts Extraction

**Script:** `scripts/form2facts.py`

- Extracts consent request texts (CRT)
- Identifies data controllers
- Processes form elements and their attributes
- Generates structured facts for compliance analysis

**Key Fact Types:**
- **Consent Request Texts:** Identifies explicit consent requests
- **Data Controllers:** Extracts organization names or implicit references
- **Form Elements:** Processes element types, text, and status
- **Required Fields:** Identifies mandatory form fields

### 6. Facts to Datalog Conversion

**Script:** `scripts/facts2dl.py`

- Converts extracted facts to datalog format
- Prepares data for formal logic analysis
- Structures facts for violation detection

### 7. Violation Detection

**Script:** `scripts/violation_detect.py`

- Uses Soufflé datalog engine for formal analysis
- Applies compliance rules to detect violations
- Processes facts using `violation_rules.datalog`
- Generates violation reports

## Configuration

### Input Requirements

- **Config Directory:** Contains website configuration files
- **Result Directory:** Output location for processed results
- **Screenshots:** Form screenshots for multimodal analysis
- **HTML Data:** Form HTML structure and metadata

### Output Structure

```
results/
├── overall.json              # Extracted form data
├── overall_final.json        # Processed form data with properties
├── overall_final_with_link.json  # Form data with extracted links
├── facts/                    # Extracted facts directory
│   ├── element.facts         # Element facts
│   ├── crt.facts            # Consent request facts
│   └── ...
└── violations/              # Violation detection results
    └── ...
```

## Key Features

### Multimodal Analysis
- Combines visual and structural analysis
- Handles complex form layouts
- Extracts icons and visual elements
- Processes dynamic form states

### Compliance Checking
- GDPR compliance analysis
- Consent request detection
- Data controller identification
- Formal logic-based violation detection

### Accessibility Analysis
- Form element accessibility assessment
- Required field identification
- Form structure analysis
- User interaction pattern detection

### Robust Processing
- Handles duplicate forms
- Manages iframe content
- Processes various form types
- Error handling and recovery

