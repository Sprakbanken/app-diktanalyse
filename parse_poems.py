"""
Script to parse TEI XML files from norn-uio/norn-poems and extract poem titles with authors.
Creates a JSON file with poem data for the dropdown menu.
"""

import json
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
REPO_OWNER = "norn-uio"
REPO_NAME = "norn-poems"
REPO_PATH = "TEI"  # Path to XML files in the repository

# PoeTree API configuration
POETREE_API_BASE = "https://versologie.cz/poetree/api"


def fetch_poetree_poems(max_poems: Optional[int] = None) -> List[Dict]:
    """
    Fetch NORN poems from the PoeTree API.

    Args:
        max_poems: Maximum number of poems to fetch (None for all)

    Returns:
        List of poem dictionaries with metadata
    """
    url = f"{POETREE_API_BASE}/poems?corpus=no"

    try:
        print(f"Fetching poems from PoeTree API: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        poems = response.json()

        if not isinstance(poems, list):
            print(f"Unexpected response format: {type(poems)}")
            return []

        print(f"Fetched {len(poems)} poems from PoeTree API")

        if max_poems:
            poems = poems[:max_poems]
            print(f"Limited to {len(poems)} poems")

        # Enrich poems with full text by fetching /poem/{id} and using `body`
        enriched = []
        for p in poems:
            poem_id = p.get("id")
            text_body = ""
            if poem_id is not None:
                try:
                    detail_url = f"{POETREE_API_BASE}/poem/{poem_id}"
                    dresp = requests.get(detail_url, timeout=20)
                    dresp.raise_for_status()
                    detail = dresp.json()
                    text_body = detail.get("body", "")
                except requests.RequestException as e:
                    print(f"Error fetching poem {poem_id} body: {e}")

            # Copy original dict and attach text
            p_copy = dict(p)
            if isinstance(text_body, str):
                p_copy["text"] = text_body
            enriched.append(p_copy)

        return enriched

    except requests.RequestException as e:
        print(f"Error fetching poems from PoeTree API: {e}")
        return []


def process_poetree_poems(poems: List[Dict]) -> Dict[str, Dict]:
    """
    Process PoeTree API poems into the format used by the app.

    Args:
        poems: List of poem dictionaries from PoeTree API

    Returns:
        Dictionary mapping display labels to poem metadata
    """
    poem_data = {}

    for idx, poem in enumerate(poems):
        # Extract metadata from PoeTree format
        title = poem.get("title", f"Untitled {idx}")
        author = poem.get("author", "Unknown")
        year = poem.get("year", "")
        poem_id = poem.get("id", idx)
        text = poem.get("text", "")

        # Create dropdown label
        dropdown_label = f"{title} - {author}"

        poem_data[dropdown_label] = {
            "id": poem_id,
            "title": title,
            "author": author,
            "year": str(year) if year else "",
            "text": text if isinstance(text, str) else "",
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

        # Try to find publication year
        date_elem = root.find(".//tei:date", ns)
        if date_elem is not None:
            year = date_elem.get("when", date_elem.text or "").strip()

        # Extract poem titles and texts from lg elements
        poems = []
        poems_texts = []

        def extract_lg_text(lg_elem):
            lines = []
            # Collect line elements; if absent, try collecting text nodes
            for l in lg_elem.findall(".//tei:l", ns):
                if l.text:
                    lines.append(l.text.strip())
                # Include tail text after inline tags
                if l.tail and l.tail.strip():
                    lines.append(l.tail.strip())
            # Handle explicit line breaks <lb/>
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
                # Normalize multiple newlines and strip
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
            if head_text:
                poems.append(head_text)
                poems_texts.append(poem_body)

        return {
            "author": author,
            "book_title": book_title,
            "year": year,
            "poems": poems,
            "poems_texts": poems_texts,
        }

    except ET.ParseError as e:
        print(f"Error parsing XML file {file_name}: {e}")
        return None


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

    poems_data = {}

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
            poems_data[file_name] = parsed_data
            print(
                f"    Found {len(parsed_data['poems'])} poems by {parsed_data['author']}"
            )

    return poems_data


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
        print("Fetching poems from PoeTree API...")
        poems = fetch_poetree_poems(max_poems=max_items)

        if poems:
            poem_data = process_poetree_poems(poems)
        else:
            print("Failed to fetch from PoeTree API, falling back to sample data")
            poem_data = create_poem_dropdown_data()

    elif use_github:
        print("Fetching poems from GitHub API...")
        poem_collections = fetch_poems_from_github(max_files=max_items)

        if not poem_collections:
            print("Failed to fetch from GitHub, falling back to sample data")
            poem_collections = SAMPLE_POEMS

        # Create dropdown data from GitHub collections
        for file_name, book_data in poem_collections.items():
            author = book_data["author"]

            # Add each poem from the collection
            for idx, poem_title in enumerate(book_data["poems"][:15]):
                dropdown_label = f"{poem_title} - {author}"
                poem_data[dropdown_label] = {
                    "file": file_name,
                    "book_title": book_data["book_title"],
                    "year": book_data["year"],
                    "poem_index": idx,
                    "source": "github",
                    "text": (
                        book_data.get("poems_texts", [""] * len(book_data["poems"]))[
                            idx
                        ]
                        if idx < len(book_data.get("poems_texts", []))
                        else ""
                    ),
                }
    else:
        print("Using embedded sample data")
        print("Use --poetree to fetch from PoeTree API")
        print("Use --github to fetch from GitHub repository")
        poem_data = create_poem_dropdown_data()

    print(f"\nGenerated {len(poem_data)} poems")
    print("\nSample entries:")
    for label in list(poem_data.keys())[:5]:
        print(f"  - {label}")

    # Save to JSON file for use in web app
    output_file = "static/poems.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(poem_data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved poem data to {output_file}")


if __name__ == "__main__":
    main()
