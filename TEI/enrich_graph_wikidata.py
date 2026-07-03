#!/usr/bin/env python3
"""Fill the `wikidata` attribute of sigma-viz nodes from TEI/listPerson.xml.

The visualizations pipeline exports sigma_graph.json without Wikidata URIs
(they get lost upstream of export_sigma), but listPerson.xml has an
<idno type="URI" subtype="wikidata"> for most persons. The sigma-viz detail
panel already renders a Wikidata link whenever the node attribute is set,
so patching the JSON is enough to light the feature up.

Idempotent — safe to re-run, including after regenerating the pipeline.

Usage (from the repo root or the TEI/ directory):

    python TEI/enrich_graph_wikidata.py
"""

import json
from pathlib import Path

import lxml.etree as ET

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
NS = {"tei": TEI_NS}

TEI_DIR = Path(__file__).resolve().parent
REPO = TEI_DIR.parent
GRAPH_JSON = REPO / "sigma-viz" / "data" / "sigma_graph.json"


def load_wikidata_uris():
    root = ET.parse(str(TEI_DIR / "listPerson.xml")).getroot()
    uris = {}
    for person in root.findall(".//tei:person", NS):
        pid = person.get(XML_ID)
        if not pid:
            continue
        for idno in person.findall(".//tei:idno", NS):
            if (idno.get("subtype") or "") == "wikidata" and idno.text:
                uris[pid] = idno.text.strip()
                break
    return uris


def main():
    uris = load_wikidata_uris()
    print(f"Loaded {len(uris)} wikidata URIs from listPerson.xml")

    data = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    filled = 0
    for node in data.get("nodes", []):
        uri = uris.get(node.get("key"))
        if uri and not node["attributes"].get("wikidata"):
            node["attributes"]["wikidata"] = uri
            filled += 1
    GRAPH_JSON.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    total = len(data.get("nodes", []))
    print(f"Filled {filled} nodes; graph now has wikidata on "
          f"{sum(1 for n in data['nodes'] if n['attributes'].get('wikidata'))}/{total} nodes.")


if __name__ == "__main__":
    main()
