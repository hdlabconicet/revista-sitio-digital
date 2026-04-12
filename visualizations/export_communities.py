"""Export community portrait data for the communities visualization."""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

from .config import ISSUE_FILES, OUTPUT_DIR, REGION_COLORS, COMMUNITY_COLORS
from .tei_parser import get_root, extract_citations, load_person_data


def export_communities_json(output_path):
    """Export community profiles with member details and contributor usage."""
    print("Exporting community portraits data...")

    persons = load_person_data()

    # Load community assignments
    with open(OUTPUT_DIR / "full_corpus" / "network" / "communities.json", 'r', encoding='utf-8') as f:
        raw_communities = json.load(f)

    # Map each person to their community
    member_to_comm = {}
    for comm in raw_communities:
        for m in comm['members']:
            member_to_comm[m['id']] = comm['community_id']

    # Collect citation data: contributor-community links + per-person citation counts
    author_community_counts = defaultdict(Counter)
    person_citation_counts = Counter()
    for issue_id, filename in ISSUE_FILES.items():
        root = get_root(filename)
        data = extract_citations(root, issue_id)

        for ref in data['person_refs']:
            person_citation_counts[ref['target_person']] += 1
            target_comm = member_to_comm.get(ref['target_person'])
            if target_comm is not None:
                author_community_counts[ref['source_author']][target_comm] += 1

    communities = []
    for comm in raw_communities:
        cid = comm['community_id']
        members = comm['members']

        # Analyze community composition
        countries = Counter()
        regions = Counter()
        periods = Counter()
        birth_years = []
        members_with_data = []

        for m in members:
            pid = m['id']
            pdata = persons.get(pid, {})
            name = pdata.get('name', m.get('name', pid))
            country = pdata.get('country', 'Unknown')
            region = pdata.get('region', 'Other/Unknown')
            period = pdata.get('period', 'Unknown')
            birth_year = pdata.get('birth_year')

            countries[country] += 1
            regions[region] += 1
            periods[period] += 1
            if birth_year:
                birth_years.append(birth_year)

            members_with_data.append({
                'id': pid,
                'name': name,
                'country': country,
                'region': region,
                'period': period,
                'birth_year': birth_year,
                'citations': person_citation_counts.get(pid, 0),
            })

        # Sort members by citation count (most cited first) for better previews
        members_with_data.sort(key=lambda x: -x['citations'])

        # Which SITIO contributors draw most from this community
        top_contributors = []
        for aid, comm_counts in author_community_counts.items():
            count = comm_counts.get(cid, 0)
            if count > 0:
                aname = persons.get(aid, {}).get('name', aid)
                top_contributors.append({'id': aid, 'name': aname, 'count': count})
        top_contributors.sort(key=lambda x: -x['count'])

        median_birth = None
        if birth_years:
            sorted_years = sorted(birth_years)
            median_birth = sorted_years[len(sorted_years) // 2]

        communities.append({
            'id': cid,
            'size': len(members),
            'color': COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)],
            'top_region': regions.most_common(1)[0][0] if regions else 'Unknown',
            'top_period': periods.most_common(1)[0][0] if periods else 'Unknown',
            'median_birth_year': median_birth,
            'regions': dict(regions.most_common()),
            'countries': dict(countries.most_common(10)),
            'periods': dict(periods.most_common()),
            'members': members_with_data,
            'top_contributors': top_contributors[:8],
        })

    communities.sort(key=lambda x: -x['size'])

    output_data = {
        'communities': communities,
        'metadata': {
            'total_communities': len(communities),
            'generated': datetime.now().isoformat(),
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False)

    size_kb = output_path.stat().st_size / 1024
    print(f"  Exported: {output_path} ({len(communities)} communities, {size_kb:.0f} KB)")


if __name__ == "__main__":
    from .config import PROJECT_ROOT
    export_communities_json(PROJECT_ROOT / "map" / "data" / "communities_data.json")
