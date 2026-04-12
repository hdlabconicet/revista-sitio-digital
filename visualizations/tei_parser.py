"""Shared TEI-XML parsing utilities for SITIO visualization scripts.

Consolidates functions duplicated across network_analysis.py (lines 34-114),
prosopography_analysis.py (lines 128-246), and integrated_analysis.py (lines 108-203).
"""

import lxml.etree as ET
import re
from collections import defaultdict
from pathlib import Path

from .config import (
    NS, TEI_DIR, COUNTRY_MAPPINGS, REGION_MAPPINGS,
    HISTORICAL_PERIODS, SKIP_DIV_TYPES, INCLUDE_WITHOUT_BYLINE,
)


def get_root(filename):
    """Load XML file with XInclude resolution. Resolves filenames against TEI_DIR."""
    filepath = TEI_DIR / filename if not Path(filename).is_absolute() else Path(filename)
    parser = ET.XMLParser(resolve_entities=True)
    tree = ET.parse(str(filepath), parser)
    tree.xinclude()
    return tree.getroot()


def clean_id(ref_string):
    """Extract clean ID from TEI reference (strip '#' prefix)."""
    if not ref_string:
        return None
    return ref_string.replace('#', '').strip()


def extract_year(date_str):
    """Extract year from ISO date string, handling BCE dates like -0384."""
    if not date_str:
        return None
    try:
        date_str = str(date_str)
        if date_str.startswith('-'):
            return int(date_str[:5])
        return int(date_str[:4])
    except (ValueError, IndexError):
        return None


def normalize_country(place_text):
    """Normalize country/birthplace text to standard country name."""
    if not place_text:
        return None
    place_lower = str(place_text).lower().strip()

    for key, value in COUNTRY_MAPPINGS.items():
        if key in place_lower:
            return value

    if 'actual' in place_lower or 'current' in place_lower:
        match = re.search(r'\((?:actual|current)\s+(\w+)\)', place_lower)
        if match:
            extracted = match.group(1).lower()
            for key, value in COUNTRY_MAPPINGS.items():
                if key in extracted:
                    return value

    return str(place_text).split('(')[0].strip()


def get_region(country):
    """Map country to geographic region."""
    if not country:
        return "Other/Unknown"
    return REGION_MAPPINGS.get(country, "Other/Unknown")


def get_historical_period(year):
    """Map birth year to historical period."""
    if year is None:
        return "Unknown"
    for start, end, period_name in HISTORICAL_PERIODS:
        if start <= year < end:
            return period_name
    if year >= 2000:
        return "21st Century"
    return "Unknown"


def load_person_data(filename=None):
    """Parse listPerson.xml into a dict mapping xml:id -> person metadata.

    Returns dict[str, dict] with keys: name, birth_year, death_year,
    birth_place_raw, country, region, period, wikidata, lifespan.
    """
    from .config import LIST_PERSON
    if filename is None:
        filename = LIST_PERSON

    root = get_root(filename)
    persons = {}

    for person in root.xpath('//tei:person', namespaces=NS):
        pid = person.get('{http://www.w3.org/XML/1998/namespace}id')
        if not pid:
            continue

        surname = person.xpath('.//tei:surname/text()', namespaces=NS)
        forename = person.xpath('.//tei:forename/text()', namespaces=NS)

        if surname and forename:
            full_name = f"{str(forename[0])} {str(surname[0])}"
        elif surname:
            full_name = str(surname[0])
        else:
            full_name = "".join(
                str(t) for t in person.xpath('.//tei:persName//text()', namespaces=NS)
            ).strip()

        birth_place_raw = person.xpath('.//tei:birth/tei:placeName/text()', namespaces=NS)
        birth_date = person.xpath('.//tei:birth/tei:date/@when', namespaces=NS)
        birth_year = extract_year(birth_date[0]) if birth_date else None
        birth_place = str(birth_place_raw[0]) if birth_place_raw else None
        country = normalize_country(birth_place)
        region = get_region(country)
        period = get_historical_period(birth_year)

        death_date = person.xpath('.//tei:death/tei:date/@when', namespaces=NS)
        death_year = extract_year(death_date[0]) if death_date else None

        wikidata = person.xpath('.//tei:idno[@subtype="wikidata"]/text()', namespaces=NS)

        persons[pid] = {
            'name': full_name,
            'birth_year': birth_year,
            'death_year': death_year,
            'birth_place_raw': birth_place,
            'country': country,
            'region': region,
            'period': period,
            'wikidata': str(wikidata[0]) if wikidata else None,
            'lifespan': (death_year - birth_year) if birth_year and death_year else None,
        }

    return persons


def load_bibl_data(filename=None):
    """Parse listBibl.xml into a dict mapping xml:id -> bibliography metadata.

    Returns dict[str, dict] with keys: title, author_ref, author_name,
    date, date_year, level, lang, wikidata.
    """
    from .config import LIST_BIBL
    if filename is None:
        filename = LIST_BIBL

    root = get_root(filename)
    bibls = {}

    for bibl in root.xpath('//tei:bibl', namespaces=NS):
        bid = bibl.get('{http://www.w3.org/XML/1998/namespace}id')
        if not bid:
            continue

        author_el = bibl.xpath('./tei:author', namespaces=NS)
        author_ref = None
        author_name = None
        if author_el:
            author_ref = clean_id(author_el[0].get('ref'))
            author_name = author_el[0].text

        title_el = bibl.xpath('./tei:title', namespaces=NS)
        title = title_el[0].text if title_el else None
        level = title_el[0].get('level') if title_el else None
        lang = title_el[0].get('{http://www.w3.org/XML/1998/namespace}lang') if title_el else None

        date_el = bibl.xpath('./tei:date', namespaces=NS)
        date_str = None
        date_year = None
        if date_el:
            date_str = date_el[0].get('when') or date_el[0].get('from')
            date_year = extract_year(date_str)

        wikidata = bibl.xpath('./tei:idno[@subtype="wikidata"]/text()', namespaces=NS)

        bibls[bid] = {
            'title': title,
            'author_ref': author_ref,
            'author_name': author_name,
            'date': date_str,
            'date_year': date_year,
            'level': level,
            'lang': lang,
            'wikidata': str(wikidata[0]) if wikidata else None,
        }

    return bibls


def _get_relevant_divs(root):
    """Get content divs using broadened filtering strategy.

    Includes divs with @type that either:
    - Have a <byline> child element, OR
    - Have @type in INCLUDE_WITHOUT_BYLINE

    Skips: divs with @type in SKIP_DIV_TYPES.
    For nested divs (child of another typed div), skip only if the child
    has NO byline and is NOT in INCLUDE_WITHOUT_BYLINE — this avoids
    counting numbered subdivisions (<div n="I">) while preserving authored
    essays inside wrapper divs like <div type="ensayos">.
    """
    relevant = []
    all_typed_divs = root.xpath('//tei:div[@type]', namespaces=NS)

    for div in all_typed_divs:
        div_type = div.get('type', '')

        if div_type in SKIP_DIV_TYPES:
            continue

        has_byline = len(div.xpath('./tei:byline', namespaces=NS)) > 0

        # For nested divs: only skip if this looks like a numbered subdivision
        # (no byline, not a known content type). Authored children of wrapper
        # divs like "ensayos" or "lecturas" should pass through.
        parent_div = div.getparent()
        if parent_div is not None and parent_div.tag == f'{{{NS["tei"]}}}div':
            parent_type = parent_div.get('type')
            if parent_type and parent_type not in SKIP_DIV_TYPES:
                if parent_type != 'editorial':
                    # This is a child of a content wrapper div.
                    # Only include if it has its own byline or is a known content type.
                    if not has_byline and div_type not in INCLUDE_WITHOUT_BYLINE:
                        continue

        if has_byline or div_type in INCLUDE_WITHOUT_BYLINE:
            relevant.append(div)

    return relevant


def extract_citations(root, issue_id):
    """Extract all entity references from an issue file.

    Returns a dict with:
    - person_refs: list of {source_author, target_person, div_id, div_type, issue_id}
    - title_refs: list of {source_author, target_bibl, div_id, issue_id}
    - divs: list of {id, type, subtype, authors, issue_id}
    - cited_person_ids: set of all cited person IDs
    - cited_bibl_ids: set of all cited bibliography IDs
    - author_ids: set of all SITIO contributor IDs
    """
    divs_data = []
    person_refs = []
    title_refs = []
    cited_person_ids = set()
    cited_bibl_ids = set()
    author_ids = set()

    relevant_divs = _get_relevant_divs(root)

    for div in relevant_divs:
        div_id = div.get('{http://www.w3.org/XML/1998/namespace}id', 'unknown')
        div_type = div.get('type', '')
        div_subtype = div.get('subtype', '')

        author_ref_list = div.xpath('./tei:byline/tei:persName/@ref', namespaces=NS)
        if not author_ref_list:
            author_ref_list = div.xpath('./tei:byline/tei:docAuthor/@ref', namespaces=NS)

        sources = [clean_id(ref) for ref in author_ref_list if clean_id(ref)]
        author_ids.update(sources)

        divs_data.append({
            'id': div_id,
            'type': div_type,
            'subtype': div_subtype,
            'authors': sources,
            'issue_id': issue_id,
        })

        # Get cited persons — exclude refs inside <note> (editorial annotations)
        citation_nodes = div.xpath(
            './/*[not(ancestor::tei:note)]'
            '[self::tei:persName or self::tei:author or self::tei:name]/@ref',
            namespaces=NS
        )
        for ref in citation_nodes:
            tid = clean_id(ref)
            if tid and tid not in sources:
                cited_person_ids.add(tid)
                for source in sources:
                    person_refs.append({
                        'source_author': source,
                        'target_person': tid,
                        'div_id': div_id,
                        'div_type': div_type,
                        'issue_id': issue_id,
                    })

        # Get cited works — exclude refs inside <note>
        title_ref_nodes = div.xpath(
            './/tei:title[@ref][not(ancestor::tei:note)]/@ref', namespaces=NS
        )
        for ref in title_ref_nodes:
            bid = clean_id(ref)
            if bid:
                cited_bibl_ids.add(bid)
                for source in sources:
                    title_refs.append({
                        'source_author': source,
                        'target_bibl': bid,
                        'div_id': div_id,
                        'issue_id': issue_id,
                    })

    return {
        'issue_id': issue_id,
        'person_refs': person_refs,
        'title_refs': title_refs,
        'divs': divs_data,
        'cited_person_ids': cited_person_ids,
        'cited_bibl_ids': cited_bibl_ids,
        'author_ids': author_ids,
    }


def merge_citations(citation_list):
    """Merge citation data from multiple issues into a single corpus-level dataset."""
    merged = {
        'issue_id': 'full_corpus',
        'person_refs': [],
        'title_refs': [],
        'divs': [],
        'cited_person_ids': set(),
        'cited_bibl_ids': set(),
        'author_ids': set(),
    }

    for data in citation_list:
        merged['person_refs'].extend(data['person_refs'])
        merged['title_refs'].extend(data['title_refs'])
        merged['divs'].extend(data['divs'])
        merged['cited_person_ids'].update(data['cited_person_ids'])
        merged['cited_bibl_ids'].update(data['cited_bibl_ids'])
        merged['author_ids'].update(data['author_ids'])

    return merged
