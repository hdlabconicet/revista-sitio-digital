"""Export citation flow data — contributor to region/country flows."""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

from .config import ISSUE_FILES, ISSUE_YEARS, OUTPUT_DIR, REGION_COLORS
from .tei_parser import get_root, extract_citations, load_person_data


def export_flows_json(output_path):
    """Export contributor → region citation flows."""
    print("Exporting citation flows data...")

    persons = load_person_data()

    # Aggregate per-author → region flows
    author_flows = defaultdict(lambda: defaultdict(int))
    author_totals = Counter()

    for issue_id, filename in ISSUE_FILES.items():
        root = get_root(filename)
        data = extract_citations(root, issue_id)
        for ref in data['person_refs']:
            aid = ref['source_author']
            tid = ref['target_person']
            region = persons.get(tid, {}).get('region', 'Other/Unknown')
            author_flows[aid][region] += 1
            author_totals[aid] += 1

    # Build flows for top contributors (min 20 citations)
    contributors = []
    for aid, total in author_totals.most_common():
        if total < 20:
            continue
        pdata = persons.get(aid, {})
        flows = dict(author_flows[aid])
        contributors.append({
            'key': aid,
            'name': pdata.get('name', aid),
            'total': total,
            'flows': flows,
        })

    # Compute region totals
    region_totals = Counter()
    for c in contributors:
        for region, count in c['flows'].items():
            region_totals[region] += count

    output_data = {
        'contributors': contributors,
        'region_totals': dict(region_totals.most_common()),
        'region_colors': REGION_COLORS,
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
    export_flows_json(PROJECT_ROOT / "flows" / "data" / "flows_data.json")
