import unittest
import json
import sys
import os

# Add the current directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from app import clean_citation


class TestBearsSearch(unittest.TestCase):
    """Test searching for 'Bears' and verifying book citations"""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_bears_search(self):
        """Test searching for 'Bears' and verifying expected book citations"""
        expected_citations = [
            "Brunner, Bernd (2007). Bears: A Brief History. Yale University Press. ISBN 978-0-300-12299-2",
            "Domico, Terry; Newman, Mark (1988). Bears of the World. Facts on File. ISBN 978-0-8160-1536-8",
            "Faulkner, William (1942). The Bear. Curley Publishing. ISBN 978-0-7927-0537-6."
        ]
        
        # Test the API call
        response = self.app.post('/api/search', 
                               data=json.dumps({'query': 'Bears'}),
                               content_type='application/json')
        data = json.loads(response.data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['query'], 'Bears')
        self.assertIsNotNone(data['page_title'])
        self.assertGreater(len(data['citations']), 0)
        
        # Check that at least some of the expected citations are present
        found_citations = 0
        for expected_citation in expected_citations:
            if any(expected_citation in citation for citation in data['citations']):
                found_citations += 1
        
        self.assertGreater(found_citations, 0, f"Expected to find at least one citation from {expected_citations}")

    def test_citation_structure(self):
        """Test that citations are returned as strings"""
        response = self.app.post('/api/search', 
                               data=json.dumps({'query': 'Bears'}),
                               content_type='application/json')
        data = json.loads(response.data)
        
        if data['citations']:
            citation = data['citations'][0]
            # Citations should be strings, not dictionaries
            self.assertIsInstance(citation, str)
            self.assertGreater(len(citation), 10)  # Should have meaningful content


class TestType1Parser(unittest.TestCase):
    """Test the type_1_parser function"""

    def setUp(self):
        # Import the function to test
        from app import type_1_parser
        self.parser = type_1_parser

    def test_type_1_parser_exists(self):
        """Test that the type_1_parser function exists and is callable"""
        self.assertTrue(callable(self.parser))

    def test_type_1_parser_returns_dict(self):
        """Test that type_1_parser returns a dictionary"""
        test_citation = "Butler, Susan (2009). The Dinkum Dictionary: The Origins of Australian Words. Text Publishing. p. 266. ISBN 978-1-921799-10-5"
        result = self.parser(test_citation)
        self.assertIsInstance(result, dict)

    def test_type_1_parser_empty_input(self):
        """Test that type_1_parser handles empty input"""
        result = self.parser("")
        self.assertEqual(result, {"authors": None, "year": None, "title": None, "isbn": None, "remaining_text": ""})

    def test_type_1_parser_none_input(self):
        """Test that type_1_parser handles None input"""
        result = self.parser(None)
        self.assertEqual(result, {"authors": None, "year": None, "title": None, "isbn": None, "remaining_text": ""})

    def test_type_1_parser_extract_year_simple(self):
        """Test that type_1_parser extracts year from simple format (2003)"""
        test_citation = "Butler, Susan (2009). The Dinkum Dictionary: The Origins of Australian Words. Text Publishing. p. 266. ISBN 978-1-921799-10-5."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Butler, Susan")
        self.assertEqual(result["year"], "2009")
        self.assertEqual(result["title"], "The Dinkum Dictionary: The Origins of Australian Words")
        self.assertEqual(result["isbn"], "978-1-921799-10-5")
        # Check that authors, title, parentheses and ISBN are removed from remaining text
        self.assertNotIn("Butler, Susan", result["remaining_text"])
        self.assertNotIn("The Dinkum Dictionary", result["remaining_text"])
        self.assertNotIn("(2009)", result["remaining_text"])
        self.assertNotIn("ISBN", result["remaining_text"])
    
    def test_type_1_parser_extract_year_simple(self):
        """Test that type_1_parser extracts year from simple format (2003)"""
        test_citation = "Margulis, Sergio (2004). Causes of Deforestation of the Brazilian Amazon (PDF). World Bank Working Paper No. 22. Washington, DC: The World Bank. ISBN 978-0-8213-5691-3. Archived (PDF) from the original on September 10, 2008. Retrieved September 4, 2008."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Margulis, Sergio")
        self.assertEqual(result["year"], "2004")
        self.assertEqual(result["title"], "Causes of Deforestation of the Brazilian Amazon")
        self.assertEqual(result["isbn"], "978-0-8213-5691-3")
        # Check that authors, title, parentheses and ISBN are removed from remaining text
        self.assertNotIn("Ashton, Sally-Ann", result["remaining_text"])
        self.assertNotIn("Cleopatra and Egypt", result["remaining_text"])
        self.assertNotIn("(2008)", result["remaining_text"])
        self.assertNotIn("ISBN", result["remaining_text"])
    
    def test_type_1_parser_extract_year_simple(self):
        """Test that type_1_parser extracts year from simple format (2003)"""
        test_citation = "Ashton, Sally-Ann (2008), Cleopatra and Egypt, Blackwell, ISBN 978-1-4051-1390-8, retrieved 18 June 2020."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Ashton, Sally-Ann")
        self.assertEqual(result["year"], "2008")
        self.assertEqual(result["title"], "Cleopatra and Egypt")
        self.assertEqual(result["isbn"], "978-1-4051-1390-8")
        # Check that authors, title, parentheses and ISBN are removed from remaining text
        self.assertNotIn("Ashton, Sally-Ann", result["remaining_text"])
        self.assertNotIn("Cleopatra and Egypt", result["remaining_text"])
        self.assertNotIn("(2008)", result["remaining_text"])
        self.assertNotIn("ISBN", result["remaining_text"])
    
    def test_type_1_parser_extract_year_simple(self):
        """Test that type_1_parser extracts year from simple format (2003)"""
        test_citation = "Prose, Francine (2022). Cleopatra: Her History, Her Myth. Yale University Press. ISBN 978-0-300-25938-4."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Prose, Francine")
        self.assertEqual(result["year"], "2022")
        self.assertEqual(result["title"], "Cleopatra: Her History, Her Myth")
        self.assertEqual(result["isbn"], "978-0-300-25938-4")
        # Check that authors, title, parentheses and ISBN are removed from remaining text
        self.assertNotIn("Prose, Francine", result["remaining_text"])
        self.assertNotIn("Cleopatra: Her History, Her Myth", result["remaining_text"])
        self.assertNotIn("(2022)", result["remaining_text"])
        self.assertNotIn("ISBN", result["remaining_text"])

    def test_type_1_parser_extract_year_complex(self):
        """Test that type_1_parser extracts year from complex format (January 5, 1980)"""
        test_citation = "Vogelnest, Larry; Woods, Rupert (18 August 2008). Medicine of Australian Mammals. Csiro Publishing. ISBN 978-0-643-09797-1."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Vogelnest, Larry; Woods, Rupert")
        self.assertEqual(result["year"], "2008")
        self.assertEqual(result["title"], "Medicine of Australian Mammals")
        self.assertEqual(result["isbn"], "978-0-643-09797-1")
        # Check that authors, title, parentheses and ISBN are removed from remaining text
        self.assertNotIn("Vogelnest, Larry; Woods, Rupert", result["remaining_text"])
        self.assertNotIn("Medicine of Australian Mammals", result["remaining_text"])
        self.assertNotIn("(18 August 2008)", result["remaining_text"])
        self.assertNotIn("ISBN", result["remaining_text"])

    def test_type_1_parser_extract_year_month_only(self):
        """Test that type_1_parser extracts year from month-year format (December 2020)"""
        test_citation = "Johnson, Bob (December 2020). Third Book. Publisher. p. 789. ISBN 1-234-56789-0."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Johnson, Bob")
        self.assertEqual(result["year"], "2020")
        self.assertEqual(result["title"], "Third Book")
        self.assertEqual(result["isbn"], "1-234-56789-0")

    def test_type_1_parser_no_year(self):
        """Test that type_1_parser handles citations without year"""
        test_citation = "Smith, John. My Book Title. Publisher Name. p. 123. ISBN 0-123-45678-9"
        result = self.parser(test_citation)
        self.assertIsNone(result["authors"])
        self.assertIsNone(result["year"])
        self.assertIsNone(result["title"])
        self.assertEqual(result["isbn"], "0-123-45678-9")

    def test_type_1_parser_remaining_text_clean(self):
        """Test that the remaining text is clean after extraction"""
        test_citation = "Butler, Susan (2009). The Dinkum Dictionary: The Origins of Australian Words. Text Publishing. p. 266. ISBN 978-1-921799-10-5"
        result = self.parser(test_citation)
        expected_remaining = "Text Publishing. p. 266."
        self.assertEqual(result["remaining_text"], expected_remaining)

    def test_type_1_parser_remove_comma_after_parentheses(self):
        """Test that type_1_parser removes comma after parentheses"""
        test_citation = "Smith, John (2020), My Book Title. Publisher Name. p. 123. ISBN 0-123-45678-9"
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Smith, John")
        self.assertEqual(result["year"], "2020")
        self.assertEqual(result["title"], "My Book Title")
        self.assertEqual(result["isbn"], "0-123-45678-9")
        # Check that the comma after parentheses is removed
        self.assertNotIn("(2020),", result["remaining_text"])
        self.assertNotIn("My Book Title", result["remaining_text"])


class TestCitationCleaning(unittest.TestCase):
    """Test cases for citation cleaning functionality"""
    
    def test_remove_after_isbn(self):
        """Test removing everything after ISBN number"""
        citation = "Taylor, Isaac (1898). Names and Their Histories: A Handbook of Historical Geography and Topographical Nomenclature. London: Rivingtons. ISBN 978-0-559-29668-0. Archived from the original on July 25, 2020. Retrieved October 12, 2008. {{cite book}}: ISBN / Date incompatibility (help)"
        expected = "Taylor, Isaac (1898). Names and Their Histories: A Handbook of Historical Geography and Topographical Nomenclature. London: Rivingtons. ISBN 978-0-559-29668-0"
        result = clean_citation(citation)
        self.assertEqual(result, expected)
    
    def test_remove_page_numbers_pp(self):
        """Test removing page numbers with pp. format"""
        citation = "Smith, John (2000). Book Title. Publisher. ISBN 123-4-567-89012-3. pp. 139–141."
        expected = "Smith, John (2000). Book Title. Publisher. ISBN 123-4-567-89012-3"
        result = clean_citation(citation)
        self.assertEqual(result, expected)
    
    def test_remove_page_numbers_p(self):
        """Test removing page numbers with p. format"""
        citation = "Doe, Jane (1995). Another Book. Publisher. ISBN 987-6-543-21098-7. p. 251."
        expected = "Doe, Jane (1995). Another Book. Publisher. ISBN 987-6-543-21098-7"
        result = clean_citation(citation)
        self.assertEqual(result, expected)
    
    def test_remove_pdf_from_title(self):
        """Test removing (PDF) from book titles"""
        citation = "Author, Name (2010). Book Title (PDF). Publisher. ISBN 111-2-333-44444-5"
        expected = "Author, Name (2010). Book Title. Publisher. ISBN 111-2-333-44444-5"
        result = clean_citation(citation)
        self.assertEqual(result, expected)
    
    def test_combined_cleaning(self):
        """Test all cleaning rules applied together"""
        citation = "Author, Name (2010). Book Title (PDF). Publisher. ISBN 111-2-333-44444-5. pp. 139–141. Archived from original."
        expected = "Author, Name (2010). Book Title. Publisher. ISBN 111-2-333-44444-5"
        result = clean_citation(citation)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main() 