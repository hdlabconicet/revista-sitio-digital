"""Prosopographical analysis for Revista SITIO TEI corpus.

Refactored from visualizations_1/prosopography_analysis.py.
"""

import pandas as pd
import json
from collections import Counter
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
    NS, HISTORICAL_PERIODS, REGION_MAPPINGS,
    MPL_STYLE, MPL_DPI,
)
from .tei_parser import load_person_data, get_historical_period


def calculate_statistics(df):
    """Calculate summary statistics."""
    stats = {}

    # Temporal statistics
    valid_years = df[df['birth_year'].notna()]['birth_year']
    if len(valid_years) > 0:
        stats['temporal'] = {
            'min_year': int(valid_years.min()),
            'max_year': int(valid_years.max()),
            'median_year': int(valid_years.median()),
            'mean_year': round(valid_years.mean(), 1),
            'std_year': round(valid_years.std(), 1),
            'count_with_dates': len(valid_years),
            'count_without_dates': len(df) - len(valid_years)
        }

    # Geographic statistics
    stats['geographic'] = {
        'countries': df['country'].value_counts().to_dict(),
        'regions': df['region'].value_counts().to_dict(),
        'num_countries': df['country'].nunique(),
        'num_regions': df['region'].nunique()
    }

    # Period statistics
    stats['periods'] = df['period'].value_counts().to_dict()

    # Lifespan statistics
    valid_lifespans = df[df['lifespan'].notna()]['lifespan']
    if len(valid_lifespans) > 0:
        stats['lifespan'] = {
            'mean': round(valid_lifespans.mean(), 1),
            'median': int(valid_lifespans.median()),
            'min': int(valid_lifespans.min()),
            'max': int(valid_lifespans.max())
        }

    return stats


def generate_visualizations(df, output_dir):
    """Generate prosopographical visualizations."""
    if not HAS_MATPLOTLIB:
        print("  Skipping visualizations (matplotlib not available)")
        return

    print("Generating visualizations...")

    # Set style
    if MPL_STYLE in plt.style.available:
        plt.style.use(MPL_STYLE)

    # 1. Birth Year Distribution (Histogram)
    fig, ax = plt.subplots(figsize=(12, 6))
    valid_years = df[df['birth_year'].notna() & (df['birth_year'] > 0)]['birth_year']

    if len(valid_years) > 0:
        ax.hist(valid_years, bins=30, edgecolor='white', alpha=0.7, color='#3498db')
        ax.axvline(valid_years.median(), color='#e74c3c', linestyle='--', linewidth=2, label=f'Median: {int(valid_years.median())}')
        ax.set_xlabel('Birth Year', fontsize=12)
        ax.set_ylabel('Number of Cited Figures', fontsize=12)
        ax.set_title('Temporal Distribution of Cited Figures in Revista SITIO', fontsize=14, fontweight='bold')
        ax.legend()
        plt.tight_layout()
        fig.savefig(output_dir / 'temporal_distribution.png', dpi=MPL_DPI)
        plt.close(fig)

    # 2. Historical Period Distribution (Bar chart)
    fig, ax = plt.subplots(figsize=(12, 6))
    period_counts = df['period'].value_counts()

    # Order by timeline
    period_order = [p[2] for p in HISTORICAL_PERIODS] + ['21st Century', 'Unknown']
    period_counts = period_counts.reindex([p for p in period_order if p in period_counts.index])

    colors = plt.cm.viridis(range(0, 256, 256 // len(period_counts)))
    bars = ax.barh(period_counts.index, period_counts.values, color=colors, edgecolor='white')
    ax.set_xlabel('Number of Cited Figures', fontsize=12)
    ax.set_title('Historical Periods of Cited Figures', fontsize=14, fontweight='bold')

    # Add value labels
    for bar, val in zip(bars, period_counts.values):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, str(val), va='center', fontsize=10)

    plt.tight_layout()
    fig.savefig(output_dir / 'period_distribution.png', dpi=MPL_DPI)
    plt.close(fig)

    # 3. Geographic Distribution (Pie chart for regions)
    fig, ax = plt.subplots(figsize=(10, 10))
    region_counts = df['region'].value_counts()

    colors = plt.cm.Set3(range(len(region_counts)))
    wedges, texts, autotexts = ax.pie(
        region_counts.values,
        labels=region_counts.index,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        pctdistance=0.8
    )
    ax.set_title('Geographic Distribution by Region', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig.savefig(output_dir / 'region_distribution.png', dpi=MPL_DPI)
    plt.close(fig)

    # 4. Top Countries (Bar chart)
    fig, ax = plt.subplots(figsize=(12, 8))
    country_counts = df['country'].value_counts().head(15)

    colors = plt.cm.Paired(range(len(country_counts)))
    bars = ax.barh(country_counts.index[::-1], country_counts.values[::-1], color=colors, edgecolor='white')
    ax.set_xlabel('Number of Cited Figures', fontsize=12)
    ax.set_title('Top 15 Countries of Origin', fontsize=14, fontweight='bold')

    for bar, val in zip(bars, country_counts.values[::-1]):
        ax.text(val + 0.3, bar.get_y() + bar.get_height()/2, str(val), va='center', fontsize=10)

    plt.tight_layout()
    fig.savefig(output_dir / 'country_distribution.png', dpi=MPL_DPI)
    plt.close(fig)

    # 5. Timeline: Birth years by decade
    fig, ax = plt.subplots(figsize=(14, 6))
    valid_years = df[df['birth_year'].notna() & (df['birth_year'] > 1400)]['birth_year']

    if len(valid_years) > 0:
        decades = (valid_years // 10) * 10
        decade_counts = decades.value_counts().sort_index()

        ax.bar(decade_counts.index, decade_counts.values, width=8, color='#2ecc71', alpha=0.8, edgecolor='white')
        ax.set_xlabel('Decade', fontsize=12)
        ax.set_ylabel('Number of Figures Born', fontsize=12)
        ax.set_title('Cited Figures by Birth Decade (Post-1400)', fontsize=14, fontweight='bold')

        # Mark key periods
        ax.axvline(1789, color='red', linestyle='--', alpha=0.5, label='French Revolution')
        ax.axvline(1848, color='orange', linestyle='--', alpha=0.5, label='1848 Revolutions')
        ax.axvline(1914, color='darkred', linestyle='--', alpha=0.5, label='WWI')
        ax.legend(fontsize=9)

        plt.tight_layout()
        fig.savefig(output_dir / 'decade_distribution.png', dpi=MPL_DPI)
        plt.close(fig)

    print("  Visualizations saved")


def export_results(df, stats, output_dir):
    """Export all results."""
    print("Exporting results...")

    output_dir.mkdir(exist_ok=True)

    # 1. Full dataset
    df.to_csv(output_dir / 'prosopography_data.csv', index=False, encoding='utf-8')

    # 2. Statistics JSON
    with open(output_dir / 'prosopography_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False, default=str)

    # 3. Country summary
    country_df = df.groupby('country').agg({
        'id': 'count',
        'birth_year': 'median'
    }).rename(columns={'id': 'count', 'birth_year': 'median_birth_year'})
    country_df = country_df.sort_values('count', ascending=False)
    country_df.to_csv(output_dir / 'country_summary.csv', encoding='utf-8')

    # 4. Period summary
    period_df = df.groupby('period').agg({
        'id': 'count',
        'birth_year': ['min', 'max']
    })
    period_df.columns = ['count', 'earliest_birth', 'latest_birth']
    period_df.to_csv(output_dir / 'period_summary.csv', encoding='utf-8')

    # 5. Persons by century (for the modern period)
    df_modern = df[df['birth_year'].notna() & (df['birth_year'] > 1400)].copy()
    df_modern['century'] = ((df_modern['birth_year'] // 100) + 1).astype(int).astype(str) + 'th'
    century_df = df_modern.groupby('century')['id'].count().sort_index()
    century_df.to_csv(output_dir / 'century_summary.csv')

    print(f"  Results exported to {output_dir}/")


def print_report(df, stats):
    """Print summary report."""
    print("\n" + "="*70)
    print("PROSOPOGRAPHICAL ANALYSIS: REVISTA SITIO")
    print("="*70)

    print(f"\nOVERVIEW")
    print(f"  Total cited persons: {len(df)}")
    print(f"  With birth dates: {stats['temporal']['count_with_dates']}")
    print(f"  Without birth dates: {stats['temporal']['count_without_dates']}")

    print(f"\nTEMPORAL DISTRIBUTION")
    print(f"  Earliest birth: {stats['temporal']['min_year']}")
    print(f"  Latest birth: {stats['temporal']['max_year']}")
    print(f"  Median birth year: {stats['temporal']['median_year']}")
    print(f"  Mean birth year: {stats['temporal']['mean_year']}")

    print(f"\nHISTORICAL PERIODS (Top 5)")
    sorted_periods = sorted(stats['periods'].items(), key=lambda x: x[1], reverse=True)
    for period, count in sorted_periods[:5]:
        pct = count / len(df) * 100
        print(f"  {period}: {count} ({pct:.1f}%)")

    print(f"\nGEOGRAPHIC DISTRIBUTION")
    print(f"  Number of countries: {stats['geographic']['num_countries']}")
    print(f"  Number of regions: {stats['geographic']['num_regions']}")

    print(f"\nTOP 10 COUNTRIES")
    sorted_countries = sorted(stats['geographic']['countries'].items(), key=lambda x: x[1], reverse=True)
    for country, count in sorted_countries[:10]:
        pct = count / len(df) * 100
        print(f"  {country}: {count} ({pct:.1f}%)")

    print(f"\nREGION BREAKDOWN")
    sorted_regions = sorted(stats['geographic']['regions'].items(), key=lambda x: x[1], reverse=True)
    for region, count in sorted_regions:
        pct = count / len(df) * 100
        print(f"  {region}: {count} ({pct:.1f}%)")

    if 'lifespan' in stats:
        print(f"\nLIFESPAN STATISTICS")
        print(f"  Mean lifespan: {stats['lifespan']['mean']} years")
        print(f"  Median lifespan: {stats['lifespan']['median']} years")

    print("\n" + "="*70)


def run_prosopography_analysis(citations, persons, output_dir):
    """Run prosopography analysis for one issue or full corpus."""
    output_dir.mkdir(parents=True, exist_ok=True)

    cited_ids = citations['cited_person_ids'] | citations['author_ids']
    cited_persons = [
        {'id': pid, **data}
        for pid, data in persons.items()
        if pid in cited_ids
    ]

    if not cited_persons:
        print(f"  No cited persons for {citations['issue_id']}. Skipping.")
        return

    df = pd.DataFrame(cited_persons)
    stats = calculate_statistics(df)
    generate_visualizations(df, output_dir)
    export_results(df, stats, output_dir)
    print_report(df, stats)
