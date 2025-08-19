#!/usr/bin/env python3
"""
Categorize normalized links using strict keyword matching rules.
Takes temp/links_normalized.json and config/categories.yml to produce temp/categorized.json
"""

import json
import csv
import sys
import yaml
from pathlib import Path
from collections import defaultdict

def load_categories():
    """Load categorization rules from YAML config."""
    config_path = Path('config/categories.yml')
    if not config_path.exists():
        print("Error: config/categories.yml not found", file=sys.stderr)
        sys.exit(1)
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config['categories']

def match_keywords(text, keywords):
    """Check if any keyword matches in text (case-insensitive)."""
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True, keyword
    return False, None

def categorize_link(link, categories, duplicates_lookup):
    """Categorize a single link using the rules."""
    link_id = link['id']
    href_norm = link['href_norm']
    text_norm = link['text_norm']
    
    # Skip invalid URLs
    if not link['valid_url']:
        return {
            'id': link_id,
            'href_norm': href_norm,
            'text_final': text_norm,
            'category': None,
            'action': 'skipped',
            'reason': f"invalid_url: {link['invalid_reason']}"
        }
    
    # Skip duplicates (keep only canonical)
    if href_norm in duplicates_lookup and duplicates_lookup[href_norm] != link_id:
        canonical_id = duplicates_lookup[href_norm]
        return {
            'id': link_id,
            'href_norm': href_norm, 
            'text_final': text_norm,
            'category': None,
            'action': 'skipped',
            'reason': f"duplicate_of:{canonical_id}"
        }
    
    # Try to match against categories (in order of specificity)
    search_text = f"{href_norm} {text_norm}"
    matches = []
    
    for category_id, category_data in categories.items():
        keywords = category_data.get('keywords', [])
        is_match, matched_keyword = match_keywords(search_text, keywords)
        if is_match:
            matches.append((category_id, matched_keyword))
    
    # Handle multiple matches - take first one (most specific)
    if len(matches) == 1:
        category_id, matched_keyword = matches[0]
        return {
            'id': link_id,
            'href_norm': href_norm,
            'text_final': text_norm,
            'category': category_id,
            'action': 'added',
            'reason': f"matched_keyword:{matched_keyword}"
        }
    elif len(matches) > 1:
        # Multiple matches - take the first one (most specific by order)
        category_id, matched_keyword = matches[0]
        other_matches = [m[0] for m in matches[1:]]
        return {
            'id': link_id,
            'href_norm': href_norm,
            'text_final': text_norm,
            'category': category_id,
            'action': 'added',
            'reason': f"matched_keyword:{matched_keyword} (also_matched:{','.join(other_matches)})"
        }
    else:
        # No matches
        return {
            'id': link_id,
            'href_norm': href_norm,
            'text_final': text_norm,
            'category': None,
            'action': 'skipped',
            'reason': 'no_category_match'
        }

def build_duplicates_lookup():
    """Build lookup of URL -> canonical ID for duplicate detection."""
    duplicates_path = Path('temp/duplicates.csv')
    duplicates_lookup = {}
    
    if duplicates_path.exists():
        with open(duplicates_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                href_norm = row['href_norm']
                canonical_id = row['canonical_id']
                duplicates_lookup[href_norm] = canonical_id
    
    return duplicates_lookup

def categorize_links():
    """Main categorization function."""
    try:
        # Load normalized links
        normalized_path = Path('temp/links_normalized.json')
        if not normalized_path.exists():
            print("Error: temp/links_normalized.json not found. Run normalize_links.py first.", file=sys.stderr)
            sys.exit(1)
        
        with open(normalized_path, 'r', encoding='utf-8') as f:
            links = json.load(f)
        
        # Load categories and duplicates
        categories = load_categories()
        duplicates_lookup = build_duplicates_lookup()
        
        print(f"Categorizing {len(links)} links using {len(categories)} categories")
        
        # Process each link
        categorized_links = []
        stats = defaultdict(int)
        
        for link in links:
            result = categorize_link(link, categories, duplicates_lookup)
            categorized_links.append(result)
            
            # Track stats
            if result['action'] == 'added':
                stats[f"added_{result['category']}"] += 1
                stats['total_added'] += 1
            else:
                reason_key = result['reason'].split(':')[0]  # Get reason type
                stats[f"skipped_{reason_key}"] += 1
                stats['total_skipped'] += 1
        
        # Print stats
        print(f"\nCategorization results:")
        print(f"  - Total processed: {len(categorized_links)}")
        print(f"  - Added: {stats['total_added']}")
        print(f"  - Skipped: {stats['total_skipped']}")
        
        # Category breakdown
        category_counts = {}
        for key, count in stats.items():
            if key.startswith('added_'):
                category = key.replace('added_', '')
                category_counts[category] = count
        
        if category_counts:
            print(f"\n  Per-category counts:")
            for category, count in sorted(category_counts.items()):
                category_name = categories[category]['name']
                print(f"    - {category} ({category_name}): {count}")
        
        # Skip reasons
        skip_counts = {}
        for key, count in stats.items():
            if key.startswith('skipped_'):
                reason = key.replace('skipped_', '')
                skip_counts[reason] = count
        
        if skip_counts:
            print(f"\n  Skip reasons:")
            for reason, count in sorted(skip_counts.items()):
                print(f"    - {reason}: {count}")
        
        # Write categorized results
        output_path = Path('temp/categorized.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(categorized_links, f, indent=2, ensure_ascii=False)
        print(f"\nWrote categorized links to {output_path}")
        
        return {
            'total_processed': len(categorized_links),
            'total_added': stats['total_added'],
            'total_skipped': stats['total_skipped'],
            'category_counts': category_counts,
            'skip_counts': skip_counts
        }
        
    except Exception as e:
        print(f"Fatal error during categorization: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    stats = categorize_links()
    print(f"\nSuccessfully categorized {stats['total_processed']} links")
    print(f"Added: {stats['total_added']}, Skipped: {stats['total_skipped']}")
