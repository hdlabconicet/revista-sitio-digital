"""Shared configuration for SITIO visualization scripts."""

from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent  # repo root
VIZ_DIR = Path(__file__).parent              # visualizations/
OUTPUT_DIR = VIZ_DIR / "outputs"
TEI_DIR = PROJECT_ROOT / "TEI"               # Source XML files location

# --- Issue files ---
ISSUE_FILES = {
    "issue_1": "issue_1.xml",
    "issue_2": "issue_2.xml",
    "issue_3": "issue_3.xml",
    "issue_4-5": "issue_4-5.xml",
    "issue_6": "issue_6.xml",
}

ISSUE_YEARS = {
    "issue_1": 1981,
    "issue_2": 1982,
    "issue_3": 1983,
    "issue_4-5": 1985,
    "issue_6": 1987,
}

# --- Reference list files ---
LIST_PERSON = "listPerson.xml"
LIST_BIBL = "listBibl.xml"
LIST_PLACES = "listPlaces2.xml"
LIST_ORGS = "listEd2.xml"

# --- TEI namespace ---
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

# --- Div filtering ---
SKIP_DIV_TYPES = {"bibliography", "appendix", "dedication", "introduction", "group"}

INCLUDE_WITHOUT_BYLINE = {
    "prose", "poem", "letter", "traduccion",
    "fragmentodenovela", "debate", "escenas",
}

# --- Historical periods ---
HISTORICAL_PERIODS = [
    (-800, -500, "Antiquity (Archaic)"),
    (-500, -300, "Classical Antiquity"),
    (-300, 500, "Hellenistic/Roman"),
    (500, 1400, "Medieval"),
    (1400, 1600, "Renaissance"),
    (1600, 1789, "Early Modern"),
    (1789, 1848, "Revolutionary Era"),
    (1848, 1914, "Long 19th Century"),
    (1914, 1945, "World Wars Era"),
    (1945, 2000, "Contemporary"),
]

# --- Country normalization ---
COUNTRY_MAPPINGS = {
    'argentina': 'Argentina',
    'france': 'France', 'francia': 'France',
    'germany': 'Germany', 'alemania': 'Germany', 'prusia': 'Germany',
    'austria': 'Austria',
    'england': 'United Kingdom', 'inglaterra': 'United Kingdom', 'reino unido': 'United Kingdom',
    'ireland': 'Ireland', 'irlanda': 'Ireland',
    'italy': 'Italy', 'italia': 'Italy',
    'spain': 'Spain', 'espania': 'Spain', 'españa': 'Spain',
    'usa': 'United States', 'estados unidos': 'United States',
    'russia': 'Russia', 'rusia': 'Russia',
    'poland': 'Poland', 'polonia': 'Poland',
    'greece': 'Greece', 'grecia': 'Greece',
    'switzerland': 'Switzerland', 'suiza': 'Switzerland',
    'czech': 'Czech Republic', 'praga': 'Czech Republic',
    'cuba': 'Cuba',
    'mexico': 'Mexico', 'méxico': 'Mexico',
    'uruguay': 'Uruguay',
    'chile': 'Chile',
    'brasil': 'Brazil', 'brazil': 'Brazil',
    'venezuela': 'Venezuela',
    'peru': 'Peru', 'perú': 'Peru',
    'colombia': 'Colombia',
    'japan': 'Japan', 'japón': 'Japan',
    'china': 'China',
    'israel': 'Israel',
    'netherlands': 'Netherlands', 'países bajos': 'Netherlands',
    'belgium': 'Belgium', 'bélgica': 'Belgium',
    'portugal': 'Portugal',
    'hungary': 'Hungary', 'hungría': 'Hungary',
    'romania': 'Romania', 'rumanía': 'Romania',
    'denmark': 'Denmark', 'dinamarca': 'Denmark',
    'sweden': 'Sweden', 'suecia': 'Sweden',
    'norway': 'Norway', 'noruega': 'Norway',
}

# --- Region mappings ---
REGION_MAPPINGS = {
    'Argentina': 'Latin America',
    'Mexico': 'Latin America',
    'Cuba': 'Latin America',
    'Uruguay': 'Latin America',
    'Chile': 'Latin America',
    'Brazil': 'Latin America',
    'Venezuela': 'Latin America',
    'Peru': 'Latin America',
    'Colombia': 'Latin America',
    'France': 'Western Europe',
    'Germany': 'Western Europe',
    'United Kingdom': 'Western Europe',
    'Italy': 'Western Europe',
    'Spain': 'Western Europe',
    'Austria': 'Western Europe',
    'Switzerland': 'Western Europe',
    'Netherlands': 'Western Europe',
    'Belgium': 'Western Europe',
    'Ireland': 'Western Europe',
    'Portugal': 'Western Europe',
    'Greece': 'Southern Europe / Classical',
    'United States': 'North America',
    'Russia': 'Eastern Europe',
    'Poland': 'Eastern Europe',
    'Czech Republic': 'Eastern Europe',
    'Hungary': 'Eastern Europe',
    'Romania': 'Eastern Europe',
    'Israel': 'Middle East',
    'Japan': 'Asia',
    'China': 'Asia',
    'Denmark': 'Scandinavia',
    'Sweden': 'Scandinavia',
    'Norway': 'Scandinavia',
}

# --- Color palettes ---
REGION_COLORS = {
    'Western Europe': '#3498db',
    'Latin America': '#2ecc71',
    'North America': '#e74c3c',
    'Eastern Europe': '#9b59b6',
    'Southern Europe / Classical': '#f39c12',
    'Scandinavia': '#00bcd4',
    'Asia': '#ff9800',
    'Middle East': '#795548',
    'Other/Unknown': '#95a5a6',
}

PERIOD_COLORS = {
    'Antiquity (Archaic)': '#1a1a2e',
    'Classical Antiquity': '#16213e',
    'Hellenistic/Roman': '#0f3460',
    'Medieval': '#533483',
    'Renaissance': '#e94560',
    'Early Modern': '#f39c12',
    'Revolutionary Era': '#e74c3c',
    'Long 19th Century': '#3498db',
    'World Wars Era': '#2ecc71',
    'Contemporary': '#1abc9c',
    'Unknown': '#95a5a6',
}

COMMUNITY_COLORS = [
    '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
    '#1abc9c', '#e91e63', '#00bcd4', '#ff9800', '#795548',
    '#607d8b', '#8bc34a', '#ffc107', '#03a9f4', '#673ab7',
]

# --- Matplotlib style ---
MPL_STYLE = 'seaborn-v0_8-darkgrid'
MPL_DPI = 150
