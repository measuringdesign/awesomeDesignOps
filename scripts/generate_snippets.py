#!/usr/bin/env python3
"""
Generate per-category Markdown snippets from categorized links.
Takes temp/categorized.json and creates temp/snippets/{category}.md files
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def generate_snippets():
    """Generate markdown snippets for each category."""
    try:
        # Load categorized links
        categorized_path = Path('temp/categorized.json')
        if not categorized_path.exists():
            print("Error: temp/categorized.json not found. Run categorize_links.py first.", file=sys.stderr)
            sys.exit(1)
            
        with open(categorized_path, 'r', encoding='utf-8') as f:
            links = json.load(f)
        
        # Group links by category
        categories = defaultdict(list)
        
        for link in links:
            if link['action'] == 'added' and link['category']:
                categories[link['category']].append({
                    'text': link['text_final'],
                    'url': link['href_norm']
                })
        
        print(f"Generating snippets for {len(categories)} categories")
        
        # Create snippets directory
        snippets_dir = Path('temp/snippets')
        snippets_dir.mkdir(exist_ok=True)
        
        # Generate a snippet for each category
        total_links = 0
        
        for category_id, links_list in categories.items():
            if not links_list:
                continue
                
            # Sort links alphabetically by text for consistency
            links_list.sort(key=lambda x: x['text'].lower())
            
            # Generate markdown content
            markdown_lines = []
            for link in links_list:
                # Format as [text](url) - no descriptions
                markdown_lines.append(f"- [{link['text']}]({link['url']})")
            
            markdown_content = '\n'.join(markdown_lines) + '\n'
            
            # Write to category file
            category_file = snippets_dir / f"{category_id}.md"
            with open(category_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"  - {category_id}: {len(links_list)} links -> {category_file}")
            total_links += len(links_list)
        
        print(f"\nGenerated {len(categories)} snippet files with {total_links} total links")
        
        # Verify all expected categories have files
        expected_categories = [
            '1.A', '1.B', '1.C', '1.D',
            '2.A.1', '2.A.2', '2.A.3', '2.B', '2.C', '2.D',
            '3.A', '3.B', '3.C', '3.D'
        ]
        
        missing_categories = []
        for expected in expected_categories:
            if expected not in categories:
                missing_categories.append(expected)
        
        if missing_categories:
            print(f"Note: No links found for categories: {', '.join(missing_categories)}")
        
        return {
            'categories_with_links': len(categories),
            'total_links': total_links,
            'missing_categories': missing_categories
        }
        
    except Exception as e:
        print(f"Fatal error generating snippets: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    stats = generate_snippets()
    print(f"\nSuccessfully generated {stats['categories_with_links']} snippet files")
    print(f"Total links: {stats['total_links']}")
