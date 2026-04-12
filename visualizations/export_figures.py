"""Export figure biography data — per-figure citation context across issues."""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

from .config import ISSUE_FILES, ISSUE_YEARS, OUTPUT_DIR, REGION_COLORS
from .tei_parser import get_root, extract_citations, load_person_data


def export_figures_json(output_path):
    """Export per-figure citation context data."""
    print("Exporting figure biography data...")

    persons = load_person_data()

    # Collect per-issue citation data
    per_issue = {}
    for issue_id, filename in ISSUE_FILES.items():
        root = get_root(filename)
        per_issue[issue_id] = extract_citations(root, issue_id)

    # For each cited figure, build their biography
    all_person_ids = set()
    for data in per_issue.values():
        all_person_ids.update(data['cited_person_ids'])
        all_person_ids.update(data['author_ids'])

    figures = []
    for pid in all_person_ids:
        pdata = persons.get(pid, {})
        name = pdata.get('name', pid)

        # Who cites this figure (SITIO contributors)
        cited_by = Counter()  # author_id -> count
        # Co-cited figures (appear in same div)
        co_cited = Counter()  # person_id -> count
        # Per-issue presence
        issue_data = {}

        for issue_id, data in per_issue.items():
            # Find all refs to this person in this issue
            refs_in_issue = [r for r in data['person_refs'] if r['target_person'] == pid]
            if not refs_in_issue:
                # Also check if this person is an author in this issue
                if pid in data['author_ids']:
                    issue_data[issue_id] = {
                        'role': 'author',
                        'citations': 0,
                        'cited_by': [],
                    }
                continue

            # Who cites them in this issue
            issue_citers = Counter()
            div_ids = set()
            for ref in refs_in_issue:
                cited_by[ref['source_author']] += 1
                issue_citers[ref['source_author']] += 1
                div_ids.add(ref['div_id'])

            # Co-citations: other people cited in the same divs
            for ref in data['person_refs']:
                if ref['div_id'] in div_ids and ref['target_person'] != pid:
                    co_cited[ref['target_person']] += 1

            citer_names = [
                {'id': aid, 'name': persons.get(aid, {}).get('name', aid), 'count': c}
                for aid, c in issue_citers.most_common()
            ]

            issue_data[issue_id] = {
                'role': 'cited',
                'citations': len(refs_in_issue),
                'cited_by': citer_names,
            }

        if not issue_data:
            continue

        total_citations = sum(
            d['citations'] for d in issue_data.values() if d.get('citations')
        )

        top_co_cited = [
            {'id': cid, 'name': persons.get(cid, {}).get('name', cid), 'count': c}
            for cid, c in co_cited.most_common(15)
        ]

        top_cited_by = [
            {'id': aid, 'name': persons.get(aid, {}).get('name', aid), 'count': c}
            for aid, c in cited_by.most_common(10)
        ]

        region = pdata.get('region', 'Other/Unknown')
        figures.append({
            'key': pid,
            'name': name,
            'country': pdata.get('country', 'Unknown'),
            'region': region,
            'period': pdata.get('period', 'Unknown'),
            'birth_year': pdata.get('birth_year'),
            'death_year': pdata.get('death_year'),
            'wikidata': pdata.get('wikidata', ''),
            'total_citations': total_citations,
            'num_issues': len([d for d in issue_data.values() if d.get('citations', 0) > 0]),
            'issues': issue_data,
            'cited_by': top_cited_by,
            'co_cited': top_co_cited,
            'color': REGION_COLORS.get(region, '#95a5a6'),
        })

    figures.sort(key=lambda x: -x['total_citations'])

    output_data = {
        'figures': figures,
        'issue_years': ISSUE_YEARS,
        'metadata': {
            'total_figures': len(figures),
            'generated': datetime.now().isoformat(),
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False)

    size_kb = output_path.stat().st_size / 1024
    print(f"  Exported: {output_path} ({len(figures)} figures, {size_kb:.0f} KB)")


if __name__ == "__main__":
    from .config import PROJECT_ROOT
    export_figures_json(PROJECT_ROOT / "timeline" / "data" / "figures_data.json")
