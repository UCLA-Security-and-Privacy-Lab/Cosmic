#!/usr/bin/env python3
"""
One-click Privacy Policy Processing and Consent Analysis Script

Directly calls html_policy_processor.py and consent_rag_analyzer.py
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_colored(message, color=Colors.WHITE):
    """Print colored message"""
    print(f"{color}{message}{Colors.END}")

def run_command(command, description=""):
    """Run command and print results with colors"""
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(f"Running: {description}", Colors.BOLD)
    print_colored(f"Command: {' '.join(command)}", Colors.BLUE)
    print_colored('='*60, Colors.CYAN)
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print_colored("SUCCESS!", Colors.GREEN)
        if result.stdout:
            print_colored("Output:", Colors.WHITE)
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_colored("FAILED!", Colors.RED)
        print_colored("Error:", Colors.RED)
        print(e.stderr)
        return False
    except Exception as e:
        print_colored(f"Unexpected error: {e}", Colors.RED)
        return False

def main():
    parser = argparse.ArgumentParser(description="One-click Privacy Policy Analysis")
    parser.add_argument("--input-dir", required=True, help="Input directory path")
    parser.add_argument("--specific", help="Process specific policy directory")
    parser.add_argument("--output", default="consent_rag_results.json", help="Output filename")
    
    args = parser.parse_args()
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print_colored("Starting Privacy Policy Analysis Pipeline...", Colors.BOLD)
    print_colored(f"Input directory: {args.input_dir}", Colors.BLUE)
    
    # Step 1: HTML to Markdown conversion
    if args.specific:
        # Process specific policy
        command = [
            sys.executable, "html_policy_processor.py",
            "--input-dir", args.input_dir,
            "--specific", args.specific
        ]
        success1 = run_command(command, "HTML to Markdown Conversion (Specific Policy)")
    else:
        # Process all policies - need to go up one level for html_policy_processor
        # because it expects a directory containing website directories
        parent_dir = str(Path(args.input_dir).parent)
        command = [
            sys.executable, "html_policy_processor.py",
            "--input-dir", parent_dir
        ]
        success1 = run_command(command, "HTML to Markdown Conversion (All Policies)")
    
    if not success1:
        print_colored("HTML conversion failed, stopping process", Colors.RED)
        return
    
    # Step 2: Consent Analysis
    if args.specific:
        # Analyze specific policy
        policy_md = Path(args.specific) / "policy.md"
        if policy_md.exists():
            # Save output in the same directory as the policy
            output_file = Path(args.specific) / args.output
            command = [
                sys.executable, "consent_rag_analyzer.py",
                "--policy-file", str(policy_md),
                "--output", str(output_file)
            ]
            success2 = run_command(command, "Consent Pattern Analysis (Specific Policy)")
        else:
            print_colored(f"Policy.md file not found: {policy_md}", Colors.RED)
            return
    else:
        # Analyze all policies - find all policy.md files
        input_path = Path(args.input_dir)
        policy_files = list(input_path.rglob("policy.md"))
        
        if not policy_files:
            print_colored("No policy.md files found", Colors.RED)
            return
        
        print_colored(f"Found {len(policy_files)} policy files", Colors.YELLOW)
        
        for i, policy_file in enumerate(policy_files, 1):
            # Save output in the same directory as the policy
            policy_dir = policy_file.parent
            output_file = policy_dir / args.output
            command = [
                sys.executable, "consent_rag_analyzer.py",
                "--policy-file", str(policy_file),
                "--output", str(output_file)
            ]
            success2 = run_command(command, f"Consent Pattern Analysis ({i}/{len(policy_files)})")
    
    print_colored("\nAnalysis Complete!", Colors.GREEN)
    print_colored("Check output files for detailed results", Colors.BLUE)

if __name__ == "__main__":
    main()