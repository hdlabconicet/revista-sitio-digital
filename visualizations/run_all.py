"""Pipeline runner for all SITIO visualization analyses.

Usage:
    python -m visualizations.run_all                          # Run everything
    python -m visualizations.run_all --issue issue_1          # Single issue
    python -m visualizations.run_all --analysis network       # Single analysis type
    python -m visualizations.run_all --issue issue_1 --analysis network
"""

import argparse
from pathlib import Path

from .config import ISSUE_FILES, OUTPUT_DIR, PROJECT_ROOT
from .tei_parser import (
    get_root, load_person_data, load_bibl_data,
    extract_citations, merge_citations,
)
from .network_analysis import run_network_analysis
from .prosopography_analysis import run_prosopography_analysis
from .integrated_analysis import run_integrated_analysis
from .export_sigma import export_sigma_json
from .export_figures import export_figures_json
from .export_affinities import export_affinities_json
from .export_communities import export_communities_json
from .export_flows import export_flows_json
from .export_shadows import export_shadows_json
from .bibliography_analysis import run_bibliography_analysis
from .comparative_analysis import run_comparative_analysis


ANALYSIS_TYPES = ['network', 'prosopography', 'integrated', 'bibliography', 'comparative']


def run_issue(issue_id, filename, persons, bibls, analyses, output_base):
    """Run selected analyses for a single issue."""
    print(f"\n{'='*60}")
    print(f"  Processing {issue_id} ({filename})")
    print(f"{'='*60}")

    root = get_root(filename)
    citations = extract_citations(root, issue_id)
    issue_output = output_base / issue_id

    print(f"  Extracted: {len(citations['person_refs'])} person refs, "
          f"{len(citations['title_refs'])} title refs, "
          f"{len(citations['divs'])} divs")

    if 'network' in analyses:
        print(f"\n--- Network Analysis: {issue_id} ---")
        run_network_analysis(citations, persons, issue_output / "network")

    if 'prosopography' in analyses:
        print(f"\n--- Prosopography Analysis: {issue_id} ---")
        run_prosopography_analysis(citations, persons, issue_output / "prosopography")

    if 'integrated' in analyses:
        print(f"\n--- Integrated Analysis: {issue_id} ---")
        run_integrated_analysis(citations, persons, issue_output / "integrated")

    if 'bibliography' in analyses:
        print(f"\n--- Bibliography Analysis: {issue_id} ---")
        run_bibliography_analysis(citations, persons, bibls, issue_output / "bibliography")

    return citations


def main():
    parser = argparse.ArgumentParser(description='SITIO Visualization Pipeline')
    parser.add_argument('--issue', type=str, help='Single issue (e.g., issue_1)')
    parser.add_argument('--analysis', type=str, help='Single analysis type (network, prosopography, integrated)')
    parser.add_argument('--no-corpus', action='store_true', help='Skip full corpus analysis')
    args = parser.parse_args()

    # Determine which issues and analyses to run
    if args.issue:
        if args.issue not in ISSUE_FILES:
            print(f"Unknown issue: {args.issue}. Valid: {list(ISSUE_FILES.keys())}")
            return
        issues = {args.issue: ISSUE_FILES[args.issue]}
    else:
        issues = ISSUE_FILES

    if args.analysis:
        if args.analysis not in ANALYSIS_TYPES:
            print(f"Unknown analysis: {args.analysis}. Valid: {ANALYSIS_TYPES}")
            return
        analyses = [args.analysis]
    else:
        analyses = ANALYSIS_TYPES

    print("SITIO Visualization Pipeline")
    print(f"  Issues: {list(issues.keys())}")
    print(f"  Analyses: {analyses}")
    print()

    # 1. Load shared reference data (once)
    print("Loading reference data...")
    persons = load_person_data()
    bibls = load_bibl_data()
    print(f"  {len(persons)} persons, {len(bibls)} bibliography entries\n")

    # 2. Per-issue analysis
    all_citations = []
    for issue_id, filename in issues.items():
        citations = run_issue(issue_id, filename, persons, bibls, analyses, OUTPUT_DIR)
        all_citations.append(citations)

    # 3. Full corpus analysis (skip if single issue or --no-corpus)
    if len(issues) > 1 and not args.no_corpus:
        print(f"\n{'='*60}")
        print("  Processing full_corpus (all issues combined)")
        print(f"{'='*60}")

        merged = merge_citations(all_citations)
        corpus_output = OUTPUT_DIR / "full_corpus"

        print(f"  Merged: {len(merged['person_refs'])} person refs, "
              f"{len(merged['title_refs'])} title refs")

        if 'network' in analyses:
            print(f"\n--- Network Analysis: full_corpus ---")
            run_network_analysis(merged, persons, corpus_output / "network")

        if 'prosopography' in analyses:
            print(f"\n--- Prosopography Analysis: full_corpus ---")
            run_prosopography_analysis(merged, persons, corpus_output / "prosopography")

        if 'integrated' in analyses:
            print(f"\n--- Integrated Analysis: full_corpus ---")
            run_integrated_analysis(merged, persons, corpus_output / "integrated")

        if 'bibliography' in analyses:
            print(f"\n--- Bibliography Analysis: full_corpus ---")
            run_bibliography_analysis(merged, persons, bibls, corpus_output / "bibliography")

    # 4. Comparative analysis (requires all issues)
    if len(issues) > 1 and 'comparative' in analyses:
        print(f"\n{'='*60}")
        print("  Comparative Analysis (cross-issue)")
        print(f"{'='*60}")

        all_issue_dict = {c['issue_id']: c for c in all_citations}
        run_comparative_analysis(all_issue_dict, persons, OUTPUT_DIR / "comparative")

    # 5. Export frontend visualization data
    if len(issues) > 1:
        print(f"\n{'='*60}")
        print("  Exporting frontend visualization data")
        print(f"{'='*60}")
        export_sigma_json(PROJECT_ROOT / "sigma-viz" / "data" / "sigma_graph.json")
        export_figures_json(PROJECT_ROOT / "timeline" / "data" / "figures_data.json")
        export_affinities_json(PROJECT_ROOT / "contributors" / "data" / "affinities_data.json")
        export_communities_json(PROJECT_ROOT / "map" / "data" / "communities_data.json")
        export_flows_json(PROJECT_ROOT / "flows" / "data" / "flows_data.json")
        export_shadows_json(PROJECT_ROOT / "shadows" / "data" / "shadows_data.json")

    print(f"\nPipeline complete. Outputs in: {OUTPUT_DIR.absolute()}")


if __name__ == "__main__":
    main()
