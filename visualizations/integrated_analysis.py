"""Integrated network-prosopography analysis for Revista SITIO.

Refactored from visualizations_1/integrated_analysis.py.
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

from .config import (
    NS, REGION_COLORS, PERIOD_COLORS, HISTORICAL_PERIODS,
    MPL_STYLE, MPL_DPI,
)
from .tei_parser import clean_id, load_person_data, get_region, get_historical_period


def build_enriched_network(citations, persons):
    """Build citation network enriched with prosopographical data.

    Parameters
    ----------
    citations : dict
        Output of extract_citations(): contains 'person_refs', 'issue_id', etc.
    persons : dict
        Output of load_person_data(): maps person_id -> metadata dict.

    Returns
    -------
    G : nx.DiGraph
    edge_details : list[dict]
    author_citations : dict[str, list[str]]
    """
    issue_id = citations.get('issue_id', 'unknown')
    print(f"Building enriched network for {issue_id}...")

    G = nx.DiGraph()
    edge_details = []
    author_citations = defaultdict(list)

    for ref in citations['person_refs']:
        source = ref['source_author']
        target = ref['target_person']
        div_id = ref['div_id']

        source_data = persons.get(source, {})
        target_data = persons.get(target, {})

        # Add source node
        if source not in G:
            G.add_node(source,
                       label=source_data.get('name', source),
                       node_type='author',
                       country=source_data.get('country', 'Unknown'),
                       region=source_data.get('region', 'Other/Unknown'),
                       period=source_data.get('period', 'Unknown'),
                       birth_year=source_data.get('birth_year'))

        # Add target node
        if target not in G:
            G.add_node(target,
                       label=target_data.get('name', target),
                       node_type='cited',
                       country=target_data.get('country', 'Unknown'),
                       region=target_data.get('region', 'Other/Unknown'),
                       period=target_data.get('period', 'Unknown'),
                       birth_year=target_data.get('birth_year'))

        author_citations[source].append(target)

        edge_details.append({
            'source': source,
            'target': target,
            'text_id': div_id,
            'source_country': source_data.get('country'),
            'target_country': target_data.get('country'),
            'target_region': target_data.get('region'),
            'target_period': target_data.get('period'),
        })

        if G.has_edge(source, target):
            G[source][target]['weight'] += 1
        else:
            G.add_edge(source, target, weight=1)

    print(f"  Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G, edge_details, dict(author_citations)


def analyze_citation_patterns(edge_details, author_citations, persons):
    """Analyze citation patterns by geography and period."""
    print("Analyzing citation patterns...")

    analysis = {}

    # Overall patterns
    target_countries = [e['target_country'] for e in edge_details if e['target_country']]
    target_regions = [e['target_region'] for e in edge_details if e['target_region']]
    target_periods = [e['target_period'] for e in edge_details if e['target_period']]

    analysis['overall'] = {
        'citations_by_country': dict(Counter(target_countries).most_common(20)),
        'citations_by_region': dict(Counter(target_regions)),
        'citations_by_period': dict(Counter(target_periods))
    }

    # Per-author patterns
    author_profiles = {}
    for author, cited_ids in author_citations.items():
        author_data = persons.get(author, {})

        countries = []
        regions = []
        periods = []

        for cid in cited_ids:
            cited_data = persons.get(cid, {})
            if cited_data.get('country'):
                countries.append(cited_data['country'])
            if cited_data.get('region'):
                regions.append(cited_data['region'])
            if cited_data.get('period'):
                periods.append(cited_data['period'])

        author_profiles[author] = {
            'name': author_data.get('name', author),
            'total_citations': len(cited_ids),
            'unique_citations': len(set(cited_ids)),
            'countries_cited': dict(Counter(countries).most_common(10)),
            'regions_cited': dict(Counter(regions)),
            'periods_cited': dict(Counter(periods))
        }

    analysis['author_profiles'] = author_profiles

    # Cross-border citations analysis
    cross_border = defaultdict(lambda: defaultdict(int))
    for e in edge_details:
        if e['source_country'] and e['target_country']:
            cross_border[e['source_country']][e['target_country']] += 1

    analysis['cross_border'] = {k: dict(v) for k, v in cross_border.items()}

    print("  Pattern analysis complete")
    return analysis


def _filter_for_viz(G, min_degree=2):
    """Filter large networks for visualization, keeping degree >= min_degree + all authors."""
    if G.number_of_nodes() <= 300:
        return G
    keep = {n for n, d in G.degree() if d >= min_degree}
    keep.update(n for n in G.nodes() if G.nodes[n].get('node_type') == 'author')
    G_viz = G.subgraph(keep).copy()
    print(f"  Filtered: {G_viz.number_of_nodes()} nodes (from {G.number_of_nodes()}, degree >= {min_degree} + authors)")
    return G_viz


def _configure_physics(net, n_nodes):
    """Configure pyvis physics scaled to network size."""
    if n_nodes > 400:
        net.barnes_hut(gravity=-4000, central_gravity=0.3, spring_length=250,
                       spring_strength=0.01, damping=0.4)
    elif n_nodes > 200:
        net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=200,
                       spring_strength=0.03, damping=0.2)
    else:
        net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=200,
                       spring_strength=0.05, damping=0.09)


def generate_geographic_network(G, output_path):
    """Generate network visualization colored by geographic region."""
    print("Generating geographic network...")

    G_viz = _filter_for_viz(G)

    net = Network(height="95vh", width="100%", bgcolor="#1a1a2e", font_color="#eee",
                  select_menu=True, filter_menu=True, cdn_resources='remote')
    _configure_physics(net, G_viz.number_of_nodes())

    degrees = dict(G_viz.degree())
    max_degree = max(degrees.values()) if degrees else 1

    for node in G_viz.nodes():
        data = G_viz.nodes[node]
        region = data.get('region', 'Other')
        color = REGION_COLORS.get(region, '#95a5a6')
        size = 10 + (degrees.get(node, 0) / max_degree) * 40
        shape = 'square' if data.get('node_type') == 'author' else 'dot'

        tooltip = f"""
        <b>{data.get('label', node)}</b><br>
        Country: {data.get('country', 'Unknown')}<br>
        Region: {region}<br>
        Period: {data.get('period', 'Unknown')}<br>
        Birth: {data.get('birth_year', 'N/A')}
        """

        net.add_node(node, label=data.get('label', node), title=tooltip,
                     size=size, color=color, shape=shape)

    for s, t, d in G_viz.edges(data=True):
        net.add_edge(s, t, value=d.get('weight', 1), arrows='to')

    net.write_html(str(output_path))
    print(f"  Saved to {output_path}")


def generate_temporal_network(G, output_path):
    """Generate network visualization colored by historical period."""
    print("Generating temporal network...")

    G_viz = _filter_for_viz(G)

    net = Network(height="95vh", width="100%", bgcolor="#0a0a0a", font_color="#eee",
                  select_menu=True, filter_menu=True, cdn_resources='remote')
    _configure_physics(net, G_viz.number_of_nodes())

    degrees = dict(G_viz.degree())
    max_degree = max(degrees.values()) if degrees else 1

    for node in G_viz.nodes():
        data = G_viz.nodes[node]
        period = data.get('period', 'Unknown')
        color = PERIOD_COLORS.get(period, '#95a5a6')
        size = 10 + (degrees.get(node, 0) / max_degree) * 40
        shape = 'square' if data.get('node_type') == 'author' else 'dot'

        net.add_node(node, label=data.get('label', node),
                     title=f"{data.get('label')}<br>Period: {period}<br>Birth: {data.get('birth_year', 'N/A')}",
                     size=size, color=color, shape=shape)

    for s, t, d in G_viz.edges(data=True):
        net.add_edge(s, t, value=d.get('weight', 1), arrows='to')

    net.write_html(str(output_path))
    print(f"  Saved to {output_path}")


def generate_visualizations(analysis, output_dir):
    """Generate statistical visualizations."""
    if not HAS_MATPLOTLIB:
        return

    print("Generating visualizations...")

    if MPL_STYLE in plt.style.available:
        plt.style.use(MPL_STYLE)

    # 1. Citations by region (pie)
    fig, ax = plt.subplots(figsize=(10, 10))
    regions = analysis['overall']['citations_by_region']
    colors = [REGION_COLORS.get(r, '#95a5a6') for r in regions.keys()]
    ax.pie(regions.values(), labels=regions.keys(), autopct='%1.1f%%', colors=colors)
    ax.set_title('Citations by Geographic Region', fontsize=14, fontweight='bold')
    fig.savefig(output_dir / 'citations_by_region.png', dpi=MPL_DPI)
    plt.close(fig)

    # 2. Citations by period (bar)
    fig, ax = plt.subplots(figsize=(12, 6))
    periods = analysis['overall']['citations_by_period']
    period_order = [p[2] for p in HISTORICAL_PERIODS] + ['Unknown']
    ordered = {k: periods.get(k, 0) for k in period_order if k in periods}
    colors = [PERIOD_COLORS.get(p, '#95a5a6') for p in ordered.keys()]
    ax.barh(list(ordered.keys()), list(ordered.values()), color=colors)
    ax.set_xlabel('Number of Citations')
    ax.set_title('Citations by Historical Period', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig.savefig(output_dir / 'citations_by_period.png', dpi=MPL_DPI)
    plt.close(fig)

    # 3. Author profiles heatmap (top authors vs regions)
    profiles = analysis['author_profiles']
    if profiles:
        authors = sorted(profiles.keys(), key=lambda x: profiles[x]['total_citations'], reverse=True)[:10]
        all_regions = set()
        for p in profiles.values():
            all_regions.update(p['regions_cited'].keys())
        all_regions = sorted(all_regions)

        data = []
        for a in authors:
            row = [profiles[a]['regions_cited'].get(r, 0) for r in all_regions]
            data.append(row)

        fig, ax = plt.subplots(figsize=(12, 8))
        im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
        ax.set_xticks(range(len(all_regions)))
        ax.set_xticklabels(all_regions, rotation=45, ha='right')
        ax.set_yticks(range(len(authors)))
        ax.set_yticklabels([profiles[a]['name'] for a in authors])
        ax.set_title('Author Citation Patterns by Region', fontsize=14, fontweight='bold')
        plt.colorbar(im, label='Citations')
        plt.tight_layout()
        fig.savefig(output_dir / 'author_region_heatmap.png', dpi=MPL_DPI)
        plt.close(fig)

    print("  Visualizations saved")


def export_results(G, analysis, persons, output_dir):
    """Export all results."""
    print("Exporting results...")
    output_dir.mkdir(exist_ok=True)

    # 1. Enriched node data
    node_data = []
    for node in G.nodes():
        d = G.nodes[node]
        node_data.append({
            'id': node,
            'name': d.get('label', node),
            'type': d.get('node_type', ''),
            'country': d.get('country', ''),
            'region': d.get('region', ''),
            'period': d.get('period', ''),
            'birth_year': d.get('birth_year', ''),
            'in_degree': G.in_degree(node),
            'out_degree': G.out_degree(node)
        })
    pd.DataFrame(node_data).to_csv(output_dir / 'enriched_nodes.csv', index=False)

    # 2. Analysis JSON
    with open(output_dir / 'citation_patterns.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)

    # 3. Author profiles CSV
    profiles = []
    for aid, data in analysis['author_profiles'].items():
        top_region = max(data['regions_cited'].items(), key=lambda x: x[1])[0] if data['regions_cited'] else 'N/A'
        top_period = max(data['periods_cited'].items(), key=lambda x: x[1])[0] if data['periods_cited'] else 'N/A'
        profiles.append({
            'author_id': aid,
            'author_name': data['name'],
            'total_citations': data['total_citations'],
            'unique_citations': data['unique_citations'],
            'top_region': top_region,
            'top_period': top_period,
            'pct_western_europe': round(data['regions_cited'].get('Western Europe', 0) / max(data['total_citations'], 1) * 100, 1),
            'pct_latin_america': round(data['regions_cited'].get('Latin America', 0) / max(data['total_citations'], 1) * 100, 1)
        })
    pd.DataFrame(profiles).to_csv(output_dir / 'author_citation_profiles.csv', index=False)

    # 4. Cross-border matrix
    cross = analysis.get('cross_border', {})
    if cross:
        all_countries = set()
        for k, v in cross.items():
            all_countries.add(k)
            all_countries.update(v.keys())
        all_countries = sorted(all_countries)

        matrix = []
        for src in all_countries:
            row = {'source': src}
            for tgt in all_countries:
                row[tgt] = cross.get(src, {}).get(tgt, 0)
            matrix.append(row)
        pd.DataFrame(matrix).to_csv(output_dir / 'cross_border_citations.csv', index=False)

    # 5. GEXF with attributes
    G_clean = G.copy()
    for node in G_clean.nodes():
        for key, value in list(G_clean.nodes[node].items()):
            G_clean.nodes[node][key] = '' if value is None else str(value)
    nx.write_gexf(G_clean, output_dir / 'enriched_network.gexf')

    print(f"  Results exported to {output_dir}/")


def print_report(analysis):
    """Print summary report."""
    print("\n" + "="*70)
    print("INTEGRATED NETWORK-PROSOPOGRAPHY ANALYSIS")
    print("="*70)

    print("\nCITATIONS BY REGION (Top 5)")
    regions = analysis['overall']['citations_by_region']
    total = sum(regions.values())
    for region, count in sorted(regions.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {region}: {count} ({count/total*100:.1f}%)")

    print("\nCITATIONS BY PERIOD (Top 5)")
    periods = analysis['overall']['citations_by_period']
    for period, count in sorted(periods.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {period}: {count} ({count/total*100:.1f}%)")

    print("\nTOP CITED COUNTRIES")
    countries = analysis['overall']['citations_by_country']
    for country, count in list(countries.items())[:10]:
        print(f"  {country}: {count}")

    print("\nAUTHOR CITATION PROFILES")
    profiles = analysis['author_profiles']
    sorted_authors = sorted(profiles.items(), key=lambda x: x[1]['total_citations'], reverse=True)

    for aid, data in sorted_authors[:8]:
        top_region = max(data['regions_cited'].items(), key=lambda x: x[1])[0] if data['regions_cited'] else 'N/A'
        print(f"  {data['name']}: {data['total_citations']} citations, primarily {top_region}")

    print("\n" + "="*70)


def run_integrated_analysis(citations, persons, output_dir):
    """Run integrated network-prosopography analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)

    G, edge_details, author_citations = build_enriched_network(citations, persons)
    if G.number_of_nodes() == 0:
        print(f"  No nodes for {citations['issue_id']}. Skipping.")
        return

    analysis = analyze_citation_patterns(edge_details, author_citations, persons)
    generate_geographic_network(G, output_dir / 'network_by_region.html')
    generate_temporal_network(G, output_dir / 'network_by_period.html')
    generate_visualizations(analysis, output_dir)
    export_results(G, analysis, persons, output_dir)
    print_report(analysis)
