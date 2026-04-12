"""Bibliography analysis for Revista SITIO TEI corpus.

Analyzes cited works via title[@ref] -> listBibl.xml.
"""

import networkx as nx
from pyvis.network import Network
import pandas as pd
import json
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .config import MPL_STYLE, MPL_DPI, COMMUNITY_COLORS
from .tei_parser import load_person_data


def run_bibliography_analysis(citations, persons, bibls, output_dir):
    """Run bibliography analysis for one issue or full corpus."""
    output_dir.mkdir(parents=True, exist_ok=True)
    issue_id = citations['issue_id']

    title_refs = citations['title_refs']
    if not title_refs:
        print(f"  No bibliography references for {issue_id}. Skipping.")
        return

    # --- Most cited works ---
    bibl_counts = Counter(ref['target_bibl'] for ref in title_refs)
    most_cited = []
    for bid, count in bibl_counts.most_common():
        bibl_data = bibls.get(bid, {})
        most_cited.append({
            'bibl_id': bid,
            'title': bibl_data.get('title', bid),
            'author_name': bibl_data.get('author_name', ''),
            'author_ref': bibl_data.get('author_ref', ''),
            'date_year': bibl_data.get('date_year', ''),
            'level': bibl_data.get('level', ''),
            'lang': bibl_data.get('lang', ''),
            'citation_count': count,
        })

    df_cited = pd.DataFrame(most_cited)
    df_cited.to_csv(output_dir / 'most_cited_works.csv', index=False, encoding='utf-8')

    # --- Author-to-work bipartite network ---
    G = nx.Graph()
    for ref in title_refs:
        source = ref['source_author']
        target_bibl = ref['target_bibl']

        source_name = persons.get(source, {}).get('name', source)
        bibl_data = bibls.get(target_bibl, {})
        bibl_label = bibl_data.get('title', target_bibl)
        if bibl_label and len(bibl_label) > 40:
            bibl_label = bibl_label[:37] + "..."

        if source not in G:
            G.add_node(source, label=source_name, node_type='author', bipartite=0)
        if target_bibl not in G:
            G.add_node(target_bibl, label=bibl_label or target_bibl, node_type='work', bipartite=1)

        if G.has_edge(source, target_bibl):
            G[source][target_bibl]['weight'] += 1
        else:
            G.add_edge(source, target_bibl, weight=1)

    # Generate pyvis visualization
    if G.number_of_nodes() > 0:
        net = Network(height="95vh", width="100%", bgcolor="#1a1a2e",
                      font_color="#eee", cdn_resources='remote')
        net.barnes_hut(gravity=-2000, central_gravity=0.3, spring_length=200)

        degrees = dict(G.degree())
        max_degree = max(degrees.values()) if degrees else 1

        for node in G.nodes():
            data = G.nodes[node]
            size = 10 + (degrees.get(node, 0) / max_degree) * 40
            if data.get('node_type') == 'author':
                color = '#e74c3c'
                shape = 'square'
            else:
                color = '#3498db'
                shape = 'dot'

            net.add_node(node, label=data.get('label', node),
                         title=f"{data.get('label', node)}<br>Type: {data.get('node_type')}<br>Connections: {degrees.get(node, 0)}",
                         size=size, color=color, shape=shape)

        for s, t, d in G.edges(data=True):
            net.add_edge(s, t, value=d.get('weight', 1))

        net.write_html(str(output_dir / 'bibl_network.html'))

    # --- Genre distribution ---
    level_counts = Counter(
        bibls.get(ref['target_bibl'], {}).get('level', 'unknown')
        for ref in title_refs
    )

    # --- Language distribution ---
    lang_counts = Counter(
        bibls.get(ref['target_bibl'], {}).get('lang') or 'es'
        for ref in title_refs
    )

    # --- Publication date distribution ---
    date_years = [
        bibls.get(ref['target_bibl'], {}).get('date_year')
        for ref in title_refs
    ]
    date_years = [y for y in date_years if y]

    # --- Charts ---
    if HAS_MATPLOTLIB and len(most_cited) > 0:
        if MPL_STYLE in plt.style.available:
            plt.style.use(MPL_STYLE)

        # Top 20 most cited works
        fig, ax = plt.subplots(figsize=(12, 8))
        top_n = min(20, len(most_cited))
        labels = [f"{r['title'][:35]}..." if r['title'] and len(r['title']) > 35 else (r['title'] or r['bibl_id'])
                  for r in most_cited[:top_n]]
        values = [r['citation_count'] for r in most_cited[:top_n]]
        bars = ax.barh(labels[::-1], values[::-1], color='#3498db', edgecolor='white')
        ax.set_xlabel('Citation Count', fontsize=12)
        ax.set_title(f'Most Cited Works — {issue_id}', fontsize=14, fontweight='bold')
        for bar, val in zip(bars, values[::-1]):
            ax.text(val + 0.2, bar.get_y() + bar.get_height()/2, str(val), va='center', fontsize=9)
        plt.tight_layout()
        fig.savefig(output_dir / 'most_cited_works.png', dpi=MPL_DPI)
        plt.close(fig)

        # Publication date distribution
        if date_years:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.hist(date_years, bins=30, edgecolor='white', alpha=0.7, color='#2ecc71')
            ax.set_xlabel('Publication Year', fontsize=12)
            ax.set_ylabel('Number of Cited Works', fontsize=12)
            ax.set_title(f'Publication Years of Cited Works — {issue_id}', fontsize=14, fontweight='bold')
            plt.tight_layout()
            fig.savefig(output_dir / 'bibl_year_distribution.png', dpi=MPL_DPI)
            plt.close(fig)

    # --- Summary JSON ---
    summary = {
        'issue_id': issue_id,
        'generated': datetime.now().isoformat(),
        'total_title_refs': len(title_refs),
        'unique_works_cited': len(bibl_counts),
        'top_10_works': [
            {'bibl_id': r['bibl_id'], 'title': r['title'],
             'author': r['author_name'], 'count': r['citation_count']}
            for r in most_cited[:10]
        ],
        'genre_distribution': dict(level_counts),
        'language_distribution': dict(lang_counts),
        'network_nodes': G.number_of_nodes() if G else 0,
        'network_edges': G.number_of_edges() if G else 0,
    }

    with open(output_dir / 'bibl_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Print report
    print(f"\n  Bibliography Analysis: {issue_id}")
    print(f"  Total references: {len(title_refs)}")
    print(f"  Unique works: {len(bibl_counts)}")
    print(f"  Top 5 cited works:")
    for r in most_cited[:5]:
        print(f"    {r['citation_count']}x — {(r['title'] or r['bibl_id'])[:50]} ({r['author_name']})")
