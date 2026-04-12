"""Export contributor profile data for the contributors page."""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

from .config import ISSUE_FILES, ISSUE_YEARS, OUTPUT_DIR, REGION_COLORS
from .tei_parser import get_root, extract_citations, load_person_data


def export_contributors_json(output_path):
    """Export contributor profiles with citation breakdowns."""
    print("Exporting contributor data...")

    persons = load_person_data()

    # Collect per-author data across all issues
    author_data = defaultdict(lambda: {
        'total_citations': 0,
        'unique_figures': set(),
        'top_cited': Counter(),
        'region_breakdown': Counter(),
        'period_breakdown': Counter(),
        'issues': [],
        'num_texts': 0,
    })

    for issue_id, filename in ISSUE_FILES.items():
        root = get_root(filename)
        data = extract_citations(root, issue_id)

        # Track texts per author in this issue
        for div in data['divs']:
            for author_id in div['authors']:
                if issue_id not in author_data[author_id]['issues']:
                    author_data[author_id]['issues'].append(issue_id)
                author_data[author_id]['num_texts'] += 1

        # Track citations per author
        for ref in data['person_refs']:
            author_id = ref['source_author']
            target_id = ref['target_person']
            pdata = persons.get(target_id, {})

            author_data[author_id]['total_citations'] += 1
            author_data[author_id]['unique_figures'].add(target_id)
            author_data[author_id]['top_cited'][pdata.get('name', target_id)] += 1

            region = pdata.get('region', 'Other/Unknown')
            period = pdata.get('period', 'Unknown')
            author_data[author_id]['region_breakdown'][region] += 1
            author_data[author_id]['period_breakdown'][period] += 1

    # Build output
    contributors = []
    for author_id, stats in author_data.items():
        pdata = persons.get(author_id, {})
        if not stats['total_citations']:
            continue

        regions = dict(stats['region_breakdown'].most_common())
        total_r = sum(regions.values()) or 1
        top_region = max(regions, key=regions.get) if regions else 'Unknown'

        periods = dict(stats['period_breakdown'].most_common())
        top_period = max(periods, key=periods.get) if periods else 'Unknown'

        contributors.append({
            'key': author_id,
            'name': pdata.get('name', author_id),
            'total_citations': stats['total_citations'],
            'unique_figures': len(stats['unique_figures']),
            'num_texts': stats['num_texts'],
            'issues': sorted(stats['issues'], key=lambda x: ISSUE_YEARS.get(x, 0)),
            'top_region': top_region,
            'pct_western_europe': round(regions.get('Western Europe', 0) / total_r * 100, 1),
            'pct_latin_america': round(regions.get('Latin America', 0) / total_r * 100, 1),
            'top_period': top_period,
            'top_cited': [{'name': n, 'citations': c}
                          for n, c in stats['top_cited'].most_common(10)],
            'region_breakdown': regions,
            'period_breakdown': periods,
        })

    contributors.sort(key=lambda x: -x['total_citations'])

    output_data = {
        'contributors': contributors,
        'metadata': {
            'total_contributors': len(contributors),
            'generated': datetime.now().isoformat(),
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"  Exported: {output_path} ({len(contributors)} contributors)")


if __name__ == "__main__":
    from .config import PROJECT_ROOT
    export_contributors_json(PROJECT_ROOT / "contributors" / "data" / "contributors_data.json")
