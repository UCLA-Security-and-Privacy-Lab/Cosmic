"""
Refactored Privacy Policy Processing Module

This module provides a clean, object-oriented approach to processing privacy policy files,
converting HTML to Markdown, and handling file operations with proper error handling.
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from tqdm import tqdm
import html2text
from bs4 import BeautifulSoup


class PrivacyPolicyProcessor:
    """
    A class to handle privacy policy file processing operations.
    """
    
    def __init__(self, base_dir: str, output_dir: Optional[str] = None):
        """
        Initialize the processor with base directory.
        
        Args:
            base_dir: Base directory containing privacy policy files
            output_dir: Optional output directory (defaults to base_dir)
        """
        self.base_dir = Path(base_dir)
        self.output_dir = Path(output_dir) if output_dir else self.base_dir
        self.html_converter = self._setup_html_converter()
    
    def _setup_html_converter(self) -> html2text.HTML2Text:
        """Setup HTML to Markdown converter with optimal settings."""
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = True
        converter.ignore_emphasis = False
        converter.body_width = 0  # Don't wrap lines
        return converter
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        Read file content with proper error handling.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If file can't be decoded
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"Unable to decode file {file_path}: {e}")
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> None:
        """
        Write content to file with proper error handling.
        
        Args:
            file_path: Path to write the file
            content: Content to write
            encoding: File encoding (default: utf-8)
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to write file {file_path}: {e}")
    
    def read_json_file(self, file_path: str) -> Dict[Any, Any]:
        """
        Read JSON file with error handling.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data
        """
        try:
            content = self.read_file(file_path)
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
    
    def html_to_markdown(self, html_content: str) -> str:
        """
        Convert HTML content to Markdown format.
        
        Args:
            html_content: HTML content as string
            
        Returns:
            Converted Markdown content
        """
        try:
            return self.html_converter.handle(html_content)
        except Exception as e:
            raise ValueError(f"Failed to convert HTML to Markdown: {e}")
    
    def process_line_breaks(self, content: str) -> str:
        """
        Process line breaks in text content to merge broken lines.
        
        Args:
            content: Text content with potential line breaks
            
        Returns:
            Processed content with merged lines
        """
        lines = content.split('\n')
        processed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Merge lines that are broken across multiple lines
            while (line.endswith(' ') and 
                   i + 1 < len(lines) and 
                   lines[i + 1].strip() != ''):
                line = line.rstrip() + ' ' + lines[i + 1]
                i += 1
            
            processed_lines.append(line.rstrip())
            i += 1
        
        return '\n'.join(processed_lines)
    
    def find_html_files(self, directory: Path) -> List[Path]:
        """
        Find HTML files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of HTML file paths
        """
        html_files = []
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.html':
                html_files.append(file_path)
        return html_files
    
    def process_single_policy(self, policy_dir: Path, force_overwrite: bool = False) -> bool:
        """
        Process a single privacy policy directory.
        
        Args:
            policy_dir: Directory containing the privacy policy
            force_overwrite: Whether to overwrite existing markdown files
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Check if markdown file already exists
            md_file = policy_dir / "policy.md"
            if md_file.exists() and not force_overwrite:
                return True
            
            # Find HTML files
            html_files = self.find_html_files(policy_dir)
            if not html_files:
                print(f"No HTML files found in {policy_dir}")
                return False
            
            # Use the first HTML file found
            html_file = html_files[0]
            
            # Read and convert HTML to Markdown
            html_content = self.read_file(str(html_file))
            markdown_content = self.html_to_markdown(html_content)
            
            # Process line breaks
            processed_content = self.process_line_breaks(markdown_content)
            
            # Write processed markdown
            self.write_file(str(md_file), processed_content)
            
            return True
            
        except Exception as e:
            print(f"Error processing {policy_dir}: {e}")
            return False
    
    def process_all_policies(self, force_overwrite: bool = False) -> Dict[str, int]:
        """
        Process all privacy policies in the base directory.
        
        Args:
            force_overwrite: Whether to overwrite existing markdown files
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'total_websites': 0,
            'total_policies': 0,
            'successful': 0,
            'failed': 0
        }
        
        if not self.base_dir.exists():
            raise FileNotFoundError(f"Base directory not found: {self.base_dir}")
        
        # Get all website directories
        website_dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]
        stats['total_websites'] = len(website_dirs)
        
        print(f"Processing {stats['total_websites']} websites...")
        
        for website_dir in tqdm(website_dirs, desc="Processing websites"):
            try:
                # Get all policy subdirectories
                policy_dirs = [d for d in website_dir.iterdir() if d.is_dir()]
                stats['total_policies'] += len(policy_dirs)
                
                for policy_dir in policy_dirs:
                    if self.process_single_policy(policy_dir, force_overwrite):
                        stats['successful'] += 1
                    else:
                        stats['failed'] += 1
                        
            except Exception as e:
                print(f"Error processing website {website_dir}: {e}")
                stats['failed'] += 1
        
        return stats
    
    def process_specific_policy(self, policy_path: str, force_overwrite: bool = False) -> bool:
        """
        Process a specific privacy policy file.
        
        Args:
            policy_path: Path to the specific policy directory
            force_overwrite: Whether to overwrite existing markdown files
            
        Returns:
            True if processing was successful, False otherwise
        """
        policy_dir = Path(policy_path)
        if not policy_dir.exists():
            raise FileNotFoundError(f"Policy directory not found: {policy_path}")
        
        return self.process_single_policy(policy_dir, force_overwrite)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process privacy policy files')
    parser.add_argument('--input-dir', required=True, help='Input directory containing privacy policies')
    parser.add_argument('--output-dir', help='Output directory (defaults to input directory)')
    parser.add_argument('--force', action='store_true', help='Force overwrite existing files')
    parser.add_argument('--specific', help='Process specific policy directory')
    
    args = parser.parse_args()
    
    processor = PrivacyPolicyProcessor(args.input_dir, args.output_dir)
    
    if args.specific:
        success = processor.process_specific_policy(args.specific, args.force)
        print(f"Processing {'successful' if success else 'failed'}")
    else:
        stats = processor.process_all_policies(args.force)
        print(f"\nProcessing complete!")
        print(f"Total websites: {stats['total_websites']}")
        print(f"Total policies: {stats['total_policies']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")


if __name__ == "__main__":
    main()
