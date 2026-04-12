"""Export top cited figures' lifespan data for the timeline visualization."""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter

from .config import ISSUE_FILES, OUTPUT_DIR, REGION_COLORS, REGION_MAPPINGS
from .tei_parser import get_root, extract_citations, load_person_data


def export_timeline_json(output_path, top_n=50):
    """Export top N figures with birth/death years for timeline."""
    print("Exporting timeline data...")

    persons = load_person_data()

    # Count total citations per person across all issues
    total_counts = Counter()
    issue_presence = {}
    for issue_id, filename in ISSUE_FILES.items():
        root = get_root(filename)
        data = extract_citations(root, issue_id)
        issue_counts = Counter(ref['target_person'] for ref in data['person_refs'])
        for pid, count in issue_counts.items():
            total_counts[pid] += count
            if pid not in issue_presence:
                issue_presence[pid] = []
            issue_presence[pid].append(issue_id)

    # Filter to those with valid birth years, take top N
    candidates = []
    for pid, count in total_counts.most_common():
        pdata = persons.get(pid, {})
        birth = pdata.get('birth_year')
        if birth and birth > 0:
            region = pdata.get('region', 'Other/Unknown')
            candidates.append({
                'key': pid,
                'name': pdata.get('name', pid),
                'birth_year': birth,
                'death_year': pdata.get('death_year'),
                'country': pdata.get('country', 'Unknown'),
                'region': region,
                'period': pdata.get('period', 'Unknown'),
                'citations': count,
                'issues': issue_presence.get(pid, []),
                'color': REGION_COLORS.get(region, '#95a5a6'),
            })
        if len(candidates) >= top_n:
            break

    # Sort by birth year for display
    candidates.sort(key=lambda x: x['birth_year'])

    # Determine time range
    births = [c['birth_year'] for c in candidates]
    min_year = min(births) - 10 if births else 1400
    max_year = 2000

    timeline_data = {
        'figures': candidates,
        'metadata': {
            'total_figures': len(candidates),
            'time_range': [min_year, max_year],
            'generated': datetime.now().isoformat(),
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(timeline_data, f, ensure_ascii=False, indent=2)

    print(f"  Exported: {output_path} ({len(candidates)} figures)")


if __name__ == "__main__":
    from .config import PROJECT_ROOT
    export_timeline_json(PROJECT_ROOT / "timeline" / "data" / "timeline_data.json")
