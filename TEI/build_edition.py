#!/usr/bin/env python3
"""Build the Revista SITIO reading edition from the TEI-XML sources.

For each issue, every top-level <body>/<div> (an article / section) becomes one
reading page written to `_txtxpagina/`, and a table of contents is written to
`_pages/02-edicion-digital.html` (permalink /indice/).

Inline annotations are preserved: <persName ref="#id"> gets a balloon tooltip
with the figure's name and dates (resolved against listPerson.xml); <placeName>,
<term> and <bibl> get light styling; editorial <note> elements become
collapsible asides.

Usage (from the repo root or the TEI/ directory):

    python TEI/build_edition.py

Dependencies: lxml (already used by the visualizations pipeline).
"""

import html
import re
from pathlib import Path

import lxml.etree as ET

# --- Paths / constants -------------------------------------------------------
TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
NS = {"tei": TEI_NS}

TEI_DIR = Path(__file__).resolve().parent          # TEI/
REPO = TEI_DIR.parent                               # repo root
OUT_DIR = REPO / "_txtxpagina"
INDICE = REPO / "_pages" / "02-edicion-digital.html"

# (key, filename, human issue label, year)
ISSUES = [
    ("issue_1", "issue_1.xml", "1", 1981),
    ("issue_2", "issue_2.xml", "2", 1982),
    ("issue_3", "issue_3.xml", "3", 1983),
    ("issue_4-5", "issue_4-5.xml", "4-5", 1985),
    ("issue_6", "issue_6.xml", "6", 1987),
]

NOTE_LABELS = {
    "summary": "Resumen editorial",
    "interpretation": "Interpretación",
    "annotation": "Nota",
}

PERSONS = {}  # populated by load_persons()


# --- Helpers -----------------------------------------------------------------
def local(el):
    return ET.QName(el).localname


def esc(text):
    return html.escape(text or "", quote=False)


def esc_attr(text):
    return html.escape(text or "", quote=True)


def collapse_ws(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def fmt_year(y):
    if y is None:
        return ""
    return f"{-y} a.C." if y < 0 else str(y)


def life_span(birth, death):
    if birth is not None and death is not None:
        return f"{fmt_year(birth)}–{fmt_year(death)}"
    if birth is not None:
        return f"n. {fmt_year(birth)}"
    if death is not None:
        return f"m. {fmt_year(death)}"
    return ""


def get_year(date_el):
    if date_el is None:
        return None
    for attr in ("when", "when-iso", "from", "notBefore", "to", "notAfter"):
        v = date_el.get(attr)
        if v:
            m = re.match(r"\s*(-?\d{1,4})", v)
            if m:
                return int(m.group(1))
    if date_el.text:
        m = re.search(r"(-?\d{3,4})", date_el.text)
        if m:
            return int(m.group(1))
    return None


def format_person_name(pn):
    if pn is None:
        return ""
    forenames = [collapse_ws(f.text) for f in pn.findall("tei:forename", NS) if f.text]
    surnames = [collapse_ws(s.text) for s in pn.findall("tei:surname", NS) if s.text]
    if forenames or surnames:
        return collapse_ws(" ".join(forenames + surnames))
    return collapse_ws("".join(pn.itertext()))


def load_persons():
    path = TEI_DIR / "listPerson.xml"
    root = ET.parse(str(path)).getroot()
    for person in root.findall(".//tei:person", NS):
        pid = person.get(XML_ID)
        if not pid:
            continue
        pn = person.find("tei:persName", NS)
        PERSONS[pid] = {
            "name": format_person_name(pn),
            "birth": get_year(person.find("tei:birth/tei:date", NS)),
            "death": get_year(person.find("tei:death/tei:date", NS)),
        }
    return PERSONS


# --- TEI -> HTML -------------------------------------------------------------
def render_children(el):
    out = []
    if el.text:
        out.append(esc(el.text))
    for child in el:
        out.append(render_node(child))
        if child.tail:
            out.append(esc(child.tail))
    return "".join(out)


def person_span(el, inner):
    ref = (el.get("ref") or "").split()
    pid = ref[0].lstrip("#") if ref else ""
    info = PERSONS.get(pid)
    if info and info.get("name"):
        tip = info["name"]
        span = life_span(info.get("birth"), info.get("death"))
        if span:
            tip = f"{tip} ({span})"
        return (
            f'<span class="ann ann-person" data-balloon="{esc_attr(tip)}" '
            f'data-balloon-pos="up">{inner}</span>'
        )
    return f'<span class="ann ann-person">{inner}</span>'


def render_note(el, inner):
    ntype = el.get("type") or ""
    label = NOTE_LABELS.get(ntype, "Nota")
    cls = "ed-note" + (f" ed-{ntype}" if ntype else "")
    return f'<details class="{cls}"><summary>{label}</summary>{inner}</details>'


def render_node(el):
    tag = local(el)
    if tag in ("lb",):
        return "<br/>"
    if tag in ("pb", "fw", "teiHeader"):
        return ""
    inner = render_children(el)

    if tag == "p":
        pid = el.get(XML_ID)
        idattr = f' id="{esc_attr(pid)}"' if pid else ""
        return f"<p{idattr}>{inner}</p>"
    if tag == "head":
        return f'<h3 class="tei-head">{inner}</h3>'
    if tag == "persName":
        return person_span(el, inner)
    if tag == "placeName":
        return f'<span class="ann ann-place">{inner}</span>'
    if tag == "orgName":
        return f'<span class="ann ann-org">{inner}</span>'
    if tag == "term":
        return f'<em class="tei-term">{inner}</em>'
    if tag == "bibl":
        return f'<span class="tei-bibl">{inner}</span>'
    if tag == "title":
        return f'<em class="tei-title">{inner}</em>'
    if tag == "foreign":
        return f'<em class="tei-foreign">{inner}</em>'
    if tag == "hi":
        rend = (el.get("rend") or "").lower()
        if "bold" in rend or "strong" in rend:
            return f"<strong>{inner}</strong>"
        return f"<em>{inner}</em>"
    if tag in ("quote", "cit"):
        return f"<blockquote>{inner}</blockquote>"
    if tag in ("q", "said"):
        return f"<q>{inner}</q>"
    if tag == "byline":
        return f'<p class="tei-byline">{inner}</p>'
    if tag == "lg":
        return f'<div class="tei-lg">{inner}</div>'
    if tag == "l":
        return f'<span class="tei-l">{inner}</span><br/>'
    if tag == "list":
        return f'<ul class="tei-list">{inner}</ul>'
    if tag == "item":
        return f"<li>{inner}</li>"
    if tag == "note":
        return render_note(el, inner)
    if tag == "ref":
        target = el.get("target") or ""
        return f'<a href="{esc_attr(target)}">{inner}</a>'
    if tag == "div":
        dtype = el.get("type") or ""
        xmlid = el.get(XML_ID)
        classes = "tei-div" + (f" tei-{dtype}" if dtype else "")
        idattr = f' id="{esc_attr(xmlid)}"' if xmlid else ""
        return f'<div class="{classes}"{idattr}>{inner}</div>'
    # Unknown / transparent wrappers: emit children only.
    return inner


TYPE_LABELS = {
    "group": "Miscelánea",
    "editorial": "Editorial",
    "text": "Texto",
    "essay": "Ensayo",
    "poem": "Poesía",
    "letter": "Correspondencia",
    "review": "Reseñas",
}


def article_title(div):
    for child in div:
        if local(child) == "head":
            return collapse_ws("".join(child.itertext()))
    dtype = div.get("type") or ""
    return TYPE_LABELS.get(dtype, "Sección")


def render_article_body(div):
    parts = []
    if div.text:
        parts.append(esc(div.text))
    skipped_title = False
    for child in div:
        if not skipped_title and local(child) == "head":
            skipped_title = True
            if child.tail:
                parts.append(esc(child.tail))
            continue
        parts.append(render_node(child))
        if child.tail:
            parts.append(esc(child.tail))
    return "".join(parts)


def yaml_quote(text):
    return "'" + (text or "").replace("'", "''") + "'"


# --- Main --------------------------------------------------------------------
def main():
    load_persons()
    print(f"Loaded {len(PERSONS)} persons from listPerson.xml")

    OUT_DIR.mkdir(exist_ok=True)
    # Remove previously generated pages so the build stays in sync.
    for old in OUT_DIR.glob("*.html"):
        old.unlink()

    toc = []  # list of (issue_label, year, [(title, permalink), ...])
    order = 0

    for key, filename, label, year in ISSUES:
        path = TEI_DIR / filename
        if not path.exists():
            print(f"  WARNING: {filename} not found, skipping")
            continue
        root = ET.parse(str(path)).getroot()
        body = root.find(".//tei:body", NS)
        if body is None:
            print(f"  WARNING: no <body> in {filename}")
            continue

        articles = [c for c in body if local(c) == "div"]
        entries = []
        for i, div in enumerate(articles, start=1):
            order += 1
            title = article_title(div)
            slug = f"{key}-{i:02d}"
            permalink = f"/ed/{slug}/"
            body_html = render_article_body(div)

            page = (
                "---\n"
                "layout: textoporpagina\n"
                f"title: {yaml_quote(title)}\n"
                f"permalink: {permalink}\n"
                f"issue: {yaml_quote(label)}\n"
                f"issue_num: {yaml_quote(label)}\n"
                f"year: {year}\n"
                f"order: {order}\n"
                "type: texto\n"
                "---\n"
                "{% raw %}\n"
                f'<article class="tei-text">\n{body_html}\n</article>\n'
                "{% endraw %}\n"
            )
            (OUT_DIR / f"{slug}.html").write_text(page, encoding="utf-8")
            entries.append((title, permalink))

        toc.append((label, year, entries))
        print(f"  {filename}: {len(entries)} articles")

    write_indice(toc)
    total = sum(len(e) for _, _, e in toc)
    print(f"Done: {total} reading pages across {len(toc)} issues.")


def write_indice(toc):
    lines = [
        "---",
        "layout: page",
        "title: Edición digital",
        "permalink: /indice/",
        "type: texto",
        "---",
        "",
        '<div class="prose" markdown="0">',
        '<div class="alert alert-warning" role="alert">',
        '  <strong>Anotaciones.</strong> Para anotar esta edición, use el botón '
        '<strong>&laquo;Anotar&raquo;</strong> de la barra de navegación: seleccione el '
        "texto de su interés para resaltarlo y asociarle notas.",
        "</div>",
        "",
        "<h2>Edición digital</h2>",
        "<p>Edición crítica digital de los seis números de <i>Revista SITIO</i> "
        "(Buenos Aires, 1981&ndash;1987), codificada en TEI-XML. Las figuras citadas "
        "aparecen resaltadas: pase el cursor sobre ellas para ver sus datos.</p>",
    ]
    for label, year, entries in toc:
        lines.append(f'<h3 class="indice-issue">Número {label} ({year})</h3>')
        lines.append('<ol class="indice-list">')
        for title, permalink in entries:
            href = "{{ site.baseurl }}" + permalink
            lines.append(f'  <li><a href="{href}">{esc(title)}</a></li>')
        lines.append("</ol>")
    lines.append("</div>")
    INDICE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote índice: {INDICE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
