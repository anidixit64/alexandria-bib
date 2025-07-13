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
                citation = re.sub(r"^[a-z\s]+\s", "", citation).strip()
                
                # Ensure we have a meaningful citation
                if citation and len(citation) > 10:
                    citations.append(citation)
    
    # Also look for citations in specific sections by finding headers and their content
    section_headers = [
        "References", "Bibliography", "Sources", "Further Reading", 
        "Notes", "Citations", "Primary Sources", "Secondary Sources"
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
                        isbn_pattern = r"ISBN[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+[-\s]?\d+"
                        if re.search(isbn_pattern, text, re.IGNORECASE):
                            citation = re.sub(r"\s+", " ", text).strip()
                            citation = re.sub(r"^\^\s*", "", citation).strip()
                            citation = re.sub(r"^[a-z\s]+\s", "", citation).strip()
                            
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
    
    return unique_citations


@app.route("/")
def home():
    return jsonify({"message": "Alexandria API is running", "status": "success"})


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
