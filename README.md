# COSMIC: Automated Reasoning of GDPR Consent Violations

## Overview

COSMIC is a research platform that combines web automation and formal logic-based compliance checking to provide analysis of online consent mechanisms (target at webforms) and GDPR compliance. 

## Project Architecture

```
cosmic/
├── PolicyParser/           # Privacy policy collection and processing
├── PP_analysis/           # Privacy policy analysis and consent extraction
├── WebformExtraction/     # Web form extraction and analysis pipeline
└── ViolationReasoning/    # Formal logic-based violation detection
```

## Key Components

### 1. PolicyParser
**Purpose**: Automated collection and processing of privacy policies from websites

**Features**:
- 🔍 Smart link extraction using  WebDriver and BeautifulSoup
- 📁 Batch processing of multiple domains from CSV files
- 💾 Incremental saving to prevent data loss
- 📥 Document download using polipy library
- 🗂️ Auto-organization by domain for easy management

**Key Files**:
- `code/website_parser.py` - Website parser
- `code/batch_processor.py` - Batch processor
- `code/pp_download.py` - Privacy policy downloader

### 2. PP_analysis (Privacy Policy Analysis)
**Purpose**: RAG-based analysis of privacy policies for consent pattern extraction

**Features**:
- 📄 HTML to Markdown conversion for better processing
- 🤖 RAG-based consent analysis using vector embeddings
- 🎯 Purpose extraction from consent sentences
- 📊 Comprehensive consent pattern analysis

**Key Files**:
- `consent_identification/html_policy_processor.py` - HTML to Markdown converter
- `consent_identification/consent_rag_analyzer.py` - RAG-based analysis
- `consent_identification/extract_purpose.py` - Purpose extraction

### 3. WebformExtraction
**Purpose**: Multimodal web form extraction and analysis using WebArena-based automation

**Features**:
- 🤖 AI-powered web navigation and form interaction
- 📸 Multimodal form extraction (screenshots + HTML)
- 🔗 Form element alignment and validation
- 📋 Comprehensive form property extraction
- 🎯 Consent request text identification
- 🔍 Data controller extraction

**Key Components**:
- **WebArena Integration**: Modified WebArena for form-focused navigation
- **Pipeline Integration**: Complete form processing pipeline
- **Multimodal Analysis**: Combines visual and structural analysis
- **Fact Extraction**: Converts forms to structured facts for compliance checking

### 4. ViolationReasoning
**Purpose**: Formal logic-based GDPR compliance violation detection

**Features**:
- ⚖️ Datalog-based formal reasoning rules
- 🔍 Automated violation detection
- 📊 Comprehensive compliance reporting
- 🎯 Multiple violation type detection

**Key Violation Types**:
- Real choice violations
- Consent separation violations
- Withdrawal mechanism violations
- Data controller identification issues
- Accessibility violations

## Quick Start

### Prerequisites

1. **Python Environment**:
```bash
conda create -n cosmic python=3.10
conda activate cosmic
```

2. **Install Dependencies**:
```bash
# For PolicyParser
pip install selenium beautifulsoup4 requests polipy

# For WebformExtraction
pip install -r WebformExtraction/webarena/requirements.txt
playwright install

# For PP_analysis
pip install openai chromadb markdown

# For ViolationReasoning
# Install Soufflé datalog engine
sudo apt-get install souffle
```

3. **API Keys**:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### Basic Usage

#### 1. Privacy Policy Collection
```bash
cd PolicyParser/code
python website_parser.py https://example.com --output results.json
python pp_download.py --input results.json
```

#### 2. Privacy Policy Analysis
```bash
cd PP_analysis/consent_identification
python run_analysis.py --input-dir /path/to/privacy/policies/
```

#### 3. Web Form Extraction
```bash
cd WebformExtraction/webarena
python run.py --instruction_path agent/prompts/jsons/p_cot_id_actree_2s.json --test_start_idx 0 --test_end_idx 1 --model gpt-4o --result_dir ./results/
```

#### 4. Violation Detection
```bash
cd ViolationReasoning/violation_reasoning
souffle -w -F /path/to/facts -D /path/to/output violation_rules.datalog
```

## Docker Support (In Preparation)

Docker images will be available soon to streamline the installation and setup process.

## Complete Pipeline

### End-to-End Analysis Workflow

1. **Data Collection**:
   - Extract privacy policy links from target websites
   - Download and process privacy policy documents
   - Navigate and extract web forms using AI agents

2. **Multimodal Analysis**:
   - Convert privacy policies to structured format
   - Extract form elements using visual and HTML analysis
   - Align form elements between different representations

3. **Fact Extraction**:
   - Extract consent request texts and data controllers
   - Identify form purposes and user actions
   - Generate structured facts for compliance checking

4. **Compliance Checking**:
   - Apply formal logic rules to detect violations
   - Generate comprehensive compliance reports
   - Identify specific areas of non-compliance

## Contact
For any questions, please contact yinglee@ucla.edu.
## Citation

If you use this work in your research, please cite:

```bibtex
@inproceedings{li2026breaking,
  title={Breaking the illusion: Automated Reasoning of GDPR Consent Violations},
  author={Li, Ying and Qiu, Wenjun and Shezan, Faysal Hossain and Cai, Kunlin and van Dam, Michelangelo and Austin, Lisa and Lie, David and Tian, Yuan},
  booktitle={Proceedings of the 2026 IEEE Symposium on Security and Privacy (S\&P)},
  year={2026}
}
```


