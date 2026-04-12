"""Export shadow influence data — figures with high centrality but low citations."""

import json
from pathlib import Path
from datetime import datetime

from .config import OUTPUT_DIR, REGION_COLORS
from .tei_parser import load_person_data


def export_shadows_json(output_path):
    """Export shadow influence rankings."""
    print("Exporting shadow influence data...")

    persons = load_person_data()

    # Load network metrics
    with open(OUTPUT_DIR / "full_corpus" / "network" / "network_summary.json", 'r', encoding='utf-8') as f:
        summary = json.load(f)

    # Load node metrics CSV for betweenness and degree
    import csv
    node_metrics = {}
    with open(OUTPUT_DIR / "full_corpus" / "network" / "node_metrics.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_metrics[row['id']] = {
                'name': row['name'],
                'node_type': row['node_type'],
                'in_degree': int(row['in_degree']),
                'out_degree': int(row['out_degree']),
                'betweenness': float(row['betweenness']),
                'pagerank': float(row['pagerank']),
            }

    # Compute shadow score: betweenness / (in_degree + 1)
    # High score = structurally important but not heavily cited
    figures = []
    for nid, metrics in node_metrics.items():
        total_degree = metrics['in_degree'] + metrics['out_degree']
        if total_degree == 0:
            continue

        pdata = persons.get(nid, {})
        shadow_score = metrics['betweenness'] / (metrics['in_degree'] + 1)

        figures.append({
            'key': nid,
            'name': metrics['name'],
            'node_type': metrics['node_type'],
            'country': pdata.get('country', 'Unknown'),
            'region': pdata.get('region', 'Other/Unknown'),
            'period': pdata.get('period', 'Unknown'),
            'in_degree': metrics['in_degree'],
            'out_degree': metrics['out_degree'],
            'betweenness': metrics['betweenness'],
            'pagerank': metrics['pagerank'],
            'shadow_score': shadow_score,
            'color': REGION_COLORS.get(pdata.get('region', ''), '#95a5a6'),
        })

    # Sort by shadow score (highest = most "shadow")
    figures.sort(key=lambda x: -x['shadow_score'])

    # Also provide a "most cited" ranking for comparison
    by_citation = sorted(figures, key=lambda x: -x['in_degree'])

    output_data = {
        'by_shadow': figures[:50],
        'by_citation': by_citation[:50],
        'by_betweenness': sorted(figures, key=lambda x: -x['betweenness'])[:50],
        'metadata': {
            'total_figures': len(figures),
            'generated': datetime.now().isoformat(),
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"  Exported: {output_path} ({len(figures)} figures)")


if __name__ == "__main__":
    from .config import PROJECT_ROOT
    export_shadows_json(PROJECT_ROOT / "shadows" / "data" / "shadows_data.json")
