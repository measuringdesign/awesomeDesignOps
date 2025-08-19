#!/usr/bin/env python3
"""
Extract all links from .source.html file.
Outputs raw link data to temp/links_raw.json and temp/links_raw.csv
"""

import json
import csv
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import html
import uuid

def extract_links():
    """Extract all anchor tags from .source.html with metadata."""
    try:
        # Read the source HTML file
        source_path = Path('.source.html')
        if not source_path.exists():
            print(f"Error: {source_path} not found", file=sys.stderr)
            sys.exit(1)
            
        with open(source_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        links = []
        current_section = "Unknown"
        order_index = 0
        
        # Walk through all elements to track sections and extract links
        for element in soup.find_all(['h2', 'h3', 'a']):
            if element.name in ['h2', 'h3']:
                # Update current section context
                current_section = element.get_text(strip=True)
            elif element.name == 'a':
                href = element.get('href')
                if href:  # Only process anchors with href
                    # Generate unique ID for this link
                    link_id = str(uuid.uuid4())
                    
                    # Extract and clean text
                    text = element.get_text(strip=True)
                    # Decode HTML entities
                    text = html.unescape(text)
                    
                    link_data = {
                        'id': link_id,
                        'href_raw': href,
                        'text_raw': text,
                        'section_hint': current_section,
                        'order_index': order_index
                    }
                    
                    links.append(link_data)
                    order_index += 1
        
        print(f"Extracted {len(links)} links from .source.html")
        
        # Ensure temp directory exists
        temp_dir = Path('temp')
        temp_dir.mkdir(exist_ok=True)
        
        # Write JSON output
        json_path = temp_dir / 'links_raw.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(links, f, indent=2, ensure_ascii=False)
        print(f"Wrote JSON to {json_path}")
        
        # Write CSV output
        csv_path = temp_dir / 'links_raw.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if links:
                fieldnames = ['id', 'href_raw', 'text_raw', 'section_hint', 'order_index']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(links)
        print(f"Wrote CSV to {csv_path}")
        
        return len(links)
        
    except Exception as e:
        print(f"Fatal error during link extraction: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    total_links = extract_links()
    print(f"Successfully extracted {total_links} links")
