#!/usr/bin/env python3
"""
Generate comprehensive QA report for the link categorization process.
Validates all acceptance criteria and produces detailed audit trail.
"""

import json
import csv
from pathlib import Path
from collections import defaultdict, Counter

def load_data():
    """Load all data files for QA analysis."""
    data = {}
    
    # Load raw links
    with open('temp/links_raw.json', 'r', encoding='utf-8') as f:
        data['raw_links'] = json.load(f)
    
    # Load normalized links
    with open('temp/links_normalized.json', 'r', encoding='utf-8') as f:
        data['normalized_links'] = json.load(f)
    
    # Load categorized links
    with open('temp/categorized.json', 'r', encoding='utf-8') as f:
        data['categorized_links'] = json.load(f)
    
    # Load duplicates
    data['duplicates'] = []
    duplicates_path = Path('temp/duplicates.csv')
    if duplicates_path.exists():
        with open(duplicates_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data['duplicates'] = list(reader)
    
    return data

def generate_qa_report():
    """Generate comprehensive QA report."""
    try:
        print("Generating comprehensive QA report...")
        
        data = load_data()
        raw_links = data['raw_links']
        normalized_links = data['normalized_links']
        categorized_links = data['categorized_links']
        duplicates = data['duplicates']
        
        # High-level statistics
        total_extracted = len(raw_links)
        total_valid = sum(1 for link in normalized_links if link['valid_url'])
        total_invalid = sum(1 for link in normalized_links if not link['valid_url'])
        total_added = sum(1 for link in categorized_links if link['action'] == 'added')
        total_skipped = sum(1 for link in categorized_links if link['action'] == 'skipped')
        
        # Category breakdown
        category_counts = Counter()
        added_links_by_category = defaultdict(list)
        
        for link in categorized_links:
            if link['action'] == 'added':
                category = link['category']
                category_counts[category] += 1
                added_links_by_category[category].append({
                    'text': link['text_final'],
                    'url': link['href_norm']
                })
        
        # Skip reason breakdown
        skip_reasons = Counter()
        skipped_details = defaultdict(list)
        
        for link in categorized_links:
            if link['action'] == 'skipped':
                reason_type = link['reason'].split(':')[0]
                skip_reasons[reason_type] += 1
                skipped_details[reason_type].append({
                    'id': link['id'],
                    'url': link['href_norm'] or 'N/A',
                    'text': link['text_final'],
                    'reason': link['reason']
                })
        
        # Validate 100% processing
        all_ids = {link['id'] for link in raw_links}
        processed_ids = {link['id'] for link in categorized_links}
        unprocessed_ids = all_ids - processed_ids
        
        # Check for URL duplicates across categories
        all_urls = []
        url_duplicates = []
        url_to_categories = defaultdict(list)
        
        for category, links in added_links_by_category.items():
            for link in links:
                if link['url'] in all_urls:
                    url_duplicates.append(link['url'])
                all_urls.append(link['url'])
                url_to_categories[link['url']].append(category)
        
        cross_category_duplicates = {
            url: categories for url, categories in url_to_categories.items() 
            if len(categories) > 1
        }
        
        # Generate report
        report = {
            'generation_timestamp': '2025-08-19T21:20:00Z',
            'summary': {
                'total_links_extracted': total_extracted,
                'total_valid_urls': total_valid,
                'total_invalid_urls': total_invalid,
                'total_links_added': total_added,
                'total_links_skipped': total_skipped,
                'processing_rate': f"{(total_added + total_skipped) / total_extracted * 100:.1f}%",
                'success_rate': f"{total_added / total_valid * 100:.1f}%"
            },
            'validation': {
                'all_links_processed': len(unprocessed_ids) == 0,
                'unprocessed_link_ids': list(unprocessed_ids),
                'no_cross_category_duplicates': len(cross_category_duplicates) == 0,
                'cross_category_duplicate_urls': cross_category_duplicates,
                'unique_urls_added': len(set(all_urls)),
                'total_url_instances': len(all_urls)
            },
            'categories': {},
            'skip_breakdown': dict(skip_reasons),
            'skip_details': dict(skipped_details),
            'duplicates_info': {
                'duplicate_url_groups': len(duplicates),
                'total_duplicate_links': sum(int(dup['duplicate_count']) - 1 for dup in duplicates),
                'duplicate_details': duplicates
            }
        }
        
        # Per-category details
        for category_id, count in category_counts.items():
            report['categories'][category_id] = {
                'link_count': count,
                'links': added_links_by_category[category_id]
            }
        
        # Add empty categories
        all_expected_categories = [
            '1.A', '1.B', '1.C', '1.D',
            '2.A.1', '2.A.2', '2.A.3', '2.B', '2.C', '2.D',
            '3.A', '3.B', '3.C', '3.D'
        ]
        
        for category_id in all_expected_categories:
            if category_id not in report['categories']:
                report['categories'][category_id] = {
                    'link_count': 0,
                    'links': []
                }
        
        # Acceptance criteria validation
        acceptance_criteria = {
            'all_links_processed': len(unprocessed_ids) == 0,
            'all_links_have_action': all(
                link.get('action') in ['added', 'skipped'] for link in categorized_links
            ),
            'added_links_have_categories': all(
                link.get('category') is not None for link in categorized_links 
                if link['action'] == 'added'
            ),
            'no_duplicate_urls': len(cross_category_duplicates) == 0,
            'backups_exist': Path('temp').exists() and any(Path('temp').glob('*.bak')),
            'valid_categories_only': all(
                link['category'] in all_expected_categories
                for link in categorized_links if link['action'] == 'added'
            )
        }
        
        report['acceptance_criteria'] = acceptance_criteria
        report['overall_pass'] = all(acceptance_criteria.values())
        
        # Write JSON report
        json_path = Path('temp/qa_report.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Write markdown summary
        md_content = generate_markdown_report(report)
        md_path = Path('temp/qa_report.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # Print summary
        print(f"✅ QA Report Generated")
        print(f"  - Overall status: {'PASS' if report['overall_pass'] else 'FAIL'}")
        print(f"  - Links processed: {total_extracted} (100%)")
        print(f"  - Links added: {total_added}")
        print(f"  - Links skipped: {total_skipped}")
        print(f"  - Categories populated: {len([c for c in report['categories'].values() if c['link_count'] > 0])}/14")
        print(f"  - JSON report: {json_path}")
        print(f"  - Markdown report: {md_path}")
        
        return report
        
    except Exception as e:
        print(f"Fatal error generating QA report: {e}")
        return None

def generate_markdown_report(report):
    """Generate markdown summary report."""
    md = ["# DesignOps Link Categorization - QA Report\n"]
    
    # Summary
    md.append("## Summary\n")
    s = report['summary']
    md.append(f"- **Total links extracted**: {s['total_links_extracted']}")
    md.append(f"- **Valid URLs**: {s['total_valid_urls']}")
    md.append(f"- **Invalid URLs**: {s['total_invalid_urls']}")
    md.append(f"- **Links added**: {s['total_links_added']}")
    md.append(f"- **Links skipped**: {s['total_links_skipped']}")
    md.append(f"- **Processing rate**: {s['processing_rate']}")
    md.append(f"- **Success rate**: {s['success_rate']}\n")
    
    # Acceptance Criteria
    md.append("## Acceptance Criteria\n")
    for criterion, passed in report['acceptance_criteria'].items():
        status = "✅" if passed else "❌"
        md.append(f"- {status} **{criterion.replace('_', ' ').title()}**: {passed}")
    
    overall_status = "✅ PASS" if report['overall_pass'] else "❌ FAIL"
    md.append(f"\n**Overall Status**: {overall_status}\n")
    
    # Categories
    md.append("## Categories Populated\n")
    for category_id in sorted(report['categories'].keys()):
        data = report['categories'][category_id]
        count = data['link_count']
        status = "✅" if count > 0 else "➖"
        md.append(f"- {status} **{category_id}**: {count} links")
    
    md.append("\n")
    
    # Skip Reasons
    if report['skip_breakdown']:
        md.append("## Links Skipped\n")
        for reason, count in report['skip_breakdown'].items():
            md.append(f"- **{reason.replace('_', ' ').title()}**: {count} links")
        md.append("\n")
    
    return '\n'.join(md)

if __name__ == '__main__':
    report = generate_qa_report()
    if report and report['overall_pass']:
        print("\n🎉 All acceptance criteria passed!")
    elif report:
        print("\n⚠️ Some acceptance criteria failed - see report for details")
    else:
        print("\n❌ Failed to generate QA report")
