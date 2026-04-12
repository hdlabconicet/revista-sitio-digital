"""Export country-level citation data for the geographic map.

Aggregates citation counts by country, adds centroid coordinates,
and computes per-issue breakdowns.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

from .config import ISSUE_FILES, OUTPUT_DIR, REGION_COLORS, REGION_MAPPINGS
from .tei_parser import get_root, extract_citations, load_person_data


# Country centroid coordinates (lat, lng) for major countries in corpus
COUNTRY_COORDS = {
    'Argentina': (-34.6, -58.4),
    'France': (46.2, 2.2),
    'Germany': (51.2, 10.4),
    'United Kingdom': (55.4, -3.4),
    'Italy': (41.9, 12.5),
    'United States': (37.1, -95.7),
    'Spain': (40.5, -3.7),
    'Greece': (39.1, 21.8),
    'Uruguay': (-34.9, -56.2),
    'Switzerland': (46.8, 8.2),
    'Ireland': (53.1, -7.7),
    'Austria': (47.5, 14.6),
    'Poland': (51.9, 19.1),
    'Cuba': (21.5, -77.8),
    'Mexico': (23.6, -102.6),
    'Brazil': (-14.2, -51.9),
    'Russia': (61.5, 105.3),
    'Czech Republic': (49.8, 15.5),
    'Netherlands': (52.1, 5.3),
    'Belgium': (50.5, 4.5),
    'Portugal': (39.4, -8.2),
    'Hungary': (47.2, 19.5),
    'Romania': (45.9, 24.9),
    'Denmark': (56.3, 9.5),
    'Sweden': (60.1, 18.6),
    'Norway': (60.5, 8.5),
    'Chile': (-35.7, -71.5),
    'Venezuela': (6.4, -66.6),
    'Peru': (-9.2, -75.0),
    'Colombia': (4.6, -74.1),
    'Japan': (36.2, 138.3),
    'China': (35.9, 104.2),
    'Israel': (31.0, 34.9),
    'Nicaragua': (12.9, -85.2),
}


def export_map_json(output_path):
    """Export country-level citation data for the map."""
    print("Exporting map data...")

    persons = load_person_data()

    # Get per-issue citation data
    per_issue_data = {}
    for issue_id, filename in ISSUE_FILES.items():
        root = get_root(filename)
        per_issue_data[issue_id] = extract_citations(root, issue_id)

    # Aggregate by country: total citations and per-issue
    country_stats = defaultdict(lambda: {
        'total_citations': 0,
        'unique_figures': set(),
        'top_figures': Counter(),
        'per_issue': defaultdict(int),
    })

    for issue_id, data in per_issue_data.items():
        # Count citations per person in this issue
        person_counts = Counter(ref['target_person'] for ref in data['person_refs'])
        for pid, count in person_counts.items():
            pdata = persons.get(pid, {})
            country = pdata.get('country')
            if not country:
                continue
            country_stats[country]['total_citations'] += count
            country_stats[country]['unique_figures'].add(pid)
            country_stats[country]['top_figures'][pdata.get('name', pid)] += count
            country_stats[country]['per_issue'][issue_id] += count

    # Build output
    countries = []
    for country, stats in sorted(country_stats.items(), key=lambda x: -x[1]['total_citations']):
        coords = COUNTRY_COORDS.get(country)
        if not coords:
            continue  # Skip countries without coordinates

        region = REGION_MAPPINGS.get(country, 'Other/Unknown')
        top_figs = [{'name': n, 'citations': c}
                    for n, c in stats['top_figures'].most_common(5)]

        countries.append({
            'country': country,
            'region': region,
            'lat': coords[0],
            'lng': coords[1],
            'total_citations': stats['total_citations'],
            'unique_figures': len(stats['unique_figures']),
            'top_figures': top_figs,
            'per_issue': dict(stats['per_issue']),
            'color': REGION_COLORS.get(region, '#95a5a6'),
        })

    map_data = {
        'countries': countries,
        'metadata': {
            'total_countries': len(countries),
            'total_citations': sum(c['total_citations'] for c in countries),
            'issues': list(ISSUE_FILES.keys()),
            'generated': datetime.now().isoformat(),
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    print(f"  Exported: {output_path} ({len(countries)} countries)")


if __name__ == "__main__":
    from .config import PROJECT_ROOT
    export_map_json(PROJECT_ROOT / "map" / "data" / "map_data.json")
