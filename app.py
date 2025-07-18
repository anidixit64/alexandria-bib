from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import requests
from bs4 import BeautifulSoup
import re
import redis
import json
import hashlib
import time

app = Flask(__name__)
CORS(app)

# Initialize Redis connection for caching
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


# User agent logging middleware
@app.before_request
def log_user_agent():
    """Log user agent information for incoming requests"""
    user_agent = request.headers.get("User-Agent", "Unknown")
    ip_address = request.remote_addr
    endpoint = request.endpoint
    method = request.method

    # Log user agent info (you can customize this format)
    print(f"[USER_AGENT] {method} {endpoint} - IP: {ip_address} - UA: {user_agent}")

    # You could also store this in Redis for analytics if needed
    # log_data = {
    #     'timestamp': datetime.now().isoformat(),
    #     'ip': ip_address,
    #     'user_agent': user_agent,
    #     'endpoint': endpoint,
    #     'method': method
    # }


# --- API Usage Monitoring Middleware ---
@app.before_request
def monitor_api_usage():
    endpoint = request.endpoint or "unknown"
    ip = request.remote_addr or "unknown"
    now = int(time.time())
    try:
        # Increment global and per-endpoint counters
        redis_client.incr("usage:total")
        redis_client.incr(f"usage:endpoint:{endpoint}")
        redis_client.incr(f"usage:ip:{ip}:endpoint:{endpoint}")
        # Track recent requests for trend analysis (set expiry for rolling window)
        redis_client.setex(f"usage:recent:{now}", 120, 1)
    except Exception:
        print("[USAGE MONITOR] Redis unavailable")


@app.route("/api/usage/stats")
def usage_stats():
    try:
        total = int(redis_client.get("usage:total") or 0)
        endpoints = [key for key in redis_client.scan_iter("usage:endpoint:*")]
        endpoint_counts = {
            k.split("usage:endpoint:")[1]: int(redis_client.get(k) or 0)
            for k in endpoints
        }
        return jsonify(
            {
                "total_requests": total,
                "per_endpoint": endpoint_counts,
                "status": "success",
            }
        )
    except Exception:
        return jsonify({"error": "Usage stats unavailable", "status": "error"}), 503


# --- Graceful Degradation for /api/search and /api/search/page ---


def check_redis_available():
    try:
        redis_client.ping()
        return True
    except Exception:
        return False


# --- Rate Limiting: Use Redis if available, else fallback to in-memory (for CI/dev) ---
def is_redis_available():
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        return True
    except Exception:
        return False


USE_REDIS_LIMITER = is_redis_available() and not os.environ.get("DISABLE_RATE_LIMITER")

if USE_REDIS_LIMITER:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["150 per minute"],
        storage_uri="redis://localhost:6379",
    )
else:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["150 per minute"],
        storage_uri="memory://",
    )


def get_cache_key(query, cache_type="search"):
    """Generate a cache key for the given query and cache type"""
    return f"alexandria:{cache_type}:{hashlib.md5(query.lower().encode()).hexdigest()}"


def get_cached_result(cache_key):
    """Get cached result from Redis"""
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        print(f"Error getting cached result: {e}")
    return None


def set_cached_result(cache_key, data, ttl=3600):
    """Set cached result in Redis with TTL (default 1 hour)"""
    try:
        redis_client.setex(cache_key, ttl, json.dumps(data))
    except Exception as e:
        print(f"Error setting cached result: {e}")


def search_wikipedia(query):
    """Search Wikipedia for a topic and return the best matching page"""
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": 10,  # Increased to get more results for disambiguation
    }

    # Custom headers with proper user agent for Wikipedia API
    headers = {
        "User-Agent": (
            "Alexandria-Bib/1.0 "
            "(https://github.com/your-repo/alexandria-bib; your-email@example.com) "
            "Python/3.12"
        )
    }

    try:
        response = requests.get(search_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data["query"]["search"]:
            return data["query"]["search"]
        return None
    except Exception as e:
        print(f"Error searching Wikipedia: {e}")
        return None


def search_wikipedia_with_suggestions(query):
    """Search Wikipedia and also get search suggestions for typos"""
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "format": "json",
        "search": query,
        "limit": 10,
        "namespace": 0,
    }

    # Custom headers with proper user agent for Wikipedia API
    headers = {
        "User-Agent": (
            "Alexandria-Bib/1.0 "
            "(https://github.com/your-repo/alexandria-bib; your-email@example.com) "
            "Python/3.12"
        )
    }

    try:
        response = requests.get(search_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        # opensearch returns: [query, [titles], [descriptions], [urls]]
        if len(data) >= 2 and data[1]:
            return data[1]  # Return list of suggested titles
        return []
    except Exception as e:
        print(f"Error getting Wikipedia suggestions: {e}")
        return []


def is_disambiguation_page(html_content):
    """Check if the HTML content is a disambiguation page"""
    soup = BeautifulSoup(html_content, "html.parser")

    # Check for disambiguation indicators in the page content
    disambiguation_indicators = [
        "this disambiguation page lists",
        "this page lists articles associated with the title",
        "this is a disambiguation page",
        "this page refers to",
        "this page lists people with the same name",
        "this page lists places with the same name",
        "this page lists topics with the same name",
        "this page lists articles with the same name",
        "topics referred to by the same term",
    ]

    # Check all paragraphs for disambiguation indicators
    paragraphs = soup.find_all("p")
    for para in paragraphs:
        para_text = para.get_text().lower()
        for indicator in disambiguation_indicators:
            if indicator in para_text:
                return True

    # Check for disambiguation template/box
    disambig_templates = soup.find_all("table", class_="ambox-disambig")
    if disambig_templates:
        return True

    # Check for disambiguation box with class dmbox-disambig
    disambig_boxes = soup.find_all("div", class_="dmbox-disambig")
    if disambig_boxes:
        return True

    # Check for disambiguation icon
    disambig_icons = soup.find_all("img", alt="Disambiguation icon")
    if disambig_icons:
        return True

    # Check page categories for disambiguation indicators
    categories = soup.find_all("a", href=lambda x: x and "Category:Disambiguation" in x)
    if categories:
        return True

    return False


def extract_disambiguation_options(html_content):
    """Extract possible options from a disambiguation page"""
    soup = BeautifulSoup(html_content, "html.parser")
    options = []

    # Look for links in the main content area
    main_content = soup.find("div", id="mw-content-text")
    if not main_content:
        return options

    # Find all links that could be disambiguation options
    links = main_content.find_all("a", href=True)

    for link in links:
        href = link.get("href", "")
        text = link.get_text().strip()

        # Skip navigation links, external links, and special pages
        if (
            href.startswith("/wiki/")
            and not href.startswith("/wiki/Special:")
            and not href.startswith("/wiki/Help:")
            and not href.startswith("/wiki/Wikipedia:")
            and not href.startswith("/wiki/File:")
            and not href.startswith("/wiki/Image:")
            and not href.startswith("/wiki/Category:")
            and not href.startswith("/wiki/Template:")
            and not href.startswith("/wiki/User:")
            and not href.startswith("/wiki/Talk:")
            and not href.startswith("/wiki/List_of_")
            and not href.startswith("/wiki/All_pages_")
            and not href.startswith("/wiki/The_")
            and text
            and len(text) > 2
            and len(text) < 100  # Avoid very long text
            and not text.startswith("[")
            and not text.endswith("]")
            and not text.startswith("All pages")
            and not text.startswith("All articles")
            and "(disambiguation)" not in text.lower()
        ):

            # Extract the page title from the href
            page_title = href.replace("/wiki/", "").replace("_", " ")

            # Skip if it's a disambiguation page itself
            if "(disambiguation)" in page_title.lower():
                continue

            # Add to options if not already present
            if page_title not in [opt["title"] for opt in options]:
                options.append({"title": page_title, "display_text": text, "url": href})

    # Return top 10 options
    return options[:10]


def get_wikipedia_content(page_title):
    """Get the HTML content of a Wikipedia page"""
    url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"

    # Custom headers with proper user agent for Wikipedia API
    headers = {
        "User-Agent": (
            "Alexandria-Bib/1.0 "
            "(https://github.com/your-repo/alexandria-bib; your-email@example.com) "
            "Python/3.12"
        )
    }

    try:
        response = requests.get(url, headers=headers)
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
        "h2:-soup-contains('References') + ol li",
        "h2:-soup-contains('Bibliography') + ol li",
        "h2:-soup-contains('Sources') + ol li",
        "h2:-soup-contains('Further Reading') + ol li",
        "h2:-soup-contains('Notes') + ol li",
        "h2:-soup-contains('Citations') + ol li",
        "h2:-soup-contains('Primary Sources') + ol li",
        "h2:-soup-contains('Secondary Sources') + ol li",
        "h3:-soup-contains('References') + ol li",
        "h3:-soup-contains('Bibliography') + ol li",
        "h3:-soup-contains('Sources') + ol li",
        "h3:-soup-contains('Further Reading') + ol li",
        "h3:-soup-contains('Notes') + ol li",
        "h3:-soup-contains('Citations') + ol li",
        "h3:-soup-contains('Primary Sources') + ol li",
        "h3:-soup-contains('Secondary Sources') + ol li",
    ]

    for selector in citation_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text()
            isbn_pattern = r"ISBN[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+"
            isbn_found = re.search(isbn_pattern, text, re.IGNORECASE)
            if isbn_found:
                c = clean_raw_citation(text)
                if c and len(c) > 10:
                    citations.append(c)

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
                            c = clean_raw_citation(text)
                            if c and len(c) > 10:
                                citations.append(c)
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
        citation = citation[: isbn_match.end()].strip()

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


def clean_raw_citation(text):
    """Clean up the raw citation text for extract_book_citations."""
    c = re.sub(r"\s+", " ", text)
    c = c.strip()
    c = re.sub(r"^\^\s*", "", c)
    c = c.strip()
    pattern = r"^[a-z\s]+\s"
    c = re.sub(pattern, "", c)
    c = c.strip()
    c = clean_citation(c)
    return c


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
        # First, check if there's a bracketed year that represents original
        # publication date
        bracket_year_pattern = r"\[c\.\s*(\d{4})"
        bracket_year_match = re.search(bracket_year_pattern, citation, re.IGNORECASE)

        if bracket_year_match:
            # Use the year from the bracketed part (original publication date)
            result["year"] = bracket_year_match.group(1)
        else:
            # Fall back to the first 4-digit year in parentheses
            year_match = re.search(r"\d{4}", date_text)
            if year_match:
                result["year"] = year_match.group(0)

        # Remove any bracketed phrase immediately after the year
        text_after_date = citation[date_end:].strip()
        # Remove leading period or comma
        if text_after_date.startswith("."):
            text_after_date = text_after_date[1:].strip()
        if text_after_date.startswith(","):
            text_after_date = text_after_date[1:].strip()
        # Remove bracketed phrase after year
        bracket_phrase_pattern = r"^\[.*?\]\.?\s*"
        bracket_phrase_match = re.match(bracket_phrase_pattern, text_after_date)
        if bracket_phrase_match:
            text_after_date = text_after_date[bracket_phrase_match.end() :].strip()
        # Skip over additional years in brackets like [1961]
        bracket_year_pattern = r"^\s*\[\d{4}\]\s*\.?\s*"
        bracket_match = re.match(bracket_year_pattern, text_after_date)
        if bracket_match:
            text_after_date = text_after_date[bracket_match.end() :].strip()
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
            "washington",
            "regnery",
            "isbn",
            "retrieved",
            "archived",
            "motilal banarsidass",
            "archana verma",
            "foreign languages press",
            "twenty-first century books",
            "dover",
            "st. martin's press",
            "w. w. norton",
            "univ. press of kentucky",
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
        # Also be smarter about periods in names (like "Ulysses S. Grant")
        stop_patterns = [
            r"\.",
            r"ISBN",
            r" p\.",
            r" pp\.",
            r"\s+retrieved",
            r"\s+archived",
        ]
        stops = []

        # Check for periods, but be smarter about periods in names and
        # publisher detection
        period_matches = list(re.finditer(r"\.", text_after_date))
        for match in period_matches:
            pos = match.start()
            # Count parentheses before this position
            open_parens = text_after_date[:pos].count("(")
            close_parens = text_after_date[:pos].count(")")
            # If we're inside parentheses, skip this stop
            if open_parens > close_parens:
                continue

            # Check if this period is followed by publisher-like content
            text_after_period = text_after_date[pos + 1 :]
            if text_after_period:
                import re as _re

                # Look for publisher patterns (more robust than hardcoded keywords)
                publisher_patterns = [
                    # Location: Publisher pattern (e.g., "New York: Random House",
                    # "Bethesda, MD: American Fisheries Society")
                    r"^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z]{2})?\s*:\s*[A-Z]",
                    # Publisher ending with common words
                    r"^\s*[A-Z][a-zA-Z\s&]+(?:Press|Publishing|University|Books|"
                    r"Publishers|Inc|Ltd|Co|Corp|Society|Bank|Affairs)",
                    # Working paper or report patterns
                    r"^\s*[A-Z][a-zA-Z\s]+(?:Working Paper|Report|Study|Series)",
                    # Simple publisher names (like "Dover", "Twenty-First Century")
                    r"^\s*[A-Z][a-zA-Z\s\-]+(?:Books|Press|Publishing|Publisher|"
                    r"University|College|Institute|Society|Company|Corporation|"
                    r"Inc|Ltd|Co|Corp)",
                    # Specific known publishers (fallback)
                    r"^\s*(?:press|publishing|publisher|university|blackwell|"
                    r"princeton|cambridge|oxford|harvard|yale|penguin|random house|"
                    r"simon & schuster|wiley|springer|elsevier|macmillan|routledge|"
                    r"academic press|london & new york|london|new york|washington|"
                    r"regnery|world bank|fisheries society|publicaffairs|dover|"
                    r"twenty-first century books|motilal banarsidass|archana verma|"
                    r"foreign languages press|st\. martin's press|w\. w\. norton|"
                    r"univ\. press of kentucky)",
                ]

                is_publisher = False
                for pattern in publisher_patterns:
                    if _re.search(pattern, text_after_period, _re.IGNORECASE):
                        stops.append(pos)
                        is_publisher = True
                        break

                if not is_publisher:
                    # Check for initials or capitalized surname (likely part of title)
                    initial_or_surname = _re.match(
                        r"^\s+[A-Z](\.|\b)|^\s+[A-Z][a-z]+", text_after_period
                    )
                    if initial_or_surname:
                        continue  # skip this period, it's part of an initial or surname
                    # Otherwise, if it's a new sentence (capital letter), treat as stop
                    if (
                        text_after_period.strip()
                        and text_after_period.strip()[0].isupper()
                    ):
                        stops.append(pos)

        # Also check for other stop patterns
        for pat in stop_patterns:
            if pat == r"\.":  # Skip periods as we already handled them above
                continue
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
        # Remove bracketed content from title
        title = re.sub(r"\s*\[.*?\]", "", title).strip()
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
            text_after_quote = text_after_date[quote_match.end() :].strip()

            # Clean up text_after_quote for leading commas/whitespace/periods
            text_after_quote = text_after_quote.lstrip(", . ").strip()
            # Look for "in" followed by book authors and "(eds.)"
            in_pattern = r"in\s+([^\(]+\(eds?\.\))[,\.]"
            in_match = re.search(in_pattern, text_after_quote, re.IGNORECASE)

            if in_match:
                book_authors = in_match.group(1).strip()
                result["book_authors"] = book_authors
                # Get text after the "in... (eds.)," or "." part
                text_after_in = text_after_quote[in_match.end() :].strip()

                # Extract book title (everything up to the next period or comma)
                # Look for the first period or comma that's not inside parentheses
                stop_index = -1
                paren_count = 0

                for i, char in enumerate(text_after_in):
                    if char == "(":
                        paren_count += 1
                    elif char == ")":
                        paren_count -= 1
                    elif paren_count == 0 and (char == "." or char == ","):
                        stop_index = i
                        break

                if stop_index != -1:
                    book_title = text_after_in[:stop_index].strip()
                    result["book_title"] = book_title
                    result["remaining_text"] = text_after_in[stop_index + 1 :].strip()
                else:
                    # If no clear stop found, take the first word/phrase
                    # This handles cases where the book title is a single word
                    words = text_after_in.split()
                    if words:
                        result["book_title"] = words[0]
                        result["remaining_text"] = " ".join(words[1:])
                    else:
                        result["book_title"] = text_after_in
                        result["remaining_text"] = ""
            else:
                # No "in ... (eds.)" pattern found, try to extract book title directly
                # Look for patterns like "Book Title. Vol. X" or "Book Title. Publisher"
                # First, try to find a period followed by "Vol." or publisher keywords
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
                    "washington",
                    "regnery",
                    "isbn",
                    "retrieved",
                    "archived",
                ]

                # Look for "Vol." pattern first
                vol_pattern = r"\.\s*Vol\.\s*\d+"
                vol_match = re.search(vol_pattern, text_after_quote, re.IGNORECASE)

                if vol_match:
                    # Extract everything up to and including "Vol. X"
                    vol_end = vol_match.end()
                    book_title = text_after_quote[:vol_end].strip()
                    result["book_title"] = book_title
                    result["remaining_text"] = text_after_quote[vol_end:].strip()
                else:
                    # Look for publisher keywords after a period
                    stop_index = -1
                    for keyword in publisher_keywords:
                        pattern = rf"\.\s*{re.escape(keyword)}"
                        match = re.search(pattern, text_after_quote, re.IGNORECASE)
                        if match:
                            stop_index = match.start()
                            break

                    if stop_index != -1:
                        book_title = text_after_quote[:stop_index].strip()
                        result["book_title"] = book_title
                        result["remaining_text"] = text_after_quote[stop_index:].strip()
                    else:
                        # Fallback: take everything up to the first period
                        period_index = text_after_quote.find(".")
                        if period_index != -1:
                            book_title = text_after_quote[:period_index].strip()
                            result["book_title"] = book_title
                            result["remaining_text"] = text_after_quote[
                                period_index + 1 :
                            ].strip()
                        else:
                            result["remaining_text"] = text_after_quote
                # If we found a book_title but no book_authors, set book_authors
                # to chapter_authors
                if result["book_title"] and not result["book_authors"]:
                    result["book_authors"] = result["chapter_authors"]
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
            result["remaining_text"] = citation[year_end : by_match.start()].strip()
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
                remaining = after_year[last_period + 1 :].strip()
            else:
                # fallback: up to the last period
                period_idx = after_year.rfind(".")
                if period_idx != -1:
                    title = after_year[:period_idx].strip()
                    remaining = after_year[period_idx + 1 :].strip()
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
                rest = citation[first_ed.end() : title_end].lstrip(", ")
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


def type_5_parser(citation):
    """
    Parse Type V citations that have editors in parentheses.
    Extracts authors, year, editor, title, and ISBN from the citation.

    Format: Authors (year). Editor (ed.). Title. Publisher. ISBN.

    Args:
        citation (str): A citation string that contains editor information

    Returns:
        dict: Parsed citation data with authors, year, editor, title, isbn, and
        remaining_text fields
    """
    if not citation:
        return {
            "authors": None,
            "year": None,
            "editor": None,
            "title": None,
            "isbn": None,
            "remaining_text": citation,
        }

    # Initialize result
    result = {
        "authors": None,
        "year": None,
        "editor": None,
        "title": None,
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

        # Extract authors from everything before the parentheses
        authors = citation[:date_start].strip()
        result["authors"] = authors

        # Extract just the year (4 digits)
        year_match = re.search(r"\d{4}", date_text)
        if year_match:
            result["year"] = year_match.group(0)

        # Extract text after the date
        text_after_date = citation[date_end:].strip()
        if text_after_date.startswith("."):
            text_after_date = text_after_date[1:].strip()

        # Look for editor pattern: Name (ed.)
        editor_pattern = r"([^\(]+)\s*\(ed\.\)"
        editor_match = re.search(editor_pattern, text_after_date, re.IGNORECASE)

        if editor_match:
            editor = editor_match.group(1).strip()
            result["editor"] = editor

            # Get text after the editor
            text_after_editor = text_after_date[editor_match.end() :].strip()

            # Clean up leading punctuation
            text_after_editor = re.sub(r"^[\.,\s]+", "", text_after_editor)

            # Extract title (everything up to the next period or publisher keywords)
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
                "facts on file",
                "isbn",
                "retrieved",
                "archived",
            ]

            # Find the next period or publisher keyword
            stop_patterns = [r"\."] + [
                rf"\b{re.escape(kw)}\b" for kw in publisher_keywords
            ]
            stops = []

            for pattern in stop_patterns:
                matches = list(re.finditer(pattern, text_after_editor, re.IGNORECASE))
                for match in matches:
                    pos = match.start()
                    # Count parentheses before this position
                    open_parens = text_after_editor[:pos].count("(")
                    close_parens = text_after_editor[:pos].count(")")
                    # If we're inside parentheses, skip this stop
                    if open_parens > close_parens:
                        continue
                    stops.append(pos)

            if stops:
                stop_index = min(stops)
                title = text_after_editor[:stop_index].strip()
                result["title"] = title
                result["remaining_text"] = text_after_editor[stop_index:].strip()
            else:
                result["title"] = text_after_editor.strip()
                result["remaining_text"] = ""
        else:
            # No editor found, treat as regular citation
            result["remaining_text"] = text_after_date

    # Extract ISBN
    isbn_pattern = r"ISBN\s+([0-9\-]+)"
    isbn_match = re.search(isbn_pattern, result["remaining_text"], re.IGNORECASE)

    if isbn_match:
        result["isbn"] = isbn_match.group(1)
        # Remove the entire ISBN from the remaining text
        isbn_full = isbn_match.group(0)
        result["remaining_text"] = (
            result["remaining_text"].replace(isbn_full, "").strip()
        )

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
            text_after_in = text_after_quote[in_match.end() :].strip()
            # Extract book title (everything up to the next comma, or period
            # if no comma)
            comma_index = text_after_in.find(",")
            if comma_index != -1:
                book_title = text_after_in[:comma_index].strip()
                result["book_title"] = book_title
                result["remaining_text"] = text_after_in[comma_index + 1 :].strip()
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
                        len(book_title_match.group(0)) :
                    ].strip()
                else:
                    next_period_index = text_after_in.find(".")
                    if next_period_index != -1:
                        book_title = text_after_in[:next_period_index].strip()
                        result["book_title"] = book_title
                        result["remaining_text"] = text_after_in[
                            next_period_index + 1 :
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


def determine_parser_type(citation):
    # Check for chapter citations (has quoted chapter titles)
    if '"' in citation or (
        "'" in citation and re.search(r"['\"][^'\"]*['\"]\\s*(?:in|In|\\.)", citation)
    ):
        return "type3"
    # Check for editor citations (contains "(ed.)" or "(eds.)")
    if "(ed." in citation or "(eds." in citation:
        return "type5"
    # Check for parenthetical dates (Type 1) - look for year in parentheses
    if re.search(r"\([^)]*\d{4}[^)]*\)", citation):
        return "type1"
    # Check for standalone years (Type 2)
    if re.search(r"\b(19|20)\d{2}\b", citation) and "(" not in citation:
        return "type2"
    # Default to Type 1 for unknown formats
    return "type1"


@app.route("/api/parse/batch", methods=["POST"])
@limiter.limit("150 per minute")
def parse_batch():
    """Parse multiple citations in a single request"""
    data = request.get_json()
    citations = data.get("citations", [])
    results = []
    for citation in citations:
        parser_type = determine_parser_type(citation)
        if parser_type == "type1":
            parsed = type_1_parser(citation)
        elif parser_type == "type2":
            parsed = type_2_parser(citation)
        elif parser_type == "type3":
            parsed = type_3_parser(citation)
        elif parser_type == "type4":
            parsed = type_4_parser(citation)
        elif parser_type == "type5":
            parsed = type_5_parser(citation)
        else:
            parsed = type_1_parser(citation)
        results.append(parsed)
    return jsonify({"results": results})


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


@app.route("/api/cache/clear", methods=["POST"])
def clear_cache():
    """Clear all cached results"""
    try:
        # Get all keys with the alexandria prefix
        keys = redis_client.keys("alexandria:*")
        if keys:
            redis_client.delete(*keys)
            return jsonify(
                {"message": f"Cleared {len(keys)} cached items", "status": "success"}
            )
        else:
            return jsonify({"message": "No cached items found", "status": "success"})
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return jsonify({"error": "Failed to clear cache", "status": "error"}), 500


@app.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    """Get cache statistics"""
    try:
        # Get all keys with the alexandria prefix
        keys = redis_client.keys("alexandria:*")
        search_keys = redis_client.keys("alexandria:search:*")
        page_keys = redis_client.keys("alexandria:page:*")

        return jsonify(
            {
                "total_cached_items": len(keys),
                "search_cached_items": len(search_keys),
                "page_cached_items": len(page_keys),
                "status": "success",
            }
        )
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return jsonify({"error": "Failed to get cache stats", "status": "error"}), 500


@app.route("/api/user-agent/info", methods=["GET"])
def user_agent_info():
    """Get information about the current request's user agent"""
    user_agent = request.headers.get("User-Agent", "Unknown")
    ip_address = request.remote_addr

    # Basic user agent parsing
    ua_info = {
        "user_agent": user_agent,
        "ip_address": ip_address,
        "endpoint": request.endpoint,
        "method": request.method,
    }

    # Try to extract browser/OS info from user agent
    ua_lower = user_agent.lower()

    # Browser detection
    if "chrome" in ua_lower:
        ua_info["browser"] = "Chrome"
    elif "firefox" in ua_lower:
        ua_info["browser"] = "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        ua_info["browser"] = "Safari"
    elif "edge" in ua_lower:
        ua_info["browser"] = "Edge"
    elif "opera" in ua_lower:
        ua_info["browser"] = "Opera"
    else:
        ua_info["browser"] = "Unknown"

    # OS detection
    if "windows" in ua_lower:
        ua_info["os"] = "Windows"
    elif "mac" in ua_lower:
        ua_info["os"] = "macOS"
    elif "linux" in ua_lower:
        ua_info["os"] = "Linux"
    elif "android" in ua_lower:
        ua_info["os"] = "Android"
    elif "ios" in ua_lower:
        ua_info["os"] = "iOS"
    else:
        ua_info["os"] = "Unknown"

    # Check if it's a bot/crawler
    bot_indicators = ["bot", "crawler", "spider", "scraper", "curl", "wget", "python"]
    ua_info["is_bot"] = any(indicator in ua_lower for indicator in bot_indicators)

    return jsonify(ua_info)


@app.route("/api/search", methods=["POST"])
@limiter.limit("150 per minute")
def search_books():
    """Search for books based on a topic using Wikipedia"""
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query is required", "status": "error"}), 400

        cache_key = get_cache_key(query)
        cached_result = get_cached_result(cache_key)

        if cached_result:
            print(f"Serving cached result for query: {query}")
            return jsonify(cached_result)

        search_results = search_wikipedia(query)

        # If no search results, check for "did you mean" suggestions
        if not search_results:
            suggestions = search_wikipedia_with_suggestions(query)
            if suggestions:
                # Convert suggestions to the same format as disambiguation options
                suggestion_options = []
                for suggestion in suggestions[:5]:  # Top 5 suggestions
                    suggestion_options.append(
                        {
                            "title": suggestion,
                            "display_text": suggestion,
                            "url": f'/wiki/{suggestion.replace(" ", "_")}',
                        }
                    )

                set_cached_result(
                    cache_key,
                    {
                        "query": query,
                        "page_title": None,
                        "suggestions": True,
                        "options": suggestion_options,
                        "status": "suggestions",
                    },
                )

                return jsonify(
                    {
                        "query": query,
                        "page_title": None,
                        "suggestions": True,
                        "options": suggestion_options,
                        "status": "suggestions",
                    }
                )
            else:
                set_cached_result(
                    cache_key,
                    {
                        "error": f'No Wikipedia page found for "{query}"',
                        "status": "error",
                    },
                )
                return (
                    jsonify(
                        {
                            "error": f'No Wikipedia page found for "{query}"',
                            "status": "error",
                        }
                    ),
                    404,
                )

        # Get the best match (first result)
        best_match = search_results[0]["title"]
        html_content = get_wikipedia_content(best_match)

        if not html_content:
            set_cached_result(
                cache_key,
                {
                    "error": f'Could not fetch content for "{best_match}"',
                    "status": "error",
                },
            )
            return (
                jsonify(
                    {
                        "error": f'Could not fetch content for "{best_match}"',
                        "status": "error",
                    }
                ),
                500,
            )

        # Check if this is a disambiguation page
        if is_disambiguation_page(html_content):
            disambiguation_options = extract_disambiguation_options(html_content)
            set_cached_result(
                cache_key,
                {
                    "query": query,
                    "page_title": best_match,
                    "disambiguation": True,
                    "options": disambiguation_options,
                    "status": "disambiguation",
                },
            )
            return jsonify(
                {
                    "query": query,
                    "page_title": best_match,
                    "disambiguation": True,
                    "options": disambiguation_options,
                    "status": "disambiguation",
                }
            )

        # Regular page - extract citations
        citations = extract_book_citations(html_content)
        set_cached_result(
            cache_key,
            {
                "query": query,
                "page_title": best_match,
                "citations": citations,
                "count": len(citations),
                "status": "success",
            },
        )
        return jsonify(
            {
                "query": query,
                "page_title": best_match,
                "citations": citations,
                "count": len(citations),
                "status": "success",
            }
        )
    except Exception as e:
        print(f"Error in search_books: {e}")
        return jsonify({"error": "Internal server error", "status": "error"}), 500


@app.route("/api/search/page", methods=["POST"])
@limiter.limit("150 per minute")
def search_specific_page():
    """Search for books on a specific Wikipedia page"""
    try:
        data = request.get_json()
        page_title = data.get("page_title", "").strip()
        if not page_title:
            return jsonify({"error": "Page title is required", "status": "error"}), 400

        # Check cache first
        cache_key = get_cache_key(page_title, "page")
        cached_result = get_cached_result(cache_key)

        if cached_result:
            print(f"Serving cached result for page: {page_title}")
            return jsonify(cached_result)

        html_content = get_wikipedia_content(page_title)
        if not html_content:
            set_cached_result(
                cache_key,
                {
                    "error": f'Could not fetch content for "{page_title}"',
                    "status": "error",
                },
            )
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
        result = {
            "page_title": page_title,
            "citations": citations,
            "count": len(citations),
            "status": "success",
        }

        # Cache the result
        set_cached_result(cache_key, result)

        return jsonify(result)
    except Exception as e:
        print(f"Error in search_specific_page: {e}")
        return jsonify({"error": "Internal server error", "status": "error"}), 500


@app.route("/api/parse/type1", methods=["POST"])
@limiter.limit("150 per minute")
def parse_type1():
    """Parse Type I citations using the type_1_parser function"""
    try:
        data = request.get_json()
        citation = data.get("citation", "").strip()
        if not citation:
            return jsonify({"error": "Citation is required", "status": "error"}), 400

        result = type_1_parser(citation)
        return jsonify(result)
    except Exception as e:
        print(f"Error in parse_type1: {e}")
        return jsonify({"error": "Internal server error", "status": "error"}), 500


@app.route("/api/parse/type2", methods=["POST"])
@limiter.limit("150 per minute")
def parse_type2():
    """Parse Type II citations using the type_2_parser function"""
    try:
        data = request.get_json()
        citation = data.get("citation", "").strip()
        if not citation:
            return jsonify({"error": "Citation is required", "status": "error"}), 400

        result = type_2_parser(citation)
        return jsonify(result)
    except Exception as e:
        print(f"Error in parse_type2: {e}")
        return jsonify({"error": "Internal server error", "status": "error"}), 500


@app.route("/api/parse/type3", methods=["POST"])
@limiter.limit("150 per minute")
def parse_type3():
    """Parse Type III citations using the type_3_parser function"""
    try:
        data = request.get_json()
        citation = data.get("citation", "").strip()
        if not citation:
            return jsonify({"error": "Citation is required", "status": "error"}), 400

        result = type_3_parser(citation)
        return jsonify(result)
    except Exception as e:
        print(f"Error in parse_type3: {e}")
        return jsonify({"error": "Internal server error", "status": "error"}), 500


@app.route("/api/parse/type5", methods=["POST"])
@limiter.limit("150 per minute")
def parse_type5():
    """Parse Type V citations using the type_5_parser function"""
    try:
        data = request.get_json()
        citation = data.get("citation", "").strip()
        if not citation:
            return jsonify({"error": "Citation is required", "status": "error"}), 400

        result = type_5_parser(citation)
        return jsonify(result)
    except Exception as e:
        print(f"Error in parse_type5: {e}")
        return jsonify({"error": "Internal server error", "status": "error"}), 500


@limiter.request_filter
def ip_whitelist():
    """Allow health check endpoint to bypass rate limiting"""
    return request.endpoint == "health_check"


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    return (
        jsonify(
            {
                "error": "Rate limit exceeded. Please try again later.",
                "status": "error",
                "retry_after": e.retry_after if hasattr(e, "retry_after") else 60,
            }
        ),
        429,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)


# --- Graceful Degradation Implementation ---
# This code runs after all routes are defined to wrap them with graceful degradation


def wrap_with_graceful_degradation():
    """Wrap search endpoints with graceful degradation"""
    if "search_books" in app.view_functions:
        old_search_books = app.view_functions["search_books"]

        def search_books_graceful():
            # Only return 503 if there's actual high load, not just Redis unavailability
            # For now, let the original function handle Redis unavailability gracefully
            return old_search_books()

        app.view_functions["search_books"] = search_books_graceful

    if "search_specific_page" in app.view_functions:
        old_search_specific_page = app.view_functions["search_specific_page"]

        def search_specific_page_graceful():
            # Only return 503 if there's actual high load, not just Redis unavailability
            # For now, let the original function handle Redis unavailability gracefully
            return old_search_specific_page()

        app.view_functions["search_specific_page"] = search_specific_page_graceful


# Apply graceful degradation wrapping
wrap_with_graceful_degradation()
