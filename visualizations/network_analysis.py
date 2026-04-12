"""Citation network analysis for Revista SITIO TEI corpus.

Refactored from visualizations_1/network_analysis.py.
"""

import networkx as nx
from pyvis.network import Network
import pandas as pd
import json
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

from .config import NS, COMMUNITY_COLORS
from .tei_parser import clean_id, load_person_data, extract_citations


def build_citation_network(citations, persons):
    """
    Build directed citation network from extracted citation data.

    Args:
        citations: dict from extract_citations() with person_refs, author_ids, etc.
        persons: dict from load_person_data() mapping pid -> metadata

    Returns:
        (G, edge_details, author_texts) same structure as original.
    """
    print("Building citation network...")

    G = nx.DiGraph()
    edge_details = []
    author_texts = defaultdict(list)

    # Build author_texts from divs data
    for div in citations.get('divs', []):
        div_id = div['id']
        for source in div['authors']:
            author_texts[source].append(div_id)

    # Process each person reference
    for ref in citations['person_refs']:
        source = ref['source_author']
        target = ref['target_person']
        div_id = ref['div_id']

        source_data = persons.get(source, {})
        source_label = source_data.get('name', source)

        G.add_node(source,
                   label=str(source_label) if source_label else source,
                   node_type='author',
                   birth_year=source_data.get('birth_year'),
                   birth_place=str(source_data.get('birth_place_raw')) if source_data.get('birth_place_raw') else None,
                   wikidata=str(source_data.get('wikidata')) if source_data.get('wikidata') else None)

        target_data = persons.get(target, {})
        target_label = target_data.get('name', target)

        if target not in G:
            G.add_node(target,
                       label=str(target_label) if target_label else target,
                       node_type='cited',
                       birth_year=target_data.get('birth_year'),
                       birth_place=str(target_data.get('birth_place_raw')) if target_data.get('birth_place_raw') else None,
                       wikidata=str(target_data.get('wikidata')) if target_data.get('wikidata') else None)

        edge_details.append({
            'source': source,
            'source_name': source_label,
            'target': target,
            'target_name': target_label,
            'text_id': div_id
        })

        if G.has_edge(source, target):
            G[source][target]['weight'] += 1
        else:
            G.add_edge(source, target, weight=1)

    print(f"   Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G, edge_details, dict(author_texts)


def calculate_network_metrics(G):
    """Calculate comprehensive network metrics."""
    print("Calculating network metrics...")

    metrics = {}

    # Basic metrics
    metrics['nodes'] = G.number_of_nodes()
    metrics['edges'] = G.number_of_edges()
    metrics['density'] = nx.density(G)

    # Identify authors (those with outgoing edges) vs cited (incoming only)
    authors = [n for n in G.nodes() if G.out_degree(n) > 0]
    cited_only = [n for n in G.nodes() if G.out_degree(n) == 0]
    metrics['num_authors'] = len(authors)
    metrics['num_cited_only'] = len(cited_only)

    # Degree statistics
    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())

    metrics['avg_in_degree'] = sum(in_degrees.values()) / len(in_degrees) if in_degrees else 0
    metrics['avg_out_degree'] = sum(out_degrees.values()) / len(out_degrees) if out_degrees else 0
    metrics['max_in_degree'] = max(in_degrees.values()) if in_degrees else 0
    metrics['max_out_degree'] = max(out_degrees.values()) if out_degrees else 0

    # Centrality measures
    print("   Computing centrality measures...")

    # In-degree centrality (who is most cited)
    in_degree_centrality = nx.in_degree_centrality(G)

    # Out-degree centrality (who cites most)
    out_degree_centrality = nx.out_degree_centrality(G)

    # Betweenness centrality (who bridges different clusters)
    betweenness = nx.betweenness_centrality(G)

    # PageRank (influence accounting for who cites you)
    pagerank = nx.pagerank(G, weight='weight')

    # Eigenvector centrality (connected to well-connected nodes)
    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
    except:
        eigenvector = {n: 0 for n in G.nodes()}

    # Store top 20 for each metric
    metrics['top_cited'] = sorted(in_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:20]
    metrics['top_citers'] = sorted(out_degree_centrality.items(), key=lambda x: x[1], reverse=True)[:20]
    metrics['top_betweenness'] = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:20]
    metrics['top_pagerank'] = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:20]
    metrics['top_eigenvector'] = sorted(eigenvector.items(), key=lambda x: x[1], reverse=True)[:20]

    # Node-level metrics dictionary
    node_metrics = {}
    for node in G.nodes():
        node_metrics[node] = {
            'in_degree': in_degrees[node],
            'out_degree': out_degrees[node],
            'in_degree_centrality': in_degree_centrality[node],
            'out_degree_centrality': out_degree_centrality[node],
            'betweenness': betweenness[node],
            'pagerank': pagerank[node],
            'eigenvector': eigenvector.get(node, 0)
        }

    # Community detection (on undirected version)
    print("   Detecting communities...")
    G_undirected = G.to_undirected()
    try:
        from networkx.algorithms.community import louvain_communities
        communities = louvain_communities(G_undirected, weight='weight', seed=42)
        metrics['num_communities'] = len(communities)
        metrics['communities'] = [list(c) for c in communities]
    except:
        # Fallback to connected components
        components = list(nx.connected_components(G_undirected))
        metrics['num_communities'] = len(components)
        metrics['communities'] = [list(c) for c in components]

    # Reciprocity (mutual citations)
    metrics['reciprocity'] = nx.reciprocity(G)

    print(f"   Metrics calculated")
    return metrics, node_metrics


def analyze_citation_patterns(G, edge_details, names_dict, author_texts):
    """Analyze specific citation patterns."""
    print("Analyzing citation patterns...")

    analysis = {}

    # Co-citation analysis: who is cited together
    print("   Computing co-citation matrix...")
    co_citations = defaultdict(lambda: defaultdict(int))

    # Group citations by text
    citations_by_text = defaultdict(set)
    for edge in edge_details:
        citations_by_text[edge['text_id']].add(edge['target'])

    # Count co-occurrences
    for text_id, cited_set in citations_by_text.items():
        cited_list = list(cited_set)
        for i, a in enumerate(cited_list):
            for b in cited_list[i+1:]:
                co_citations[a][b] += 1
                co_citations[b][a] += 1

    # Top co-cited pairs
    co_cited_pairs = []
    seen = set()
    for a in co_citations:
        for b, count in co_citations[a].items():
            pair = tuple(sorted([a, b]))
            if pair not in seen:
                seen.add(pair)
                co_cited_pairs.append({
                    'person_a': names_dict.get(a, a),
                    'person_b': names_dict.get(b, b),
                    'id_a': a,
                    'id_b': b,
                    'co_citation_count': count
                })

    co_cited_pairs.sort(key=lambda x: x['co_citation_count'], reverse=True)
    analysis['top_co_cited'] = co_cited_pairs[:30]

    # Citation diversity per author
    print("   Computing author citation profiles...")
    author_profiles = {}
    for author, texts in author_texts.items():
        # Get all persons cited by this author
        cited_by_author = set()
        for edge in edge_details:
            if edge['source'] == author:
                cited_by_author.add(edge['target'])

        author_profiles[author] = {
            'name': names_dict.get(author, author),
            'num_texts': len(texts),
            'unique_citations': len(cited_by_author),
            'cited_persons': [names_dict.get(p, p) for p in cited_by_author]
        }

    analysis['author_profiles'] = author_profiles

    # Most cited persons overall
    citation_counts = Counter(edge['target'] for edge in edge_details)
    analysis['most_cited'] = [
        {'id': pid, 'name': names_dict.get(pid, pid), 'count': count}
        for pid, count in citation_counts.most_common(30)
    ]

    print(f"   Pattern analysis complete")
    return analysis


def generate_enhanced_visualization(G, metrics, names_dict, output_path):
    """Generate enhanced interactive visualization.

    For large networks (>300 nodes), filters to degree >= 2 to reduce clutter.
    All nodes remain in data exports regardless.
    """
    print("Generating enhanced visualization...")

    # For large networks, create a filtered subgraph for visualization
    n_total = G.number_of_nodes()
    if n_total > 300:
        min_degree = 2
        keep = {n for n, d in G.degree() if d >= min_degree}
        # Always keep authors (they have outgoing edges)
        keep.update(n for n in G.nodes() if G.nodes[n].get('node_type') == 'author')
        G_viz = G.subgraph(keep).copy()
        print(f"  Filtered for visualization: {G_viz.number_of_nodes()} nodes "
              f"(from {n_total}, showing degree >= {min_degree} + all authors)")
    else:
        G_viz = G

    # Assign communities as colors
    community_map = {}
    for i, community in enumerate(metrics.get('communities', [])):
        for node in community:
            community_map[node] = i

    net = Network(
        height="95vh",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="#eee",
        select_menu=True,
        filter_menu=True,
        cdn_resources='remote'
    )

    # Physics settings scaled to visualization size
    n = G_viz.number_of_nodes()
    if n > 400:
        net.barnes_hut(gravity=-4000, central_gravity=0.3, spring_length=250,
                       spring_strength=0.01, damping=0.4)
    elif n > 200:
        net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=200,
                       spring_strength=0.03, damping=0.2)
    else:
        net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=200,
                       spring_strength=0.05, damping=0.09)

    # Calculate node sizes based on degree
    degrees = dict(G_viz.degree())
    max_degree = max(degrees.values()) if degrees else 1

    colors = COMMUNITY_COLORS

    for node in G_viz.nodes():
        node_data = G_viz.nodes[node]
        label = node_data.get('label', node)
        node_type = node_data.get('node_type', 'unknown')
        community = community_map.get(node, 0)

        size = 10 + (degrees.get(node, 0) / max_degree) * 40
        color = colors[community % len(colors)]

        in_deg = G_viz.in_degree(node)
        out_deg = G_viz.out_degree(node)
        birth = node_data.get('birth_year', 'N/A')
        tooltip = f"""
        <b>{label}</b><br>
        Type: {node_type}<br>
        Birth: {birth}<br>
        Cited by: {in_deg}<br>
        Cites: {out_deg}<br>
        Community: {community}
        """

        shape = 'square' if node_type == 'author' else 'dot'

        net.add_node(
            node,
            label=label,
            title=tooltip,
            size=size,
            color=color,
            shape=shape,
            borderWidth=2,
            borderWidthSelected=4
        )

    for source, target, data in G_viz.edges(data=True):
        weight = data.get('weight', 1)
        net.add_edge(
            source,
            target,
            value=weight,
            title=f"Citations: {weight}",
            arrows='to'
        )

    net.write_html(str(output_path))
    print(f"   Visualization saved to {output_path}")


def export_results(G, metrics, node_metrics, analysis, names_dict, person_metadata, output_dir):
    """Export all results to various formats."""
    print("Exporting results...")

    output_dir.mkdir(exist_ok=True)

    # 1. Network metrics summary (JSON)
    summary = {
        'generated': datetime.now().isoformat(),
        'network_stats': {
            'nodes': metrics['nodes'],
            'edges': metrics['edges'],
            'density': metrics['density'],
            'num_authors': metrics['num_authors'],
            'num_cited_only': metrics['num_cited_only'],
            'num_communities': metrics['num_communities'],
            'reciprocity': metrics['reciprocity'],
            'avg_in_degree': metrics['avg_in_degree'],
            'avg_out_degree': metrics['avg_out_degree']
        },
        'top_cited': [
            {'id': id, 'name': names_dict.get(id, id), 'centrality': score}
            for id, score in metrics['top_cited']
        ],
        'top_pagerank': [
            {'id': id, 'name': names_dict.get(id, id), 'pagerank': score}
            for id, score in metrics['top_pagerank']
        ],
        'top_betweenness': [
            {'id': id, 'name': names_dict.get(id, id), 'betweenness': score}
            for id, score in metrics['top_betweenness']
        ]
    }

    with open(output_dir / 'network_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # 2. Node metrics (CSV)
    node_rows = []
    for node, m in node_metrics.items():
        node_data = G.nodes[node]
        node_rows.append({
            'id': node,
            'name': names_dict.get(node, node),
            'node_type': node_data.get('node_type', ''),
            'birth_year': node_data.get('birth_year', ''),
            'birth_place': node_data.get('birth_place', ''),
            'in_degree': m['in_degree'],
            'out_degree': m['out_degree'],
            'betweenness': round(m['betweenness'], 6),
            'pagerank': round(m['pagerank'], 6),
            'eigenvector': round(m['eigenvector'], 6)
        })

    df_nodes = pd.DataFrame(node_rows)
    df_nodes = df_nodes.sort_values('pagerank', ascending=False)
    df_nodes.to_csv(output_dir / 'node_metrics.csv', index=False, encoding='utf-8')

    # 3. Edge list (CSV)
    edge_rows = []
    for source, target, data in G.edges(data=True):
        edge_rows.append({
            'source_id': source,
            'source_name': names_dict.get(source, source),
            'target_id': target,
            'target_name': names_dict.get(target, target),
            'weight': data.get('weight', 1)
        })

    df_edges = pd.DataFrame(edge_rows)
    df_edges.to_csv(output_dir / 'edges.csv', index=False, encoding='utf-8')

    # 4. Co-citation analysis (CSV)
    df_cocite = pd.DataFrame(analysis['top_co_cited'])
    df_cocite.to_csv(output_dir / 'co_citations.csv', index=False, encoding='utf-8')

    # 5. Most cited (CSV)
    df_cited = pd.DataFrame(analysis['most_cited'])
    df_cited.to_csv(output_dir / 'most_cited.csv', index=False, encoding='utf-8')

    # 6. Author profiles (JSON)
    with open(output_dir / 'author_profiles.json', 'w', encoding='utf-8') as f:
        json.dump(analysis['author_profiles'], f, indent=2, ensure_ascii=False)

    # 7. Communities (JSON)
    communities_data = []
    for i, community in enumerate(metrics.get('communities', [])):
        members = [
            {'id': m, 'name': names_dict.get(m, m)}
            for m in community
        ]
        communities_data.append({
            'community_id': i,
            'size': len(community),
            'members': members
        })

    with open(output_dir / 'communities.json', 'w', encoding='utf-8') as f:
        json.dump(communities_data, f, indent=2, ensure_ascii=False)

    # 8. GEXF for Gephi (clean None values first)
    G_clean = G.copy()
    for node in G_clean.nodes():
        for key, value in list(G_clean.nodes[node].items()):
            if value is None:
                G_clean.nodes[node][key] = ''
            else:
                G_clean.nodes[node][key] = str(value)
    nx.write_gexf(G_clean, output_dir / 'network.gexf')

    print(f"   Results exported to {output_dir}/")


def print_report(metrics, analysis, names_dict):
    """Print summary report to console."""
    print("\n" + "="*70)
    print("NETWORK ANALYSIS REPORT: REVISTA SITIO")
    print("="*70)

    print(f"\nBASIC STATISTICS")
    print(f"   Nodes: {metrics['nodes']}")
    print(f"   Edges: {metrics['edges']}")
    print(f"   Density: {metrics['density']:.4f}")
    print(f"   Authors (with outgoing): {metrics['num_authors']}")
    print(f"   Cited only (no outgoing): {metrics['num_cited_only']}")
    print(f"   Communities detected: {metrics['num_communities']}")
    print(f"   Reciprocity: {metrics['reciprocity']:.4f}")

    print(f"\nTOP 10 MOST CITED (In-Degree Centrality)")
    for i, (pid, score) in enumerate(metrics['top_cited'][:10], 1):
        name = names_dict.get(pid, pid)
        print(f"   {i:2}. {name:<30} (score: {score:.4f})")

    print(f"\nTOP 10 AUTHORS BY CITATIONS MADE (Out-Degree)")
    for i, (pid, score) in enumerate(metrics['top_citers'][:10], 1):
        name = names_dict.get(pid, pid)
        print(f"   {i:2}. {name:<30} (score: {score:.4f})")

    print(f"\nTOP 10 BRIDGE FIGURES (Betweenness Centrality)")
    for i, (pid, score) in enumerate(metrics['top_betweenness'][:10], 1):
        name = names_dict.get(pid, pid)
        print(f"   {i:2}. {name:<30} (score: {score:.4f})")

    print(f"\nTOP 10 INFLUENTIAL (PageRank)")
    for i, (pid, score) in enumerate(metrics['top_pagerank'][:10], 1):
        name = names_dict.get(pid, pid)
        print(f"   {i:2}. {name:<30} (score: {score:.4f})")

    print(f"\nTOP 10 CO-CITED PAIRS")
    for i, pair in enumerate(analysis['top_co_cited'][:10], 1):
        print(f"   {i:2}. {pair['person_a']:<20} + {pair['person_b']:<20} ({pair['co_citation_count']} texts)")

    print("\n" + "="*70)


def run_network_analysis(citations, persons, output_dir):
    """Run full network analysis pipeline."""
    output_dir.mkdir(parents=True, exist_ok=True)
    names_dict = {pid: data['name'] for pid, data in persons.items()}
    person_metadata = persons

    G, edge_details, author_texts = build_citation_network(citations, persons)
    if G.number_of_nodes() == 0:
        print(f"  No nodes in network for {citations['issue_id']}. Skipping.")
        return

    metrics, node_metrics = calculate_network_metrics(G)
    analysis = analyze_citation_patterns(G, edge_details, names_dict, author_texts)
    generate_enhanced_visualization(G, metrics, names_dict, output_dir / 'network_visualization.html')
    export_results(G, metrics, node_metrics, analysis, names_dict, person_metadata, output_dir)
    print_report(metrics, analysis, names_dict)
