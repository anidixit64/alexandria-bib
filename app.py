from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)


def search_wikipedia(query):
    """Search Wikipedia for a topic and return the best matching page"""
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": 1,
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["query"]["search"]:
            return data["query"]["search"][0]["title"]
        return None
    except Exception as e:
        print(f"Error searching Wikipedia: {e}")
        return None


def get_wikipedia_content(page_title):
    """Get the HTML content of a Wikipedia page"""
    url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching Wikipedia page: {e}")
        return None


def extract_bibliography_sections(html_content):
    """Extract bibliography, sources, further reading, or references sections"""
    soup = BeautifulSoup(html_content, "html.parser")

    # Look for different section headers
    section_headers = [
        "Bibliography",
        "Sources",
        "Further Reading",
        "References",
        "bibliography",
        "sources",
        "further reading",
        "references",
    ]

    sections = []

    # Find all h2 and h3 headers
    headers = soup.find_all(["h2", "h3"])

    for header in headers:
        header_text = header.get_text().strip().lower()

        # Check if this header matches any of our target sections
        for target in section_headers:
            if target.lower() in header_text:
                # Get the next sibling elements until we hit another header
                content = []
                current = header.find_next_sibling()

                while current and current.name not in [
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6",
                ]:
                    if current.name:
                        content.append(str(current))
                    current = current.find_next_sibling()

                sections.append(
                    {"title": header.get_text().strip(), "content": "\n".join(content)}
                )
                break

    return sections


def extract_book_citations(html_content):
    """Extract book citations that contain ISBN numbers"""
    soup = BeautifulSoup(html_content, "html.parser")
    citations = []

    # Updated citation selectors to include more sections
    citation_selectors = [
        "ol li",
        "ul li",
        ".reflist li",
        ".references li",
        "#References li",
        "#Bibliography li",
        "#Sources li",
        "#Further_Reading li",
        "#Notes li",
        "#Citations li",
        "#Primary_Sources li",
        "#Secondary_Sources li",
        "h2:contains('References') + ol li",
        "h2:contains('Bibliography') + ol li",
        "h2:contains('Sources') + ol li",
        "h2:contains('Further Reading') + ol li",
        "h2:contains('Notes') + ol li",
        "h2:contains('Citations') + ol li",
        "h2:contains('Primary Sources') + ol li",
        "h2:contains('Secondary Sources') + ol li",
        "h3:contains('References') + ol li",
        "h3:contains('Bibliography') + ol li",
        "h3:contains('Sources') + ol li",
        "h3:contains('Further Reading') + ol li",
        "h3:contains('Notes') + ol li",
        "h3:contains('Citations') + ol li",
        "h3:contains('Primary Sources') + ol li",
        "h3:contains('Secondary Sources') + ol li",
    ]

    for selector in citation_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text()
            isbn_pattern = r"ISBN[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+"
            if re.search(isbn_pattern, text, re.IGNORECASE):
                # Clean up the citation text - remove '^ ' and lowercase letter sequences
                citation = re.sub(r"\s+", " ", text).strip()
                citation = re.sub(r"^\^\s*", "", citation).strip()
                citation = re.sub(
                    r"^[a-z\s]+\s",
                    "",
                    citation,
                )
                citation = citation.strip()

                # Apply additional cleaning rules
                citation = clean_citation(citation)

                # Ensure we have a meaningful citation
                if citation and len(citation) > 10:
                    citations.append(citation)

    # Also look for citations in specific sections by finding headers and their content
    section_headers = [
        "References",
        "Bibliography",
        "Sources",
        "Further Reading",
        "Notes",
        "Citations",
        "Primary Sources",
        "Secondary Sources",
    ]

    # Find all h2 and h3 headers
    headers = soup.find_all(["h2", "h3"])

    for header in headers:
        header_text = header.get_text().strip()

        # Check if this header matches any of our target sections
        if any(target.lower() in header_text.lower() for target in section_headers):
            # Get the next sibling elements until we hit another header
            current = header.find_next_sibling()

            while current and current.name not in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if current.name in ["ol", "ul"]:
                    # Extract list items from this list
                    list_items = current.find_all("li")
                    for item in list_items:
                        text = item.get_text()
                        isbn_pattern = (
                            r"ISBN[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+"
                        )
                        if re.search(isbn_pattern, text, re.IGNORECASE):
                            citation = re.sub(r"\s+", " ", text).strip()
                            citation = re.sub(r"^\^\s*", "", citation).strip()
                            citation = re.sub(r"^[a-z\s]+\s", "", citation).strip()

                            # Apply additional cleaning rules
                            citation = clean_citation(citation)

                            if citation and len(citation) > 10:
                                citations.append(citation)
                current = current.find_next_sibling()

    # Remove duplicates while preserving order
    unique_citations = []
    seen = set()
    for citation in citations:
        if citation not in seen:
            unique_citations.append(citation)
            seen.add(citation)

    # Filter to only include citations with dates in parentheses
    filtered_citations = []
    date_pattern = r"\([^)]*(?:\d{4}|\d{1,2}\s+[A-Za-z]+(?:\s+\d{4})?)[^)]*\)"

    for citation in unique_citations:
        if re.search(date_pattern, citation, re.IGNORECASE):
            filtered_citations.append(citation)

    return filtered_citations


def clean_citation(citation):
    """
    Clean citation text by:
    1. Removing everything after the ISBN number
    2. Removing page numbers (pp. 139–141, p. 251, etc.)
    3. Removing (PDF) from book titles

    Args:
        citation (str): Raw citation text

    Returns:
        str: Cleaned citation text
    """
    if not citation:
        return citation

    # Step 1: Remove everything after the ISBN number
    # Pattern to match ISBN followed by numbers and hyphens
    isbn_pattern = r"ISBN[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+"
    isbn_match = re.search(isbn_pattern, citation, re.IGNORECASE)

    if isbn_match:
        # Keep only up to and including the ISBN
        citation = citation[:isbn_match.end()].strip()

    # Step 2: Remove page numbers
    # Pattern to match various page number formats
    page_patterns = [
        r"\s+pp\.\s+\d+[–—−-]\d+\.?",  # pp. 139–141
        r"\s+p\.\s+\d+\.?",  # p. 251
        r"\s+pages?\s+\d+[–—−-]\d+\.?",  # pages 139-141
        r"\s+page\s+\d+\.?",  # page 251
    ]

    for pattern in page_patterns:
        citation = re.sub(pattern, "", citation, flags=re.IGNORECASE)

    # Step 3: Remove (PDF) from book titles
    # Pattern to match (PDF) with optional spaces around it
    pdf_pattern = r"\s*\(PDF\)\s*"
    citation = re.sub(pdf_pattern, "", citation, flags=re.IGNORECASE)

    # Clean up any extra whitespace and fix spaces before periods
    citation = re.sub(r"\s+\.", ".", citation)  # Remove space(s) before period
    citation = re.sub(r"\s+", " ", citation).strip()
    citation = re.sub(r"\.\s*$", "", citation)  # Remove trailing period

    return citation


def type_1_parser(citation):
    """
    Parse Type I citations that contain parenthetical dates.
    Extracts author names, year/date, title, and ISBN from the citation.

    Args:
        citation (str): A citation string that contains parenthetical dates

    Returns:
        dict: Parsed citation data with authors, year, title, isbn, and
        remaining_text fields
    """
    if not citation:
        return {
            "authors": None,
            "year": None,
            "title": None,
            "isbn": None,
            "remaining_text": "",
        }

    # Initialize result
    result = {
        "authors": None,
        "year": None,
        "title": None,
        "isbn": None,
        "remaining_text": citation,
    }

    # Extract year/date from parentheses
    # Pattern to match (2003) or (January 5, 1980) or (March 6, 1987)
    date_pattern = r"\([^)]*(?:\d{4}|\d{1,2}\s+[A-Za-z]+(?:\s+\d{4})?)[^)]*\)"
    date_match = re.search(date_pattern, citation, re.IGNORECASE)

    if date_match:
        date_text = date_match.group(0)
        date_start = date_match.start()
        date_end = date_match.end()

        # Extract authors from everything before the parentheses
        authors = citation[:date_start].strip()
        result["authors"] = authors

        # Extract just the year (4 digits)
        year_match = re.search(r"\d{4}", date_text)
        if year_match:
            result["year"] = year_match.group(0)

        # Extract title from after the parentheses to the next period, comma,
        # or before publisher/ISBN
        text_after_date = citation[date_end:].strip()
        if text_after_date.startswith("."):
            text_after_date = text_after_date[1:].strip()
        if text_after_date.startswith(","):
            text_after_date = text_after_date[1:].strip()
        # Skip over additional years in brackets like [1961]
        bracket_year_pattern = r"^\s*\[\d{4}\]\s*\.?\s*"
        bracket_match = re.match(bracket_year_pattern, text_after_date)
        if bracket_match:
            text_after_date = text_after_date[bracket_match.end():].strip()
        # Find the next period, 'ISBN', 'p.', 'pp.', 'retrieved', or 'archived',
        # or a comma before publisher/ISBN
        publisher_keywords = [
            "press",
            "publishing",
            "publisher",
            "university",
            "blackwell",
            "princeton",
            "cambridge",
            "oxford",
            "harvard",
            "yale",
            "penguin",
            "random house",
            "simon & schuster",
            "wiley",
            "springer",
            "elsevier",
            "macmillan",
            "routledge",
            "academic press",
            "london & new york",
            "london",
            "new york",
            "isbn",
            "retrieved",
            "archived",
        ]
        # Find comma followed by publisher-like word or ISBN/retrieved/archived
        comma_pat = re.compile(
            r",\s*([A-Za-z& ]+)(?:\s*:\s*[A-Za-z& ]+)?", re.IGNORECASE
        )
        comma_match = comma_pat.search(text_after_date)
        comma_stop = None
        if comma_match:
            next_word = comma_match.group(1).strip().lower()
            for kw in publisher_keywords:
                if next_word.startswith(kw):
                    comma_stop = comma_match.start()
                    break
        # Find the next period, 'ISBN', 'p.', 'pp.', 'retrieved', or 'archived'
        # But don't stop at parentheses that are part of the title
        stop_patterns = [
            r"\.",
            r"ISBN",
            r" p\.",
            r" pp\.",
            r"\s+retrieved",
            r"\s+archived",
        ]
        stops = []
        for pat in stop_patterns:
            matches = list(re.finditer(pat, text_after_date, re.IGNORECASE))
            for match in matches:
                # Check if this stop is inside parentheses (part of title)
                pos = match.start()
                # Count parentheses before this position
                open_parens = text_after_date[:pos].count("(")
                close_parens = text_after_date[:pos].count(")")
                # If we're inside parentheses, skip this stop
                if open_parens > close_parens:
                    continue
                stops.append(pos)
        if comma_stop is not None:
            stops.append(comma_stop)
        if stops:
            stop_index = min(stops)
            title = text_after_date[:stop_index].strip()
        else:
            title = text_after_date.strip()
        # Remove (PDF) from title
        title = re.sub(r"\s*\(PDF\)\s*", "", title, flags=re.IGNORECASE)
        # Remove trailing period
        title = re.sub(r"\.+$", "", title).strip()
        result["title"] = title
        # Remove the title from the remaining text
        if stops:
            remaining = text_after_date[stop_index:].strip()
            # Remove leading punctuation/whitespace
            remaining = re.sub(r"^[\.,\s]+", "", remaining)
            result["remaining_text"] = remaining
        else:
            result["remaining_text"] = ""

    # Extract ISBN
    # Pattern to match ISBN followed by numbers and hyphens
    isbn_pattern = r"ISBN\s+([0-9\-]+)"
    isbn_match = re.search(isbn_pattern, result["remaining_text"], re.IGNORECASE)

    if isbn_match:
        result["isbn"] = isbn_match.group(1)
        # Remove the entire ISBN from the remaining text
        isbn_full = isbn_match.group(0)  # This includes "ISBN " and the number
        result["remaining_text"] = (
            result["remaining_text"].replace(isbn_full, "").strip()
        )

    return result


def type_3_parser(citation):
    """
    Parse Type III citations that contain quoted chapter titles.
    Extracts chapter authors, year, chapter title, book authors, book title, and ISBN.

    Format: Chapter Authors (year). 'Chapter Title'. In Book Authors (eds.).
    Book Title. Publisher. ISBN.

    Args:
        citation (str): A citation string that contains quoted chapter titles

    Returns:
        dict: Parsed citation data with chapter_authors, book_authors, year,
        chapter_title, book_title, isbn, and remaining_text fields
    """
    if not citation:
        return {
            "chapter_authors": None,
            "book_authors": None,
            "year": None,
            "chapter_title": None,
            "book_title": None,
            "isbn": None,
            "remaining_text": citation,
        }

    # Initialize result
    result = {
        "chapter_authors": None,
        "book_authors": None,
        "year": None,
        "chapter_title": None,
        "book_title": None,
        "isbn": None,
        "remaining_text": citation,
    }

    # Extract year/date from parentheses
    date_pattern = r"\([^)]*(?:\d{4}|\d{1,2}\s+[A-Za-z]+(?:\s+\d{4})?)[^)]*\)"
    date_match = re.search(date_pattern, citation, re.IGNORECASE)

    if date_match:
        date_text = date_match.group(0)
        date_start = date_match.start()
        date_end = date_match.end()

        # Extract chapter authors from everything before the parentheses
        chapter_authors = citation[:date_start].strip()
        result["chapter_authors"] = chapter_authors

        # Extract just the year (4 digits)
        year_match = re.search(r"\d{4}", date_text)
        if year_match:
            result["year"] = year_match.group(0)

        # Extract chapter title from quoted text after the parentheses
        text_after_date = citation[date_end:].strip()
        if text_after_date.startswith("."):
            text_after_date = text_after_date[1:].strip()

        # Remove comma if it appears immediately after the parentheses
        if text_after_date.startswith(","):
            text_after_date = text_after_date[1:].strip()

        # Find quoted chapter title (single or double quotes)
        quote_pattern = r'[\'"]([^\'"]+)[\'"]'
        quote_match = re.search(quote_pattern, text_after_date)

        if quote_match:
            chapter_title = quote_match.group(1)
            result["chapter_title"] = chapter_title

            # Get text after the quoted chapter title
            text_after_quote = text_after_date[quote_match.end():].strip()

            # Clean up text_after_quote for leading commas/whitespace
            text_after_quote = text_after_quote.lstrip(", ").strip()
            # Look for "in" followed by book authors and "(eds.)"
            in_pattern = r"in\s+([^\(]+\(eds?\.\))[,\.]"
            in_match = re.search(in_pattern, text_after_quote, re.IGNORECASE)

            if in_match:
                book_authors = in_match.group(1).strip()
                result["book_authors"] = book_authors
                # Get text after the "in... (eds.)," or "." part
                text_after_in = text_after_quote[in_match.end():].strip()
                # Extract book title (everything up to the next comma, or period
                # if no comma)
                comma_index = text_after_in.find(",")
                if comma_index != -1:
                    book_title = text_after_in[:comma_index].strip()
                    result["book_title"] = book_title
                    result["remaining_text"] = text_after_in[comma_index + 1:].strip()
                else:
                    # Fallback to previous logic: up to the next period
                    book_title_pattern = r"^(.*?\([^)]*\))?[^.]*\."
                    book_title_match = re.match(book_title_pattern, text_after_in)
                    if book_title_match:
                        book_title = book_title_match.group(0).strip()
                        if book_title.endswith("."):
                            book_title = book_title[:-1]
                        result["book_title"] = book_title
                        idx = len(book_title_match.group(0))
                        result["remaining_text"] = text_after_in[idx:].strip()
                    else:
                        next_period_index = text_after_in.find(".")
                        if next_period_index != -1:
                            book_title = text_after_in[:next_period_index].strip()
                            result["book_title"] = book_title
                            idx = next_period_index + 1
                            result["remaining_text"] = text_after_in[idx:].strip()
                        else:
                            result["book_title"] = text_after_in
                            result["remaining_text"] = ""
            else:
                result["remaining_text"] = text_after_quote
        else:
            # If no quoted chapter title found, treat as regular citation
            result["remaining_text"] = text_after_date

    # Extract ISBN
    isbn_pattern = r"ISBN\s+([0-9\-]+)"
    isbn_match = re.search(isbn_pattern, result["remaining_text"], re.IGNORECASE)

    if isbn_match:
        result["isbn"] = isbn_match.group(1)
        # Remove the entire ISBN from the remaining text
        isbn_full = isbn_match.group(0)  # This includes "ISBN " and the number
        result["remaining_text"] = (
            result["remaining_text"].replace(isbn_full, "").strip()
        )

    return result


def type_2_parser(citation):
    """
    Parse Type II citations that have standalone years (not in parentheses).
    Extracts authors, year, title, and ISBN from the citation.

    Format: Authors, Title, Publisher, Year, ISBN.

    Args:
        citation (str): A citation string that contains standalone years

    Returns:
        dict: Parsed citation data with authors, year, title, isbn, and
        remaining_text fields
    """
    if not citation:
        return {
            "authors": None,
            "year": None,
            "title": None,
            "isbn": None,
            "remaining_text": citation,
        }

    # Initialize result
    result = {
        "authors": None,
        "year": None,
        "title": None,
        "isbn": None,
        "remaining_text": citation,
    }

    # Extract ISBN first
    isbn_pattern = r"ISBN\s+([0-9\-X]+)"
    isbn_match = re.search(isbn_pattern, citation, re.IGNORECASE)

    if isbn_match:
        result["isbn"] = isbn_match.group(1)
        # Remove the entire ISBN from the citation
        isbn_full = isbn_match.group(0)
        citation = citation.replace(isbn_full, "").strip()

    # Extract year (4-digit number)
    year_pattern = r"\b(19|20)\d{2}\b"
    year_match = re.search(year_pattern, citation)

    # Always define author_year_match
    author_year_pattern = r"^([^\(]+)\s*\(\d{4}\)\."
    author_year_match = re.match(author_year_pattern, citation)

    if year_match:
        result["year"] = year_match.group(0)
        year_start = year_match.start()
        year_end = year_match.end()

        publisher_keywords = [
            "press",
            "publishing",
            "publisher",
            "university",
            "blackwell",
            "princeton",
            "cambridge",
            "oxford",
            "harvard",
            "yale",
            "penguin",
            "random house",
            "simon & schuster",
            "wiley",
            "springer",
            "elsevier",
            "macmillan",
            "routledge",
            "academic press",
            "london & new york",
            "london",
            "new york",
            "isbn",
            "retrieved",
            "archived",
        ]
        text_before_year = citation[:year_start]
        title_end = year_start
        for keyword in publisher_keywords:
            pattern = rf",\s*[^,]*{re.escape(keyword)}[^,]*"
            match = re.search(pattern, text_before_year, re.IGNORECASE)
            if match:
                title_end = match.start()
                break

        # Check if this is a "Title (year) by Author" format
        by_pattern = r"by\s+([^\(]+?)\s*\([^\)]+\)"
        by_match = re.search(by_pattern, citation, re.IGNORECASE)
        if by_match:
            author_part = by_match.group(1).strip()
            author = re.sub(r"\s*\([^\)]*\)\s*$", "", author_part).strip()
            citation_without_author = citation[: by_match.start()].strip()
            title = citation_without_author[:year_start].strip()
            title = re.sub(r",\s*$", "", title).strip()
            title = re.sub(r"\s*\(\s*$", "", title).strip()
            result["authors"] = author
            result["title"] = title
            result["remaining_text"] = citation[year_end:by_match.start()].strip()
            result["remaining_text"] = re.sub(
                r"^[\.,\s]+", "", result["remaining_text"]
            )
        elif author_year_match:
            # Sorensen style: Author (year). Title. Publisher.
            authors = author_year_match.group(1).strip()
            title_start = author_year_match.end()
            after_year = citation[title_start:]
            # Find the last period before 'Press', 'Publisher', or 'ISBN'
            pub_keywords = ["Press", "Publisher", "ISBN"]
            last_period = -1
            for kw in pub_keywords:
                idx = after_year.find(kw)
                if idx != -1:
                    # Find the last period before this keyword
                    period_idx = after_year.rfind(".", 0, idx)
                    if period_idx > last_period:
                        last_period = period_idx
            if last_period != -1:
                title = after_year[:last_period].strip()
                remaining = after_year[last_period + 1:].strip()
            else:
                # fallback: up to the last period
                period_idx = after_year.rfind(".")
                if period_idx != -1:
                    title = after_year[:period_idx].strip()
                    remaining = after_year[period_idx + 1:].strip()
                else:
                    title = after_year.strip()
                    remaining = ""
            result["authors"] = authors
            result["title"] = title
            result["remaining_text"] = remaining
        else:
            # Standard format: Authors, Title, Publisher, Year
            ed_match = list(re.finditer(r"ed\.,", citation[:title_end], re.IGNORECASE))
            if ed_match:
                first_ed = ed_match[0]
                authors = citation[: first_ed.end()].strip()
                authors = re.sub(r",\s*$", "", authors)
                rest = citation[first_ed.end():title_end].lstrip(", ")
                parts = [p.strip() for p in rest.split(",") if p.strip()]
                if len(parts) >= 2:
                    title = ", ".join(parts[:2])
                elif parts:
                    title = parts[0]
                else:
                    title = ""
                result["authors"] = authors
                result["title"] = title
            else:
                comma_indices = [
                    m.start() for m in re.finditer(",", citation[:title_end])
                ]
                if comma_indices:
                    last_author_comma = comma_indices[-1]
                    authors = citation[:last_author_comma].strip()
                    authors = re.sub(r",\s*$", "", authors)
                    title_start = last_author_comma + 1
                    result["authors"] = authors
                    result["title"] = citation[title_start:title_end].strip()
                else:
                    authors = citation[:year_start].strip()
                    authors = re.sub(r",\s*$", "", authors)
                    title_start = year_end
                    result["authors"] = authors
                    result["title"] = citation[title_start:title_end].strip()
        # Remaining text is everything after the year
        if not result["remaining_text"]:
            result["remaining_text"] = citation[year_end:].strip()
            result["remaining_text"] = re.sub(
                r"^[\.,\s]+", "", result["remaining_text"]
            )
    else:
        result["remaining_text"] = citation

    return result


def type_4_parser(citation):
    """
    Parse Type IV citations that have quoted chapter titles without parenthetical
    dates. Extracts chapter authors, year, chapter title, book authors, book
    title, and ISBN.

    Format: Chapter Authors, "Chapter Title", in Book Authors (eds.), Book Title,
    Publisher, Year. ISBN.

    Args:
        citation (str): A citation string that contains quoted chapter titles
        without parenthetical dates

    Returns:
        dict: Parsed citation data with chapter_authors, book_authors, year,
        chapter_title, book_title, isbn, and remaining_text fields
    """
    if not citation:
        return {
            "chapter_authors": None,
            "book_authors": None,
            "year": None,
            "chapter_title": None,
            "book_title": None,
            "isbn": None,
            "remaining_text": citation,
        }

    # Initialize result
    result = {
        "chapter_authors": None,
        "book_authors": None,
        "year": None,
        "chapter_title": None,
        "book_title": None,
        "isbn": None,
        "remaining_text": citation,
    }

    # First, try to find quoted chapter title
    quote_pattern = r'[\'"]([^\'"]+)[\'"]'
    quote_match = re.search(quote_pattern, citation)

    if quote_match:
        chapter_title = quote_match.group(1)
        result["chapter_title"] = chapter_title

        # Get text before and after the quoted title
        text_before_quote = citation[: quote_match.start()].strip()
        text_after_quote = citation[quote_match.end() :].strip()

        # Extract chapter authors from text before the quote
        # Look for the last comma before the quote
        comma_indices = [m.start() for m in re.finditer(",", text_before_quote)]
        if comma_indices:
            last_comma = comma_indices[-1]
            chapter_authors = text_before_quote[:last_comma].strip()
            result["chapter_authors"] = chapter_authors
        else:
            result["chapter_authors"] = text_before_quote

        # Clean up text_after_quote for leading commas/whitespace
        text_after_quote = text_after_quote.lstrip(", ").strip()

        # Look for "in" followed by book authors and "(eds.)"
        in_pattern = r"in\s+([^\(]+\(eds?\.\))[,\.]"
        in_match = re.search(in_pattern, text_after_quote, re.IGNORECASE)

        if in_match:
            book_authors = in_match.group(1).strip()
            result["book_authors"] = book_authors
            # Get text after the "in... (eds.)," or "." part
            text_after_in = text_after_quote[in_match.end():].strip()
            # Extract book title (everything up to the next comma, or period
            # if no comma)
            comma_index = text_after_in.find(",")
            if comma_index != -1:
                book_title = text_after_in[:comma_index].strip()
                result["book_title"] = book_title
                result["remaining_text"] = text_after_in[comma_index + 1:].strip()
            else:
                # Fallback to previous logic: up to the next period
                book_title_pattern = r"^(.*?\([^)]*\))?[^.]*\."
                book_title_match = re.match(book_title_pattern, text_after_in)
                if book_title_match:
                    book_title = book_title_match.group(0).strip()
                    if book_title.endswith("."):
                        book_title = book_title[:-1]
                    result["book_title"] = book_title
                    result["remaining_text"] = text_after_in[
                        len(book_title_match.group(0)):
                    ].strip()
                else:
                    next_period_index = text_after_in.find(".")
                    if next_period_index != -1:
                        book_title = text_after_in[:next_period_index].strip()
                        result["book_title"] = book_title
                        result["remaining_text"] = text_after_in[
                            next_period_index + 1:
                        ].strip()
                    else:
                        result["book_title"] = text_after_in
                        result["remaining_text"] = ""
        else:
            result["remaining_text"] = text_after_quote

        # Extract year from remaining text
        year_pattern = r"\b(19|20)\d{2}\b"
        year_match = re.search(year_pattern, result["remaining_text"])
        if year_match:
            result["year"] = year_match.group(0)

    # Extract ISBN
    isbn_pattern = r"ISBN\s+([0-9\-]+)"
    isbn_match = re.search(isbn_pattern, result["remaining_text"], re.IGNORECASE)

    if isbn_match:
        result["isbn"] = isbn_match.group(1)
        # Remove the entire ISBN from the remaining text
        isbn_full = isbn_match.group(0)  # This includes "ISBN " and the number
        result["remaining_text"] = (
            result["remaining_text"].replace(isbn_full, "").strip()
        )

    return result


@app.route("/")
def home():
    return jsonify(
        {
            "message": "Alexandria API is running",
            "status": "success",
        }
    )


@app.route("/api/health")
def health_check():
    return jsonify({"status": "healthy", "service": "alexandria-backend"})


@app.route("/api/search", methods=["POST"])
def search_books():
    """Search for books based on a topic using Wikipedia"""
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query is required", "status": "error"}), 400
        page_title = search_wikipedia(query)
        if not page_title:
            return (
                jsonify(
                    {
                        "error": f'No Wikipedia page found for "{query}"',
                        "status": "error",
                    }
                ),
                404,
            )
        html_content = get_wikipedia_content(page_title)
        if not html_content:
            return (
                jsonify(
                    {
                        "error": f'Could not fetch content for "{page_title}"',
                        "status": "error",
                    }
                ),
                500,
            )
        citations = extract_book_citations(html_content)
        return jsonify(
            {
                "query": query,
                "page_title": page_title,
                "citations": citations,
                "count": len(citations),
                "status": "success",
            }
        )
    except Exception as e:
        print(f"Error in search_books: {e}")
        return jsonify({"error": "Internal server error", "status": "error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
