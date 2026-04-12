"""Cross-issue comparative analysis for Revista SITIO.

Compares citation patterns across the 5 issues (1981-1987).
"""

import pandas as pd
import json
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from .config import (
    ISSUE_YEARS, REGION_COLORS, MPL_STYLE, MPL_DPI,
)


def run_comparative_analysis(all_issue_data, persons, output_dir):
    """Run cross-issue comparative analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)

    issue_ids = sorted(all_issue_data.keys(), key=lambda x: ISSUE_YEARS.get(x, 0))

    # --- Per-issue summaries ---
    issue_summaries = {}
    all_person_counts = {}

    for issue_id in issue_ids:
        data = all_issue_data[issue_id]
        year = ISSUE_YEARS.get(issue_id, 0)

        person_counter = Counter(ref['target_person'] for ref in data['person_refs'])
        all_person_counts[issue_id] = person_counter

        region_counter = Counter()
        country_counter = Counter()
        birth_years = []
        for pid in data['cited_person_ids']:
            pdata = persons.get(pid, {})
            if pdata.get('region'):
                region_counter[pdata['region']] += 1
            if pdata.get('country'):
                country_counter[pdata['country']] += 1
            if pdata.get('birth_year'):
                birth_years.append(pdata['birth_year'])

        type_counter = Counter(d['type'] for d in data['divs'])

        total_regions = sum(region_counter.values()) or 1
        issue_summaries[issue_id] = {
            'year': year,
            'num_person_refs': len(data['person_refs']),
            'num_title_refs': len(data['title_refs']),
            'num_unique_persons': len(data['cited_person_ids']),
            'num_divs': len(data['divs']),
            'num_authors': len(data['author_ids']),
            'top_10_cited': [
                {'id': pid, 'name': persons.get(pid, {}).get('name', pid), 'count': c}
                for pid, c in person_counter.most_common(10)
            ],
            'region_pct': {r: round(c / total_regions * 100, 1) for r, c in region_counter.most_common()},
            'country_top5': dict(country_counter.most_common(5)),
            'median_birth_year': int(sorted(birth_years)[len(birth_years)//2]) if birth_years else None,
            'genre_composition': dict(type_counter),
        }

    # --- Recurring figures ---
    person_issues = defaultdict(set)
    for issue_id, counter in all_person_counts.items():
        for pid in counter:
            person_issues[pid].add(issue_id)

    recurring = []
    for pid, issues in person_issues.items():
        if len(issues) >= 2:
            pdata = persons.get(pid, {})
            total = sum(all_person_counts[i].get(pid, 0) for i in issues)
            recurring.append({
                'person_id': pid,
                'name': pdata.get('name', pid),
                'country': pdata.get('country', ''),
                'num_issues': len(issues),
                'issues': sorted(issues, key=lambda x: ISSUE_YEARS.get(x, 0)),
                'total_citations': total,
            })
    recurring.sort(key=lambda x: x['total_citations'], reverse=True)

    df_recurring = pd.DataFrame(recurring)
    df_recurring.to_csv(output_dir / 'recurring_figures.csv', index=False, encoding='utf-8')

    # --- Charts ---
    if HAS_MATPLOTLIB:
        if MPL_STYLE in plt.style.available:
            plt.style.use(MPL_STYLE)

        labels = [f"{iid}\n({ISSUE_YEARS.get(iid, '')})" for iid in issue_ids]

        # 1. Top cited persons per issue
        fig, axes = plt.subplots(1, len(issue_ids), figsize=(4 * len(issue_ids), 6), sharey=False)
        if len(issue_ids) == 1:
            axes = [axes]
        for ax, iid in zip(axes, issue_ids):
            top5 = issue_summaries[iid]['top_10_cited'][:5]
            names = [t['name'][:20] for t in top5]
            counts = [t['count'] for t in top5]
            ax.barh(names[::-1], counts[::-1], color='#3498db', edgecolor='white')
            ax.set_title(f"{iid}\n({ISSUE_YEARS.get(iid, '')})", fontsize=11)
            ax.set_xlabel('Citations')
        plt.suptitle('Top 5 Cited Figures per Issue', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        fig.savefig(output_dir / 'evolution_persons.png', dpi=MPL_DPI, bbox_inches='tight')
        plt.close(fig)

        # 2. Geographic focus evolution
        all_regions = set()
        for s in issue_summaries.values():
            all_regions.update(s['region_pct'].keys())
        all_regions = sorted(all_regions)

        fig, ax = plt.subplots(figsize=(12, 6))
        bottom = [0] * len(issue_ids)
        for region in all_regions:
            values = [issue_summaries[iid]['region_pct'].get(region, 0) for iid in issue_ids]
            color = REGION_COLORS.get(region, '#95a5a6')
            ax.bar(labels, values, bottom=bottom, label=region, color=color, edgecolor='white')
            bottom = [b + v for b, v in zip(bottom, values)]
        ax.set_ylabel('Percentage (%)', fontsize=12)
        ax.set_title('Geographic Focus Evolution (1981-1987)', fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
        plt.tight_layout()
        fig.savefig(output_dir / 'evolution_geography.png', dpi=MPL_DPI, bbox_inches='tight')
        plt.close(fig)

        # 3. Citation volume evolution
        fig, ax = plt.subplots(figsize=(10, 6))
        sizes = [issue_summaries[iid]['num_unique_persons'] for iid in issue_ids]
        refs = [issue_summaries[iid]['num_person_refs'] for iid in issue_ids]
        x = range(len(issue_ids))
        ax.bar(x, refs, width=0.4, label='Total person refs', color='#3498db', align='center')
        ax.bar([i + 0.4 for i in x], sizes, width=0.4, label='Unique persons', color='#2ecc71', align='center')
        ax.set_xticks([i + 0.2 for i in x])
        ax.set_xticklabels(labels)
        ax.set_ylabel('Count', fontsize=12)
        ax.set_title('Citation Volume Evolution', fontsize=14, fontweight='bold')
        ax.legend()
        plt.tight_layout()
        fig.savefig(output_dir / 'evolution_volume.png', dpi=MPL_DPI)
        plt.close(fig)

        # 4. Median birth year evolution
        fig, ax = plt.subplots(figsize=(10, 6))
        medians = [issue_summaries[iid]['median_birth_year'] for iid in issue_ids]
        valid = [(l, m) for l, m in zip(labels, medians) if m]
        if valid:
            ax.plot([v[0] for v in valid], [v[1] for v in valid], 'o-', markersize=10,
                    color='#e74c3c', linewidth=2)
            ax.set_ylabel('Median Birth Year of Cited Figures', fontsize=12)
            ax.set_title('Temporal Focus Evolution', fontsize=14, fontweight='bold')
            plt.tight_layout()
            fig.savefig(output_dir / 'evolution_temporal.png', dpi=MPL_DPI)
        plt.close(fig)

    # --- Summary JSON ---
    report = {
        'generated': datetime.now().isoformat(),
        'issue_summaries': issue_summaries,
        'recurring_figures_count': len(recurring),
        'recurring_top10': recurring[:10],
    }

    with open(output_dir / 'comparative_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    # Print report
    print(f"\n  Comparative Analysis")
    print(f"  Recurring figures (2+ issues): {len(recurring)}")
    print(f"  Top 5 recurring:")
    for r in recurring[:5]:
        print(f"    {r['name']}: {r['num_issues']} issues, {r['total_citations']} citations")
    for iid in issue_ids:
        s = issue_summaries[iid]
        print(f"\n  {iid} ({s['year']}): {s['num_unique_persons']} unique persons, "
              f"median birth {s['median_birth_year']}")
        top3 = ', '.join(t['name'] for t in s['top_10_cited'][:3])
        print(f"    Top cited: {top3}")
