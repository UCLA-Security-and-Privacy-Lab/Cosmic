# ViolationReasoning

A formal logic-based system for detecting GDPR compliance violations in web forms using Datalog rules and the Soufflé datalog engine.

## Overview

This system implements formal reasoning rules to detect various types of GDPR compliance violations in web forms, including consent request violations, data controller identification issues, and accessibility problems. The system uses Datalog (a declarative logic programming language) to express complex compliance rules and automatically detect violations.

## Key Features

- **Formal Logic Rules**: Uses Datalog to express GDPR compliance requirements
- **Automated Violation Detection**: Identifies multiple types of compliance violations
- **Consent Analysis**: Analyzes consent request texts and user choice mechanisms
- **Data Controller Identification**: Validates proper data controller specification
- **Accessibility Compliance**: Checks form accessibility and user interaction patterns
- **Batch Processing**: Processes multiple forms and websites systematically

## Directory Structure

```
ViolationReasoning/
└── violation_reasoning/
    ├── violation_rules.datalog    # Main violation detection rules
    ├── declarations.datalog       # Data type and relation declarations
    ├── rules.datalog             # Helper rules and computations
    ├── help_facts.datalog        # Static facts and helper relations
    └── input.datalog             # Input data specifications
```

## Core Components

1. Main Violation Rules (`violation_rules.datalog`)

The primary file containing GDPR compliance violation detection rules

2. Data Declarations (`declarations.datalog`)



3. Helper Rules (`rules.datalog`)

Contains computational rules and aggregations:

- **Purpose Analysis**: Counts unique purposes and clusters
- **Element Classification**: Categorizes form elements (textbox, button, checkbox)
- **Cluster Management**: Groups related consent purposes
- **Counting Functions**: Aggregates various metrics

4. Static Facts (`help_facts.datalog`)

Defines static relationships and helper facts:

- **Suboperations**: Maps form actions to consent operations
- **Element Types**: Defines selectable element types
- **Helper Relations**: Simplifies complex rule expressions

## Usage

### Prerequisites

1. **Soufflé Datalog Engine**: Install Soufflé for running the datalog programs
   ```bash
   # Install Soufflé (Ubuntu/Debian)
   sudo apt-get install souffle
   
   # Or build from source
   https://github.com/souffle-lang/souffle.git
   ```

2. **Input Data**: Prepare fact files containing form analysis results

### Running Violation Detection

#### Basic Usage

```bash
# Navigate to the violation reasoning directory
cd /path/to/ViolationReasoning/violation_reasoning

# Run violation detection on a facts directory
souffle -w -F /path/to/facts -D /path/to/output violation_rules.datalog
```

#### Parameters

- **`-w`**: Enable warnings
- **`-F <facts_dir>`**: Directory containing input fact files
- **`-D <output_dir>`**: Directory for output results
- **`violation_rules.datalog`**: Main rules file

#### Input Data Format

The system expects the following fact files in the input directory:

- **`crt.facts`**: Consent request texts with controller, action, purpose, negation, and element type
- **`element.facts`**: Form elements with ID, type, and text
- **`element_required.facts`**: Required field information
- **`element_status.facts`**: Element status (checked, unchecked, etc.)
- **`eid_sent_id.facts`**: Element-to-sentence ID mappings
- **`action_element.facts`**: Action-to-element relationships
- **`cluster_purposes.facts`**: Purpose clustering information
- **`withdraw.facts`**: Withdrawal mechanism information
- **`data_controller.facts`**: Data controller specifications

### Integration with Web Form Pipeline

The violation reasoning system integrates with the web form extraction pipeline:

```python
# From violation_detect.py
import subprocess

# Run violation detection for each website
for fact_folder in facts_folders:
    fact_folder_path = os.path.join(each_website_path, "facts", fact_folder)
    results_facts_folder = os.path.join(results_folder, fact_folder)
    
    # Execute Soufflé with violation rules
    cmd = ["souffle", "-w", "-F", fact_folder_path, "-D", results_facts_folder, "violation_rules.datalog"]
    subprocess.run(cmd, check=True)
```

## Output Results

The system generates CSV files for each type of violation detected:

### Violation Types

1. **`real_choice_violation.csv`**: Missing or inadequate real choice mechanisms
2. **`separate_EID_consent_violation.csv`**: Elements associated with multiple consent clusters
3. **`withdraw_available_violation.csv`**: Missing withdrawal mechanisms
4. **`specify_cid_global.csv`**: Missing data controller identification
5. **`specify_purpose.csv`**: Missing purpose specification
6. **`ambiguous.csv`**: Ambiguous consent language
7. **`freely_given_violation.csv`**: Non-freely given consent
8. **`pre_selected.csv`**: Pre-selected consent elements

### Analysis Results

1. **`real_choice_1.csv` to `real_choice_5.csv`**: Detailed real choice analysis
2. **`no_real_choice.csv`**: Cases with no real choice mechanism
3. **`real_choice_cluster_violation.csv`**: Cluster-level violations

