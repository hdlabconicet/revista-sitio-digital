"""Export editorial affinity data — citation overlap between SITIO contributors."""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

from .config import ISSUE_FILES, ISSUE_YEARS, OUTPUT_DIR, REGION_COLORS
from .tei_parser import get_root, extract_citations, load_person_data


def export_affinities_json(output_path):
    """Export contributor affinity matrix and profiles."""
    print("Exporting editorial affinities data...")

    persons = load_person_data()

    # Collect per-author citation sets across all issues
    author_citations = defaultdict(set)  # author_id -> set of cited person_ids
    author_citation_counts = defaultdict(Counter)  # author_id -> Counter of cited person_ids
    author_issues = defaultdict(list)
    author_texts = defaultdict(int)
    author_region_counts = defaultdict(Counter)

    for issue_id, filename in ISSUE_FILES.items():
        root = get_root(filename)
        data = extract_citations(root, issue_id)

        for div in data['divs']:
            for aid in div['authors']:
                if issue_id not in author_issues[aid]:
                    author_issues[aid].append(issue_id)
                author_texts[aid] += 1

        for ref in data['person_refs']:
            aid = ref['source_author']
            tid = ref['target_person']
            author_citations[aid].add(tid)
            author_citation_counts[aid][tid] += 1
            region = persons.get(tid, {}).get('region', 'Other/Unknown')
            author_region_counts[aid][region] += 1

    # Filter to authors with at least 5 citations
    active_authors = [aid for aid, cites in author_citations.items() if len(cites) >= 5]
    active_authors.sort(key=lambda x: -len(author_citations[x]))

    # Compute pairwise Jaccard similarity
    matrix = []
    for i, a1 in enumerate(active_authors):
        row = []
        for j, a2 in enumerate(active_authors):
            set1 = author_citations[a1]
            set2 = author_citations[a2]
            intersection = set1 & set2
            union = set1 | set2
            jaccard = len(intersection) / len(union) if union else 0
            shared_count = len(intersection)
            row.append({
                'jaccard': round(jaccard, 3),
                'shared': shared_count,
            })
        matrix.append(row)

    # Build contributor profiles
    contributors = []
    for aid in active_authors:
        pdata = persons.get(aid, {})
        cites = author_citation_counts[aid]
        top_cited = [
            {'id': pid, 'name': persons.get(pid, {}).get('name', pid), 'count': c}
            for pid, c in cites.most_common(10)
        ]
        regions = dict(author_region_counts[aid].most_common())
        total_r = sum(regions.values()) or 1
        top_region = max(regions, key=regions.get) if regions else 'Unknown'

        contributors.append({
            'key': aid,
            'name': pdata.get('name', aid),
            'total_citations': sum(cites.values()),
            'unique_figures': len(author_citations[aid]),
            'num_texts': author_texts[aid],
            'issues': sorted(author_issues[aid], key=lambda x: ISSUE_YEARS.get(x, 0)),
            'top_region': top_region,
            'top_cited': top_cited,
            'region_breakdown': regions,
        })

    # Pre-compute shared figures for each pair (top 10 only, for click detail)
    shared_details = {}
    for i, a1 in enumerate(active_authors):
        for j, a2 in enumerate(active_authors):
            if i >= j:
                continue
            shared = author_citations[a1] & author_citations[a2]
            if not shared:
                continue
            # Sort by combined citation count
            shared_list = []
            for pid in shared:
                count = author_citation_counts[a1][pid] + author_citation_counts[a2][pid]
                shared_list.append({
                    'id': pid,
                    'name': persons.get(pid, {}).get('name', pid),
                    'count': count,
                })
            shared_list.sort(key=lambda x: -x['count'])
            shared_details[f"{i}-{j}"] = shared_list[:10]

    output_data = {
        'contributors': contributors,
        'matrix': matrix,
        'shared_details': shared_details,
        'metadata': {
            'total_contributors': len(contributors),
            'generated': datetime.now().isoformat(),
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False)

    size_kb = output_path.stat().st_size / 1024
    print(f"  Exported: {output_path} ({len(contributors)} contributors, {size_kb:.0f} KB)")


if __name__ == "__main__":
    from .config import PROJECT_ROOT
    export_affinities_json(PROJECT_ROOT / "contributors" / "data" / "affinities_data.json")
