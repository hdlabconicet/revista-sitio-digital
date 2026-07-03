#!/usr/bin/env python3
"""Build the Bibliografía page from TEI/listBibl.xml.

Generates `_recursos/05-biblio.md` (permalink /biblio/): the works cited across
the six issues of Revista SITIO, sorted by author, with Wikidata links where
available. The script owns the whole file (same pattern as the índice in
build_edition.py) — regenerate after editing listBibl.xml.

Usage (from the repo root or the TEI/ directory):

    python TEI/build_biblio.py

Dependencies: lxml.
"""

import html
import re
import unicodedata
from pathlib import Path

import lxml.etree as ET

TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}

TEI_DIR = Path(__file__).resolve().parent
REPO = TEI_DIR.parent
OUT = REPO / "_recursos" / "05-biblio.md"

SORT_ARTICLES = re.compile(r"^(el|la|los|las|un|una|unos|unas|the|le|les|l')\s+", re.I)


def collapse_ws(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def md_escape(text):
    text = html.escape(collapse_ws(text), quote=False)
    return re.sub(r"([*_\[\]])", r"\\\1", text)


def sort_key(text):
    text = SORT_ARTICLES.sub("", collapse_ws(text).strip("\"'«»“”‘’"))
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def get_year(bibl):
    date = bibl.find("tei:date", NS)
    if date is None:
        return ""
    for attr in ("when", "notBefore", "from", "to", "notAfter"):
        v = date.get(attr)
        if v:
            m = re.match(r"\s*(-?\d{3,4})", v)
            if m:
                return m.group(1)
    if date.text:
        m = re.search(r"(-?\d{3,4})", date.text)
        if m:
            return m.group(1)
    return ""


def format_authors(bibl):
    names = [collapse_ws("".join(a.itertext())) for a in bibl.findall("tei:author", NS)]
    names = [n for n in names if n]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " y " + names[-1]


def format_titles(bibl):
    titles = bibl.findall("tei:title", NS)
    if not titles:
        return "", ""
    main = collapse_ws("".join(titles[0].itertext()))
    # Articles (level="a") go in quotes; books/journals in italics.
    if titles[0].get("level") == "a":
        parts = [f"&ldquo;{md_escape(main.strip('“”"'))}&rdquo;"]
    else:
        parts = [f"*{md_escape(main)}*"]
    for extra in titles[1:]:
        text = md_escape(collapse_ws("".join(extra.itertext())))
        if not text:
            continue
        if (extra.get("type") or "") == "translated":
            parts.append(f" [*{text}*]")
        elif extra.get("level") in ("j", "m", "s"):
            parts.append(f", en *{text}*")
        else:
            parts.append(f", *{text}*")
    return "".join(parts), main


def format_entry(bibl):
    authors = format_authors(bibl)
    titles_md, main_title = format_titles(bibl)
    year = get_year(bibl)

    pieces = []
    if authors:
        pieces.append(md_escape(authors) + ".")
    if year:
        pieces.append(f"({year}).")
    pieces.append(titles_md + ".")

    wikidata = ""
    for idno in bibl.findall("tei:idno", NS):
        if "wikidata" in (idno.get("subtype") or "") and idno.text:
            wikidata = collapse_ws(idno.text)
            break
    if wikidata:
        pieces.append(f"[(Wikidata)]({wikidata})")

    key = sort_key(authors) if authors else sort_key(main_title)
    return key, " ".join(pieces)


HEADER = """\
---
layout: page
title: Bibliografía
permalink: /biblio/
type: extras
description: Fuente, bibliografía citada y lecturas sobre Revista SITIO
icon: book
---

### Fuente

* *Revista SITIO*, núms. 1&ndash;6. Buenos Aires, 1981&ndash;1987. Dirigida por Ramón Alcalde, Eduardo Grüner, Luis Gusmán, Jorge Jinkis, Mario Levin y Luis Thonis.

### Bibliografía citada

Obras citadas o mencionadas a lo largo de los seis números de la revista,
según la codificación TEI ({count} entradas). Las entradas enlazan a Wikidata
cuando la obra está identificada allí.
"""

FOOTER = """
### Bibliografía crítica

*Revista SITIO* se inscribe en el campo de las revistas culturales e intelectuales argentinas de los años de la dictadura y la transición democrática, junto a publicaciones como *Punto de Vista*, *Babel* y, en la tradición previa, *Contorno*.

<!-- TODO: los editores completarán esta sección con la bibliografía secundaria sobre
     SITIO y sobre las revistas culturales argentinas del período. -->

*Sección en preparación.*
"""


def main():
    root = ET.parse(str(TEI_DIR / "listBibl.xml")).getroot()
    bibls = root.findall(".//tei:bibl", NS)
    entries = sorted(format_entry(b) for b in bibls)

    lines = [HEADER.format(count=len(entries))]
    current_letter = None
    for key, entry in entries:
        letter = key[:1].upper()
        if not letter.isalpha():
            letter = "#"
        if letter != current_letter:
            current_letter = letter
            lines.append(f"\n#### {letter}\n")
        lines.append(f"* {entry}")
    lines.append(FOOTER)

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(REPO)} with {len(entries)} entries.")


if __name__ == "__main__":
    main()
