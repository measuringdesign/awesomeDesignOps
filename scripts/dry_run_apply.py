#!/usr/bin/env python3
"""
Dry-run application of snippets to index.md.
Validates structure and simulates changes without actually writing.
"""

import json
import re
from pathlib import Path

# Mapping from category IDs to index.md section headings
CATEGORY_TO_HEADING = {
    '1.A': '### 1.A Team Models (centralised, embedded, hybrid)',
    '1.B': '### 1.B Capacity & Resource Planning', 
    '1.C': '### 1.C Governance & Standards',
    '1.D': '### 1.D Onboarding & Knowledge Sharing',
    '2.A.1': '#### 2.A.1 Foundations (colour, type, spacing)',
    '2.A.2': '#### 2.A.2 Components (UI kits, patterns)',
    '2.A.3': '#### 2.A.3 Documentation (usage guidelines, principles)',
    '2.B': '### 2.B Toolchains & Platforms',
    '2.C': '### 2.C Workflow Optimisation',
    '2.D': '### 2.D Collaboration with Engineering',
    '3.A': '### 3.A Testing & Accessibility',
    '3.B': '### 3.B Metrics & Measurement',
    '3.C': '### 3.C Feedback Loops',
    '3.D': '### 3.D Continuous Improvement'
}

def parse_index_structure(index_content):
    """Parse index.md and extract headings and their positions."""
    lines = index_content.split('\n')
    headings = {}
    
    for i, line in enumerate(lines):
        for category_id, expected_heading in CATEGORY_TO_HEADING.items():
            if line.strip() == expected_heading:
                headings[category_id] = {
                    'line_number': i,
                    'heading': expected_heading,
                    'found': True
                }
    
    return headings, lines

def find_snippet_files():
    """Find all snippet files and their link counts."""
    snippets_dir = Path('temp/snippets')
    snippets = {}
    
    for category_id in CATEGORY_TO_HEADING.keys():
        snippet_file = snippets_dir / f"{category_id}.md"
        if snippet_file.exists():
            with open(snippet_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Count links by counting lines starting with "- ["
            link_count = len([line for line in content.split('\n') if line.strip().startswith('- [')])
            snippets[category_id] = {
                'file': snippet_file,
                'link_count': link_count,
                'content': content
            }
        else:
            snippets[category_id] = {
                'file': None,
                'link_count': 0,
                'content': ''
            }
    
    return snippets

def dry_run_apply():
    """Perform dry-run validation of index.md structure and snippet application."""
    try:
        # Read current index.md
        index_path = Path('index.md')
        if not index_path.exists():
            print("Error: index.md not found", file=sys.stderr)
            return False
            
        with open(index_path, 'r', encoding='utf-8') as f:
            index_content = f.read()
        
        print("Performing dry-run validation...")
        
        # Parse structure
        headings, lines = parse_index_structure(index_content)
        snippets = find_snippet_files()
        
        # Validation results
        validation_errors = []
        validation_warnings = []
        
        # Check all expected headings exist
        missing_headings = []
        for category_id, expected_heading in CATEGORY_TO_HEADING.items():
            if category_id not in headings:
                missing_headings.append(f"{category_id}: {expected_heading}")
        
        if missing_headings:
            validation_errors.append(f"Missing headings: {missing_headings}")
        
        # Verify no extra headings would be created
        # (This is inherently prevented by our approach)
        
        # Check snippet files exist for categories with links
        missing_snippets = []
        for category_id, snippet_data in snippets.items():
            if snippet_data['link_count'] > 0 and not snippet_data['file']:
                missing_snippets.append(category_id)
        
        if missing_snippets:
            validation_errors.append(f"Missing snippet files: {missing_snippets}")
        
        # Simulate insertion and check for duplicates
        simulated_links = set()
        duplicate_links = []
        
        for category_id, snippet_data in snippets.items():
            if snippet_data['content']:
                # Extract URLs from markdown links
                link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                matches = re.findall(link_pattern, snippet_data['content'])
                
                for text, url in matches:
                    if url in simulated_links:
                        duplicate_links.append(f"Duplicate URL {url} in category {category_id}")
                    simulated_links.add(url)
        
        if duplicate_links:
            validation_errors.append(f"Would introduce duplicates: {duplicate_links[:5]}...")  # Show first 5
        
        # Generate report
        report = {
            'validation_passed': len(validation_errors) == 0,
            'total_headings_found': len(headings),
            'total_expected_headings': len(CATEGORY_TO_HEADING),
            'total_categories_with_links': sum(1 for s in snippets.values() if s['link_count'] > 0),
            'total_links_to_add': sum(s['link_count'] for s in snippets.values()),
            'unique_links': len(simulated_links),
            'categories': {},
            'validation_errors': validation_errors,
            'validation_warnings': validation_warnings
        }
        
        # Per-category details
        for category_id in CATEGORY_TO_HEADING.keys():
            heading_found = category_id in headings
            snippet_data = snippets.get(category_id, {'link_count': 0})
            
            report['categories'][category_id] = {
                'heading_found': heading_found,
                'heading_text': CATEGORY_TO_HEADING[category_id],
                'link_count': snippet_data['link_count'],
                'will_be_updated': heading_found and snippet_data['link_count'] > 0
            }
        
        # Write report
        report_path = Path('temp/dry_run_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        if report['validation_passed']:
            print("✅ Dry-run validation PASSED")
        else:
            print("❌ Dry-run validation FAILED")
            for error in validation_errors:
                print(f"  ERROR: {error}")
        
        if validation_warnings:
            for warning in validation_warnings:
                print(f"  WARNING: {warning}")
        
        print(f"\nDry-run summary:")
        print(f"  - Headings found: {len(headings)}/{len(CATEGORY_TO_HEADING)}")
        print(f"  - Categories with links: {report['total_categories_with_links']}")
        print(f"  - Total links to add: {report['total_links_to_add']}")
        print(f"  - Unique URLs: {report['unique_links']}")
        print(f"  - Report written to: {report_path}")
        
        return report['validation_passed']
        
    except Exception as e:
        print(f"Fatal error during dry-run: {e}")
        return False

if __name__ == '__main__':
    import sys
    success = dry_run_apply()
    if not success:
        sys.exit(1)
    print("Dry-run validation completed successfully")
