"""Export enriched network to Sigma.js JSON format with ForceAtlas2 layout.

Reads the GEXF from the integrated analysis, adds community assignments
and issue presence data, computes layout, and writes sigma_graph.json.

Usage:
    python -m visualizations.export_sigma
"""

import json
import networkx as nx
from pathlib import Path
from datetime import datetime
from fa2 import ForceAtlas2

from .config import (
    ISSUE_FILES, OUTPUT_DIR, COMMUNITY_COLORS,
    REGION_COLORS, PERIOD_COLORS,
)
from .tei_parser import get_root, extract_citations


def load_enriched_graph():
    """Load the full-corpus enriched network GEXF."""
    gexf_path = OUTPUT_DIR / "full_corpus" / "integrated" / "enriched_network.gexf"
    G = nx.read_gexf(str(gexf_path))
    print(f"  Loaded GEXF: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def load_community_assignments():
    """Load community assignments from network analysis."""
    communities_path = OUTPUT_DIR / "full_corpus" / "network" / "communities.json"
    with open(communities_path, 'r', encoding='utf-8') as f:
        communities = json.load(f)

    node_community = {}
    for comm in communities:
        cid = comm['community_id']
        for member in comm['members']:
            node_community[member['id']] = cid
    return node_community


def compute_issue_presence():
    """Determine which issues each person appears in."""
    node_issues = {}
    for issue_id, filename in ISSUE_FILES.items():
        root = get_root(filename)
        data = extract_citations(root, issue_id)
        all_ids = data['cited_person_ids'] | data['author_ids']
        for pid in all_ids:
            if pid not in node_issues:
                node_issues[pid] = []
            node_issues[pid].append(issue_id)
    return node_issues


def compute_layout(G):
    """Compute ForceAtlas2 layout positions."""
    print("  Computing ForceAtlas2 layout (this may take a moment)...")
    forceatlas2 = ForceAtlas2(
        outboundAttractionDistribution=True,
        edgeWeightInfluence=1.0,
        jitterTolerance=1.0,
        barnesHutOptimize=True,
        barnesHutTheta=1.2,
        scalingRatio=2.0,
        strongGravityMode=False,
        gravity=1.0,
        verbose=False,
    )
    G_undirected = G.to_undirected()
    positions = forceatlas2.forceatlas2_networkx_layout(G_undirected, pos=None, iterations=1000)
    print(f"  Layout computed for {len(positions)} nodes")
    return positions


def compute_node_sizes(G):
    """Compute node sizes based on degree, scaled to 3-20 range."""
    degrees = dict(G.degree())
    if not degrees:
        return {}
    max_deg = max(degrees.values())
    min_size, max_size = 3, 20
    sizes = {}
    for node, deg in degrees.items():
        node_type = G.nodes[node].get('node_type', 'cited')
        base = min_size + (deg / max(max_deg, 1)) * (max_size - min_size)
        if node_type == 'author':
            base = max(base, 5)
        sizes[node] = round(base, 1)
    return sizes


def get_color(color_map, key, default='#95a5a6'):
    """Look up color from a color map, with fallback."""
    return color_map.get(key, default)


def export_sigma_json(output_path):
    """Main export function: GEXF -> sigma_graph.json."""
    print("Exporting Sigma.js graph data...")

    G = load_enriched_graph()
    communities = load_community_assignments()
    issue_presence = compute_issue_presence()
    positions = compute_layout(G)
    sizes = compute_node_sizes(G)

    nodes = []
    for node_id in G.nodes():
        data = G.nodes[node_id]
        pos = positions.get(node_id, (0, 0))
        comm = communities.get(node_id, 0)
        issues = issue_presence.get(node_id, [])

        region = data.get('region', 'Other/Unknown')
        period = data.get('period', 'Unknown')

        birth_year = data.get('birth_year', '')
        if birth_year:
            try:
                birth_year = int(float(birth_year))
            except (ValueError, TypeError):
                birth_year = ''

        nodes.append({
            'key': node_id,
            'attributes': {
                'label': data.get('label', node_id),
                'x': round(pos[0], 2),
                'y': round(pos[1], 2),
                'size': sizes.get(node_id, 3),
                'node_type': data.get('node_type', 'cited'),
                'country': data.get('country', 'Unknown'),
                'region': region,
                'period': period,
                'birth_year': birth_year,
                'wikidata': data.get('wikidata', '') if data.get('wikidata') else '',
                'community': comm,
                'issues': issues,
                'in_degree': G.in_degree(node_id),
                'out_degree': G.out_degree(node_id),
                'color_community': COMMUNITY_COLORS[comm % len(COMMUNITY_COLORS)],
                'color_region': get_color(REGION_COLORS, region),
                'color_period': get_color(PERIOD_COLORS, period),
            }
        })

    edges = []
    for i, (source, target, data) in enumerate(G.edges(data=True)):
        edges.append({
            'key': f'e_{i}',
            'source': source,
            'target': target,
            'attributes': {
                'weight': data.get('weight', 1),
            }
        })

    sigma_data = {
        'nodes': nodes,
        'edges': edges,
        'metadata': {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'num_communities': max(communities.values()) + 1 if communities else 0,
            'issues': list(ISSUE_FILES.keys()),
            'generated': datetime.now().isoformat(),
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sigma_data, f, ensure_ascii=False)

    size_kb = output_path.stat().st_size / 1024
    print(f"  Exported: {output_path} ({size_kb:.0f} KB)")
    print(f"  {len(nodes)} nodes, {len(edges)} edges")


if __name__ == "__main__":
    from .config import PROJECT_ROOT
    output = PROJECT_ROOT / "sigma-viz" / "data" / "sigma_graph.json"
    export_sigma_json(output)
