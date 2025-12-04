"""
Script to parse TEI XML files from norn-uio/norn-poems and extract poem titles with authors.
Creates a JSON file with poem data for the dropdown menu.
"""

import json
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import poetree
import random


# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
REPO_OWNER = "norn-uio"
REPO_NAME = "norn-poems"
REPO_PATH = "TEI"  # Path to XML files in the repository

# PoeTree API configuration
POETREE_API_BASE = "https://versologie.cz/poetree/api"


def reconstruct_plain_text(poem_body: list) -> str:
    """From the poetree.Poem.get_body() list output, reconstruct the plain text poem."""
    text = ""
    for idx, line in enumerate(poem_body):
        line_stanza = line.get("id_stanza")
        if idx == 0:
            current_stanza = line_stanza
        if current_stanza == line_stanza:
            text += line.get("text") + "\n"
        else:
            text += "\n"
            current_stanza = line_stanza
            text += line.get("text")
    return text


def fetch_poetree_poems(max_poems: Optional[int] = None) -> Dict[str, Dict]:
    """
    Fetch NORN poems using the poetree Python library (preferred).

    Returns a list of poem dicts enriched with `text` (body) and metadata.
    """

    corpus = poetree.Corpus("no")
    poems = [poem for source in corpus.get_sources() for poem in source.get_poems()]
    if max_poems:
        poems = poems[:max_poems]

    poem_data = {}

    for poem in poems:
        author = poetree.Author(lang="no", id_=poem.id_author)
        book = poetree.Source(lang="no", id_=poem.id_source)

        # Create dropdown label
        dropdown_label = f"{poem.title} - {author.name}"  # type: ignore

        poem_data[dropdown_label] = {
            "poem_id": poem.id,
            "poetree_id": poem.id_,
            "title": poem.title,
            "author": author.name,  # type: ignore
            "author_born": str(author.born) if author.born else "?",  # type: ignore
            "author_died": str(author.died) if author.died else "?",  # type: ignore
            "book_title": book.title,  # type: ignore
            "year": str(book.year_published) if book.year_published else "?",  # type: ignore
            "book_url": f"https://urn.nb.no/URN:NBN:no-nb_digibok_{book.id}",  # type: ignore
            "text": reconstruct_plain_text(poem.get_body()),
            "source": "poetree",
        }

    return poem_data


def fetch_github_repo_contents(
    owner: str = REPO_OWNER,
    repo: str = REPO_NAME,
    path: str = REPO_PATH,
    max_files: Optional[int] = None,
) -> List[Dict]:
    """
    Fetch list of files from a GitHub repository using the GitHub API.

    Args:
        owner: Repository owner
        repo: Repository name
        path: Path within the repository
        max_files: Maximum number of files to return (None for all)

    Returns:
        List of file metadata dictionaries
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        files = response.json()

        # Filter for XML files only
        xml_files = [
            f
            for f in files
            if isinstance(f, dict) and f.get("name", "").endswith(".xml")
        ]

        if max_files:
            xml_files = xml_files[:max_files]

        return xml_files

    except requests.RequestException as e:
        print(f"Error fetching repository contents: {e}")
        return []


def fetch_xml_file_content(download_url: str) -> Optional[str]:
    """
    Fetch the raw content of an XML file from GitHub.

    Args:
        download_url: Direct download URL for the file

    Returns:
        XML content as string, or None if fetch fails
    """
    try:
        response = requests.get(download_url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching XML file: {e}")
        return None


def parse_tei_xml(xml_content: str, file_name: str) -> Optional[Dict]:
    """
    Parse TEI XML content to extract poem metadata.

    Args:
        xml_content: XML content as string
        file_name: Name of the XML file

    Returns:
        Dictionary with author, book_title, year, and poems list
    """
    try:
        root = ET.fromstring(xml_content)

        # Define TEI namespace
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}

        # Extract metadata from TEI header
        author = ""
        book_title = ""
        year = ""

        # Try to find author
        author_elem = root.find(".//tei:author", ns)
        if author_elem is not None and author_elem.text:
            author = author_elem.text.strip()

        # Try to find title
        title_elem = root.find(".//tei:title[@type='main']", ns)
        if title_elem is None:
            title_elem = root.find(".//tei:title", ns)
        if title_elem is not None and title_elem.text:
            book_title = title_elem.text.strip()

        # Try to find publication year from TEI header: teiHeader/fileDesc/sourceDesc/bibl/date
        date_elem = root.find(
            ".//tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:bibl/tei:date",
            ns,
        )

        year = (date_elem.text or "?").strip()  # type: ignore

        # Extract poem titles and texts from lg elements
        poems = []
        poems_texts = []
        poem_ids = []
        book_url = ""

        # Try to find book URL from TEI header: teiHeader/fileDesc/sourceDesc/bibl/ref/@target
        ref_elem = root.find(
            ".//tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:bibl/tei:ref",
            ns,
        )
        if ref_elem is not None:
            book_url = (ref_elem.get("target") or ref_elem.text or "").strip()
        elif ref_elem is None:
            bibl_elem = root.find(
                ".//tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:bibl",
                ns,
            )
            if bibl_elem is not None:
                book_url = (
                    f"https://www.nb.no/items/URN:NBN:{bibl_elem.get('xml:id')}"
                    if bibl_elem is not None
                    else ""
                )
        else:
            book_url = ""

        def extract_lg_text(lg_elem):
            # If this lg contains stanza children, build text per stanza and join with two newlines
            stanza_children = lg_elem.findall("tei:lg[@type='stanza']", ns)
            if stanza_children:
                stanza_texts = []
                for stanza in stanza_children:
                    stanza_lines = []
                    for l in stanza.findall("tei:l", ns):
                        if l.text:
                            stanza_lines.append(l.text.strip())
                        if l.tail and l.tail.strip():
                            stanza_lines.append(l.tail.strip())
                    if not stanza_lines:
                        # Fallback stanza text using lb-based splitting
                        parts = []
                        for node in stanza.iter():
                            tag = node.tag if isinstance(node.tag, str) else ""
                            if tag.endswith("lb"):
                                parts.append("\n")
                            if node.text:
                                parts.append(node.text)
                            if node.tail:
                                parts.append(node.tail)
                        text = "".join(parts)
                        text = "\n".join([ln.strip() for ln in text.splitlines()])
                        stanza_texts.append(text.strip())
                    else:
                        stanza_texts.append("\n".join(stanza_lines).strip())
                return "\n\n".join([s for s in stanza_texts if s])

            # Otherwise, collect line elements directly under lg
            lines = []
            for l in lg_elem.findall("tei:l", ns):
                if l.text:
                    lines.append(l.text.strip())
                if l.tail and l.tail.strip():
                    lines.append(l.tail.strip())
            if not lines:
                # Fallback: join all text under lg with newlines on lb
                parts = []
                for node in lg_elem.iter():
                    tag = node.tag if isinstance(node.tag, str) else ""
                    if tag.endswith("lb"):
                        parts.append("\n")
                    if node.text:
                        parts.append(node.text)
                    if node.tail:
                        parts.append(node.tail)
                text = "".join(parts)
                text = "\n".join([ln.strip() for ln in text.splitlines()])
                return text.strip()
            return "\n".join(lines).strip()

        lgs = root.findall(".//tei:lg[@type='poem']", ns)
        if not lgs:
            lgs = root.findall(".//tei:lg", ns)

        for lg in lgs:
            head_text = ""
            head = lg.find("tei:head", ns)
            if head is not None and head.text:
                head_text = head.text.strip()
            # Only consider as a poem if there is some content
            poem_body = extract_lg_text(lg)
            # Capture xml:id for the poem lg element
            xml_id = lg.get("{http://www.w3.org/XML/1998/namespace}id", "")
            if head_text:
                poems.append(head_text)
                poems_texts.append(poem_body)
                poem_ids.append(xml_id)

        return {
            "author": author,
            "book_title": book_title,
            "year": year,
            "poems": poems,
            "poems_texts": poems_texts,
            "book_url": book_url,
            "poem_ids": poem_ids,
        }

    except ET.ParseError as e:
        print(f"Error parsing XML file {file_name}: {e}")
        return None


def enrich_poem_data_from_github(poem_collections: dict) -> Dict[str, Dict]:
    poem_data = {}
    # Create dropdown data from GitHub collections
    for file_name, book_data in poem_collections.items():
        author = book_data["author"]

        # Add each poem from the collection
        for idx, poem_title in enumerate(book_data["poems"]):
            dropdown_label = f"{poem_title} - {author}"
            poem_data[dropdown_label] = {
                "file": file_name,
                "poem_id": (
                    book_data.get("poem_ids", [""] * len(book_data["poems"]))[idx]
                    if idx < len(book_data.get("poem_ids", []))
                    else ""
                ),
                "title": poem_title,
                "author": author,
                "book_title": book_data["book_title"],
                "year": book_data["year"],
                "poem_index": idx,
                "source": "github",
                "book_url": book_data.get("book_url", ""),
                "text": (
                    book_data.get("poems_texts", [""] * len(book_data["poems"]))[idx]
                    if idx < len(book_data.get("poems_texts", []))
                    else ""
                ),
            }

    return poem_data


def fetch_poems_from_github(max_files: int = 5) -> Dict[str, Dict]:
    """
    Fetch and parse poem data from the GitHub repository.

    Args:
        max_files: Maximum number of XML files to process

    Returns:
        Dictionary mapping file names to poem metadata
    """
    print(f"Fetching poem files from GitHub repository {REPO_OWNER}/{REPO_NAME}...")

    # Get list of XML files
    files = fetch_github_repo_contents(max_files=max_files)

    if not files:
        print("No files found or error fetching from GitHub")
        return {}

    print(f"Found {len(files)} XML files, processing...")

    poem_collections = {}

    for file_info in files:
        file_name = file_info.get("name")
        download_url = file_info.get("download_url")

        if not file_name or not download_url:
            continue

        print(f"  Processing {file_name}...")

        # Fetch XML content
        xml_content = fetch_xml_file_content(download_url)
        if not xml_content:
            continue

        # Parse XML
        parsed_data = parse_tei_xml(xml_content, file_name)
        if parsed_data and parsed_data["poems"]:
            poem_collections[file_name] = parsed_data
            print(
                f"    Found {len(parsed_data['poems'])} poems by {parsed_data['author']}"
            )
    poem_data = enrich_poem_data_from_github(poem_collections)
    return poem_data


# Sample TEI XML data embedded for offline parsing
# In production, you could fetch from GitHub API or use local copies

SAMPLE_POEMS = {
    "2006081600051.xml": {
        "author": "Mortensson-Egnund, Ivar",
        "book_title": "Or duldo: draumkvæe",
        "year": "1895",
        "poems": [
            "Maaneljos",
            "Uro",
            "Kven æ du?",
            "Dæ ropar eit maal",
            "Vaar",
            "Baanehender",
            "Ei go tiend",
            "Mannaord",
            "Livsens leik",
            "Høgt leite",
            "Uten titel",
            "Utferd",
            "Mannavyrdna",
            "Tirande glør",
            "Fivreld",
            "Ein liten ting",
            "Liv aa sæle",
            "Vitjing",
            "Got aa fagert",
            "Glitretindar",
            "Eg tenkte",
            "Fela",
            "Husk",
            "Kattejerd",
            "Eld aa vatn",
        ],
    },
    "2006082400076.xml": {
        "author": "Randers, Kristofer",
        "book_title": "En Kjærlighedsvaar : Digt-Cyklus",
        "year": "1894",
        "poems": [
            "Forord",
            "Tilegnelse til 1ste Udgave",
            "Tilegnelse til 2den Udgave",
            "Til Kjærligheden",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "Aftenhvisken",
            "Tonerne",
            "I krydsilden",
            "Rosen og Tistlen",
            "Bellas Hjerte",
            "Visitten i Helvede",
            "Amors Besøg",
            "Alvorsord",
            "Tømmermænd",
            "Drømmen",
            "Pandora",
            "Stille Lykke",
            "Kjærlighedssang",
            "Min Skat",
            "Digtersorg",
        ],
    },
}


def create_poem_dropdown_data() -> Dict[str, Dict]:
    """
    Create dropdown data structure with format: {"Title - Author": {"file": "...", "xml_id": "..."}}
    """
    poem_data = {}

    # Process each book collection
    for file_name, book_data in SAMPLE_POEMS.items():
        author = book_data["author"]

        # Add each poem from the collection
        for idx, poem_title in enumerate(
            book_data["poems"][:15]
        ):  # Limit to first 15 poems per book
            # Create dropdown label: "Poem Title - Author"
            dropdown_label = f"{poem_title} - {author}"

            poem_data[dropdown_label] = {
                "file": file_name,
                "book_title": book_data["book_title"],
                "year": book_data["year"],
                "poem_index": idx,
            }

    return poem_data


def main():
    """Generate poem data and save to JSON file"""
    import sys

    # Check command line arguments
    use_github = "--github" in sys.argv
    use_poetree = "--poetree" in sys.argv
    max_items = 100  # Default limit

    # Check for custom limit
    for arg in sys.argv:
        if arg.startswith("--max="):
            try:
                max_items = int(arg.split("=")[1])
            except ValueError:
                print(f"Invalid max value: {arg}")

    poem_data = {}

    if use_poetree:
        print("Fetching poems from PoeTree...")
        poem_data = fetch_poetree_poems(max_poems=max_items)
        if not poem_data:
            print("Failed to fetch from PoeTree API, falling back to sample data")
            poem_data = create_poem_dropdown_data()

    elif use_github:
        print("Fetching poems from GitHub API...")
        poem_data = fetch_poems_from_github(max_files=max_items)

        if not poem_data:
            print("Failed to fetch from GitHub, falling back to sample data")
            poem_data = create_poem_dropdown_data()
    else:
        print("Using embedded sample data")
        print("Use --poetree to fetch from PoeTree API")
        print("Use --github to fetch from GitHub repository")
        poem_data = create_poem_dropdown_data()

    print(f"\nGenerated {len(poem_data)} poems")
    print("\nSample entries:")
    for label in random.sample(tuple(poem_data.keys()), 5):
        print(f"  - {label}")

    # Save to JSON file for use in web app
    output_file = "static/poems.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(poem_data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved poem data to {output_file}")


if __name__ == "__main__":
    main()
