#!/usr/bin/env python3
"""
Apply categorized links to index.md.
Replaces placeholder content with actual link lists.
"""

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

def load_snippets():
    """Load all snippet files."""
    snippets_dir = Path('temp/snippets')
    snippets = {}
    
    for category_id in CATEGORY_TO_HEADING.keys():
        snippet_file = snippets_dir / f"{category_id}.md"
        if snippet_file.exists():
            with open(snippet_file, 'r', encoding='utf-8') as f:
                snippets[category_id] = f.read().strip()
        else:
            snippets[category_id] = ""
    
    return snippets

def apply_changes():
    """Apply snippet content to index.md sections."""
    try:
        # Load snippets
        snippets = load_snippets()
        
        # Read current index.md
        index_path = Path('index.md')
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        result_lines = []
        
        i = 0
        changes_made = 0
        
        while i < len(lines):
            line = lines[i]
            result_lines.append(line)
            
            # Check if this line matches a heading we want to update
            category_to_update = None
            for category_id, expected_heading in CATEGORY_TO_HEADING.items():
                if line.strip() == expected_heading:
                    category_to_update = category_id
                    break
            
            if category_to_update and snippets[category_to_update]:
                # Found a heading with content to insert
                i += 1
                
                # Skip any existing content until next heading or end
                start_skip = i
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    # Stop at next heading (starts with # or is a major section)
                    if (next_line.startswith('#') or 
                        next_line.startswith('## ') or 
                        next_line.startswith('### ') or 
                        next_line.startswith('#### ')):
                        break
                    i += 1
                
                # Insert empty line and snippet content
                result_lines.append('')
                result_lines.append(snippets[category_to_update])
                result_lines.append('')
                
                changes_made += 1
                print(f"  ✅ Updated {category_to_update} with {snippets[category_to_update].count('- [')} links")
                
                # Don't increment i here - we want to process the next heading
                continue
            else:
                i += 1
        
        # Write updated content
        updated_content = '\n'.join(result_lines)
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"\n✅ Applied changes to index.md")
        print(f"  - Sections updated: {changes_made}")
        print(f"  - Total links added: {sum(snippet.count('- [') for snippet in snippets.values())}")
        
        return changes_made
        
    except Exception as e:
        print(f"Fatal error applying changes: {e}")
        return 0

if __name__ == '__main__':
    import sys
    
    print("Applying categorized links to index.md...")
    changes = apply_changes()
    
    if changes > 0:
        print(f"Successfully applied {changes} section updates")
    else:
        print("No changes were applied")
        sys.exit(1)
