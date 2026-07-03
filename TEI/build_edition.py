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
import json
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
IDX_DIR = REPO / "_indices"
INDICE = REPO / "_pages" / "02-edicion-digital.html"

ISSUES = [
    {"key": "issue_1", "file": "issue_1.xml", "label": "1", "year": 1981,
     "slug": "numero-1", "cover": "Sitio-1_tapa.jpg",
     "ahira": "https://ahira.com.ar/ejemplares/sitio-no-1/"},
    {"key": "issue_2", "file": "issue_2.xml", "label": "2", "year": 1982,
     "slug": "numero-2", "cover": "Sitio-2_tapa-n.jpg",
     "ahira": "https://ahira.com.ar/ejemplares/sitio-no-2/"},
    {"key": "issue_3", "file": "issue_3.xml", "label": "3", "year": 1983,
     "slug": "numero-3", "cover": "Sitio-3_tapa-n.jpg",
     "ahira": "https://ahira.com.ar/ejemplares/sitio-no-3/"},
    {"key": "issue_4-5", "file": "issue_4-5.xml", "label": "4-5", "year": 1985,
     "slug": "numero-4-5", "cover": "Sitio-4-5_tapa.jpg",
     "ahira": "https://ahira.com.ar/ejemplares/sitio-no-4-5/"},
    {"key": "issue_6", "file": "issue_6.xml", "label": "6", "year": 1987,
     "slug": "numero-6", "cover": "Sitio-6_tapa-n.jpg",
     "ahira": "https://ahira.com.ar/ejemplares/sitio-no-6/"},
]

# Notes excluded from the reading edition. Types listed here are dropped
# wholesale; individual notes can be excluded via their xml:id or @target
# (without the leading '#') — note that most untyped (original) footnotes
# carry neither, so per-note curation of those requires adding ids to the TEI.
EXCLUDED_NOTE_TYPES = {"interpretation"}
EXCLUDED_NOTE_IDS = set()

PERSONS = {}  # populated by load_persons()

GRAPH_JSON = REPO / "sigma-viz" / "data" / "sigma_graph.json"
GRAPH_NODE_KEYS = set()  # populated by load_graph_keys(); keys == listPerson xml:ids


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


def load_graph_keys():
    if GRAPH_JSON.exists():
        data = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
        GRAPH_NODE_KEYS.update(n["key"] for n in data.get("nodes", []))
    return GRAPH_NODE_KEYS


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
    if not (info and info.get("name")):
        return f'<span class="ann ann-person">{inner}</span>'
    tip = info["name"]
    span = life_span(info.get("birth"), info.get("death"))
    if span:
        tip = f"{tip} ({span})"
    if pid in GRAPH_NODE_KEYS:
        # Reading pages live at {baseurl}/ed/<slug>/, so ../../ resolves to the
        # site root regardless of baseurl (the body is inside {% raw %}).
        return (
            f'<a class="ann ann-person ann-linked" '
            f'href="../../sigma-viz/?node={esc_attr(pid)}" '
            f'target="_blank" rel="noopener" '
            f'data-balloon="{esc_attr(tip + " · Ver en la red de citas")}" '
            f'data-balloon-pos="up">{inner}</a>'
        )
    return (
        f'<span class="ann ann-person" data-balloon="{esc_attr(tip)}" '
        f'data-balloon-pos="up">{inner}</span>'
    )


def note_excluded(el):
    if (el.get("type") or "") in EXCLUDED_NOTE_TYPES:
        return True
    ident = el.get(XML_ID) or (el.get("target") or "").lstrip("#")
    return bool(ident) and ident in EXCLUDED_NOTE_IDS


# Notes render as superscript calls in the text; their content is gathered
# here (reset per article) and emitted as a "Notas" section at the end.
ARTICLE_NOTES = []

FN_LABELS = {
    "translator": "N. del T.",
    "editorial": "N. del E.",
    "historical_context": "N. del E.",
}


def register_footnote(el, backref=True):
    num = len(ARTICLE_NOTES) + 1
    content = render_flow(el)
    label = FN_LABELS.get(el.get("type") or "")
    if label:
        tag = f'<span class="fn-label">[{label}]</span> '
        if content.startswith("<p"):
            gt = content.index(">") + 1
            content = content[:gt] + tag + content[gt:]
        else:
            content = tag + content
    ARTICLE_NOTES.append({"num": num, "content": content, "backref": backref})
    if backref:
        return (
            f'<sup class="fn-ref" id="fnref-{num}">'
            f'<a href="#fn-{num}">{num}</a></sup>'
        )
    return ""


def render_note(el):
    # Editorial summaries are abstracts: they stay in place as a collapsible
    # box. Every other note becomes a numbered footnote; notes hanging
    # directly from a <div> have no inline anchor, so they are listed without
    # a marker or back-link.
    if (el.get("type") or "") == "summary":
        return (
            '<details class="ed-note ed-summary"><summary>Resumen editorial'
            f"</summary>{render_flow(el)}</details>"
        )
    parent = el.getparent()
    if parent is not None and local(parent) in ("div", "body"):
        register_footnote(el, backref=False)
        return ""
    return register_footnote(el, backref=True)


def render_notes_section():
    if not ARTICLE_NOTES:
        return ""
    items = []
    for note in ARTICLE_NOTES:
        content = note["content"]
        if note["backref"]:
            back = (
                f' <a class="fn-back" href="#fnref-{note["num"]}" '
                'aria-label="Volver al texto">&#8617;</a>'
            )
            if content.endswith("</p>"):
                content = content[:-4] + back + "</p>"
            else:
                content += back
        items.append(f'<li id="fn-{note["num"]}">{content}</li>')
    return (
        '<section class="fn-notes"><h3 class="tei-head">Notas</h3>'
        f'<ol class="fn-list">{"".join(items)}</ol></section>'
    )


def render_cit(el):
    # A <cit> pairs a quotation with its source: one <figure> holding the
    # <blockquote> and a <figcaption> for the <bibl>, in document order
    # (a handful of cits are bibl-first intro phrases).
    parts = []
    for child in el:
        t = local(child)
        if t == "bibl":
            parts.append(
                f'<figcaption class="tei-cit-source">{render_children(child)}</figcaption>'
            )
        elif t in ("quote", "q"):
            parts.append(f"<blockquote>{render_children(child)}</blockquote>")
        else:
            parts.append(render_node(child))
    return f'<figure class="tei-cit">{"".join(parts)}</figure>'


# Elements that render as blocks and therefore cannot live inside a <p>.
# (Non-summary notes render as inline footnote calls, so they flow normally.)
BLOCK_IN_P = {"cit", "quote", "lg", "list"}
# Sentence punctuation left dangling after a displayed quote or note.
TAIL_PUNCT = re.compile(r"^[.,;:!?…)\]»”]+")


def is_block_note(child):
    return local(child) == "note" and (child.get("type") or "") == "summary"


def absorb_punct(block_html, punct):
    # Tuck trailing sentence punctuation inside the quote block (after the
    # quotation or its source caption) instead of orphaning it at the start
    # of the next paragraph.
    p = esc(punct)
    idx = max(block_html.rfind("</figcaption>"), block_html.rfind("</blockquote>"))
    if idx == -1:
        return block_html + p
    return block_html[:idx] + p + block_html[idx:]


def render_flow(el, pid=None):
    # Block quotes sit mid-sentence in the TEI, but block elements inside <p>
    # are invalid HTML (browsers close the paragraph early and the rest
    # becomes stray text). Split the flow around them, wrap inline runs in
    # real <p>, and re-attach dangling punctuation to the quote block.
    # Used for paragraphs and for footnote/summary contents alike.
    parts = []
    buf = [esc(el.text)] if el.text else []
    state = {"first_done": False}

    def flush():
        text = "".join(buf)
        del buf[:]
        if not text.strip():
            return
        attrs = ""
        if not state["first_done"] and pid:
            attrs += f' id="{esc_attr(pid)}"'
        if state["first_done"]:
            attrs += ' class="tei-p-cont"'
        state["first_done"] = True
        parts.append(f"<p{attrs}>{text}</p>")

    for child in el:
        tag = local(child)
        if tag == "note" and note_excluded(child):
            if child.tail:
                buf.append(esc(child.tail))
            continue
        if tag in BLOCK_IN_P or is_block_note(child):
            block_html = render_node(child)
            tail = child.tail or ""
            punct = ""
            stripped = tail.lstrip()
            m = TAIL_PUNCT.match(stripped)
            if m:
                punct = m.group(0)
                tail = stripped[len(punct):]
            if punct and tag == "note":
                # The summary box displaces its content: the mark belongs to
                # the surrounding sentence (or to a preceding quote block).
                if "".join(buf).strip():
                    buf.append(esc(punct))
                elif parts and max(
                    parts[-1].rfind("</figcaption>"), parts[-1].rfind("</blockquote>")
                ) != -1:
                    parts[-1] = absorb_punct(parts[-1], punct)
                else:
                    buf.append(esc(punct))
                punct = ""
            flush()
            if punct:
                block_html = absorb_punct(block_html, punct)
            parts.append(block_html)
            if tail:
                buf.append(esc(tail))
        else:
            buf.append(render_node(child))
            if child.tail:
                buf.append(esc(child.tail))
    flush()
    return "".join(parts)


def render_node(el):
    tag = local(el)
    if tag in ("lb",):
        return "<br/>"
    if tag in ("pb", "fw", "teiHeader"):
        return ""
    if tag == "note":
        return "" if note_excluded(el) else render_note(el)
    if tag == "head":
        # Footnote calls are phrasing content, so they can stay in the <h3>.
        return f'<h3 class="tei-head">{render_children(el)}</h3>'
    if tag == "cit":
        return render_cit(el)
    if tag == "p":
        return render_flow(el, el.get(XML_ID))
    inner = render_children(el)

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
    if tag == "quote":
        return f'<blockquote class="tei-quote">{inner}</blockquote>'
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


TITLE_EXCLUDE = {"note", "bibl"}


def head_title_text(el):
    # Like itertext(), but skips note/bibl subtrees (their text is not part of
    # the title) while keeping every element's tail.
    parts = [el.text or ""]
    for child in el:
        if local(child) not in TITLE_EXCLUDE:
            parts.append(head_title_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def article_title(div):
    for child in div:
        if local(child) == "head":
            title = collapse_ws(head_title_text(child))
            title = re.sub(r"\s+([.,;:!?])", r"\1", title)
            title = re.sub(r"(?<!\.)\.$", "", title)
            return title
    dtype = div.get("type") or ""
    return TYPE_LABELS.get(dtype, "Sección")


def article_authors(div):
    # Firmas del artículo: bylines (y docAuthor) en cualquier nivel; los divs
    # de tipo grupo (misceláneas, reseñas) reúnen las firmas de sus piezas.
    names = []
    for el in div.iter():
        if local(el) in ("byline", "docAuthor"):
            text = collapse_ws("".join(el.itertext()))
            text = re.sub(r"^por\s+", "", text, flags=re.I).strip(" .,;:")
            if text and text not in names:
                names.append(text)
    if not names:
        return ""
    if len(names) > 3:
        return ", ".join(names[:3]) + " y otros"
    if len(names) > 1:
        return ", ".join(names[:-1]) + " y " + names[-1]
    return names[0]


def render_article_body(div):
    parts = []
    if div.text:
        parts.append(esc(div.text))
    skipped_title = False
    for child in div:
        if not skipped_title and local(child) == "head":
            skipped_title = True
            # The title <head> is dropped (the page layout prints the title),
            # but any footnote attached to it must survive in the notes
            # section (there is no title text to anchor a marker to).
            for sub in child:
                if local(sub) == "note" and not note_excluded(sub):
                    register_footnote(sub, backref=False)
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
    load_graph_keys()
    print(f"Loaded {len(GRAPH_NODE_KEYS)} node keys from sigma_graph.json")

    OUT_DIR.mkdir(exist_ok=True)
    IDX_DIR.mkdir(exist_ok=True)
    # Remove previously generated pages so the build stays in sync.
    for old in OUT_DIR.glob("*.html"):
        old.unlink()
    for old in IDX_DIR.glob("*.html"):
        old.unlink()

    total = 0
    order = 0

    for issue in ISSUES:
        path = TEI_DIR / issue["file"]
        if not path.exists():
            print(f"  WARNING: {issue['file']} not found, skipping")
            continue
        root = ET.parse(str(path)).getroot()
        body = root.find(".//tei:body", NS)
        if body is None:
            print(f"  WARNING: no <body> in {issue['file']}")
            continue

        articles = [c for c in body if local(c) == "div"]
        entries = []
        for i, div in enumerate(articles, start=1):
            order += 1
            title = article_title(div)
            authors = article_authors(div)
            slug = f"{issue['key']}-{i:02d}"
            permalink = f"/ed/{slug}/"
            del ARTICLE_NOTES[:]
            body_html = render_article_body(div) + render_notes_section()

            page = (
                "---\n"
                "layout: textoporpagina\n"
                f"title: {yaml_quote(title)}\n"
                f"author: {yaml_quote(authors)}\n"
                f"permalink: {permalink}\n"
                f"issue: {yaml_quote(issue['label'])}\n"
                f"issue_num: {yaml_quote(issue['label'])}\n"
                f"issue_slug: {yaml_quote(issue['slug'])}\n"
                f"year: {issue['year']}\n"
                f"order: {order}\n"
                "type: texto\n"
                "---\n"
                "{% raw %}\n"
                f'<article class="tei-text">\n{body_html}\n</article>\n'
                "{% endraw %}\n"
            )
            (OUT_DIR / f"{slug}.html").write_text(page, encoding="utf-8")
            entries.append((title, permalink, authors))

        write_issue_index(issue, entries)
        total += len(entries)
        print(f"  {issue['file']}: {len(entries)} articles")

    write_landing()
    print(f"Done: {total} reading pages across {len(ISSUES)} issues.")


def write_issue_index(issue, entries):
    lines = [
        "---",
        "layout: page",
        f"title: {yaml_quote('Número ' + issue['label'] + ' (' + str(issue['year']) + ')')}",
        f"permalink: /indice/{issue['slug']}/",
        "---",
        "",
        '<div class="prose" markdown="0">',
        '<p class="issue-meta">',
        f'  <a href="{{{{ site.baseurl }}}}/indice/">&larr; Todos los números</a>',
        '  &middot;',
        f'  <a href="{esc_attr(issue["ahira"])}" target="_blank" rel="noopener">'
        "Facsímil en AHIRA &nearr;</a>",
        "</p>",
        '<ol class="indice-list">',
    ]
    for title, permalink, authors in entries:
        href = "{{ site.baseurl }}" + permalink
        author_html = (
            f' <span class="indice-autor">&mdash; {esc(authors)}</span>' if authors else ""
        )
        lines.append(f'  <li><a href="{href}">{esc(title)}</a>{author_html}</li>')
    lines += ["</ol>", "</div>"]
    out = IDX_DIR / f"{issue['slug']}.html"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_landing():
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
        "<p>Edición crítica digital de los seis números de <i>Revista SITIO</i> "
        "(Buenos Aires, 1981&ndash;1987), codificada en TEI-XML.</p>",
        "",
        '<div class="tapa-grid">',
    ]
    for issue in ISSUES:
        cover = "{{ site.baseurl }}/assets/imagenes/" + issue["cover"]
        lines += [
            '  <div class="tapa-card">',
            f'    <a href="{{{{ site.baseurl }}}}/indice/{issue["slug"]}/">',
            f'      <img src="{cover}" alt="Tapa de SITIO n.º {issue["label"]} '
            f'({issue["year"]})" loading="lazy">',
            f'      <h3>Número {issue["label"]} <span class="tapa-year">'
            f'({issue["year"]})</span></h3>',
            "    </a>",
            "  </div>",
        ]
    lines += ["</div>", "</div>"]
    INDICE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote índice: {INDICE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
