#!/usr/bin/env python3
"""
Normalize URLs and de-duplicate strictly.
Takes temp/links_raw.json and produces temp/links_normalized.json and temp/duplicates.csv
"""

import json
import csv
import sys
import re
import html
from urllib.parse import urlparse, parse_qs, urlunparse
from pathlib import Path
from collections import defaultdict

def clean_tracking_params(url):
    """Remove tracking parameters from URL."""
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'gclid', 'fbclid', 'mc_cid', 'mc_eid'
    }
    
    parsed = urlparse(url)
    if not parsed.query:
        return url
    
    query_params = parse_qs(parsed.query)
    cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}
    
    # Rebuild query string
    if cleaned_params:
        query_pairs = []
        for key, values in cleaned_params.items():
            for value in values:
                query_pairs.append(f"{key}={value}")
        new_query = '&'.join(query_pairs)
    else:
        new_query = ''
    
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        ''  # Remove fragment
    ))

def normalize_url(href_raw):
    """Normalize a URL with strict validation."""
    try:
        # Decode HTML entities and strip whitespace
        url = html.unescape(href_raw.strip())
        
        # Check for obviously broken schemes (don't auto-fix)
        if re.match(r'htt[^p]://', url, re.IGNORECASE) or re.match(r'https?[^:]/', url, re.IGNORECASE):
            return None, f"Invalid scheme in URL: {url}"
        
        # Parse URL
        parsed = urlparse(url)
        
        # Must have scheme and netloc for valid URLs
        if not parsed.scheme or not parsed.netloc:
            return None, f"Missing scheme or domain: {url}"
        
        # Only allow http/https schemes
        if parsed.scheme.lower() not in ['http', 'https']:
            return None, f"Unsupported scheme '{parsed.scheme}': {url}"
        
        # Normalize components
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip('/')  # Remove trailing slash
        if not path:
            path = ''
        
        # Remove tracking params and fragments
        cleaned_url = urlunparse((scheme, netloc, path, parsed.params, parsed.query, ''))
        normalized_url = clean_tracking_params(cleaned_url)
        
        return normalized_url, None
        
    except Exception as e:
        return None, f"Parse error: {str(e)}"

def normalize_links():
    """Normalize all extracted links and identify duplicates."""
    try:
        # Read raw links
        raw_path = Path('temp/links_raw.json')
        if not raw_path.exists():
            print("Error: temp/links_raw.json not found. Run extract_links.py first.", file=sys.stderr)
            sys.exit(1)
        
        with open(raw_path, 'r', encoding='utf-8') as f:
            raw_links = json.load(f)
        
        print(f"Processing {len(raw_links)} raw links")
        
        normalized_links = []
        url_to_ids = defaultdict(list)  # Track duplicates
        
        for link in raw_links:
            link_id = link['id']
            href_raw = link['href_raw']
            text_raw = link['text_raw']
            
            # Normalize URL
            href_norm, invalid_reason = normalize_url(href_raw)
            
            # Normalize text
            text_norm = text_raw.strip()
            
            # Build normalized link record
            normalized_link = {
                'id': link_id,
                'href_raw': href_raw,
                'href_norm': href_norm,
                'text_norm': text_norm,
                'valid_url': href_norm is not None,
                'invalid_reason': invalid_reason
            }
            
            normalized_links.append(normalized_link)
            
            # Track for duplicate detection
            if href_norm:
                url_to_ids[href_norm].append(link_id)
        
        # Identify duplicates
        duplicates = []
        for href_norm, ids in url_to_ids.items():
            if len(ids) > 1:
                duplicates.append({
                    'href_norm': href_norm,
                    'duplicate_ids': ids,
                    'canonical_id': ids[0],  # First one is canonical
                    'duplicate_count': len(ids)
                })
        
        valid_count = sum(1 for link in normalized_links if link['valid_url'])
        invalid_count = len(normalized_links) - valid_count
        duplicate_url_count = len(duplicates)
        duplicate_link_count = sum(d['duplicate_count'] - 1 for d in duplicates)
        
        print(f"Normalization results:")
        print(f"  - Total links: {len(normalized_links)}")
        print(f"  - Valid URLs: {valid_count}")
        print(f"  - Invalid URLs: {invalid_count}")
        print(f"  - Unique URLs: {len(url_to_ids)}")
        print(f"  - Duplicate URLs: {duplicate_url_count}")
        print(f"  - Duplicate links: {duplicate_link_count}")
        
        # Write normalized links
        normalized_path = Path('temp/links_normalized.json')
        with open(normalized_path, 'w', encoding='utf-8') as f:
            json.dump(normalized_links, f, indent=2, ensure_ascii=False)
        print(f"Wrote normalized links to {normalized_path}")
        
        # Write duplicates CSV
        duplicates_path = Path('temp/duplicates.csv')
        with open(duplicates_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['href_norm', 'canonical_id', 'duplicate_count', 'all_ids']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for dup in duplicates:
                writer.writerow({
                    'href_norm': dup['href_norm'],
                    'canonical_id': dup['canonical_id'],
                    'duplicate_count': dup['duplicate_count'],
                    'all_ids': ','.join(dup['duplicate_ids'])
                })
        print(f"Wrote duplicates report to {duplicates_path}")
        
        return {
            'total': len(normalized_links),
            'valid': valid_count,
            'invalid': invalid_count,
            'unique_urls': len(url_to_ids),
            'duplicate_urls': duplicate_url_count,
            'duplicate_links': duplicate_link_count
        }
        
    except Exception as e:
        print(f"Fatal error during normalization: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    stats = normalize_links()
    print(f"Successfully normalized {stats['total']} links")
    print(f"Valid: {stats['valid']}, Invalid: {stats['invalid']}")
    print(f"Unique URLs: {stats['unique_urls']}, Duplicates: {stats['duplicate_links']}")
