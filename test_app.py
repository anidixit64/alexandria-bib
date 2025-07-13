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
    """Test the type_1_parser function for standard citations with parenthetical dates"""

    def setUp(self):
        from app import type_1_parser
        self.parser = type_1_parser

    def test_parser_exists(self):
        """Test that the type_1_parser function exists and is callable"""
        self.assertTrue(callable(self.parser))

    def test_parser_returns_dict(self):
        """Test that type_1_parser returns a dictionary"""
        test_citation = "Butler, Susan (2009). The Dinkum Dictionary: The Origins of Australian Words. Text Publishing. p. 266. ISBN 978-1-921799-10-5"
        result = self.parser(test_citation)
        self.assertIsInstance(result, dict)

    def test_empty_input(self):
        """Test that type_1_parser handles empty input"""
        result = self.parser("")
        self.assertEqual(result, {"authors": None, "year": None, "title": None, "isbn": None, "remaining_text": ""})

    def test_none_input(self):
        """Test that type_1_parser handles None input"""
        result = self.parser(None)
        self.assertEqual(result, {"authors": None, "year": None, "title": None, "isbn": None, "remaining_text": ""})

    def test_extract_year_simple(self):
        """Test that type_1_parser extracts year from simple format (2009)"""
        test_citation = "Butler, Susan (2009). The Dinkum Dictionary: The Origins of Australian Words. Text Publishing. p. 266. ISBN 978-1-921799-10-5."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Butler, Susan")
        self.assertEqual(result["year"], "2009")
        self.assertEqual(result["title"], "The Dinkum Dictionary: The Origins of Australian Words")
        self.assertEqual(result["isbn"], "978-1-921799-10-5")
        # Check that extracted parts are removed from remaining text
        self.assertNotIn("Butler, Susan", result["remaining_text"])
        self.assertNotIn("The Dinkum Dictionary", result["remaining_text"])
        self.assertNotIn("(2009)", result["remaining_text"])
        self.assertNotIn("ISBN", result["remaining_text"])
    
    def test_extract_year_with_pdf(self):
        """Test that type_1_parser removes (PDF) from title"""
        test_citation = "Margulis, Sergio (2004). Causes of Deforestation of the Brazilian Amazon (PDF). World Bank Working Paper No. 22. Washington, DC: The World Bank. ISBN 978-0-8213-5691-3."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Margulis, Sergio")
        self.assertEqual(result["year"], "2004")
        self.assertEqual(result["title"], "Causes of Deforestation of the Brazilian Amazon")
        self.assertEqual(result["isbn"], "978-0-8213-5691-3")

    def test_extract_year_complex_date(self):
        """Test that type_1_parser extracts year from complex date format (18 August 2008)"""
        test_citation = "Vogelnest, Larry; Woods, Rupert (18 August 2008). Medicine of Australian Mammals. Csiro Publishing. ISBN 978-0-643-09797-1."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Vogelnest, Larry; Woods, Rupert")
        self.assertEqual(result["year"], "2008")
        self.assertEqual(result["title"], "Medicine of Australian Mammals")
        self.assertEqual(result["isbn"], "978-0-643-09797-1")

    def test_extract_year_month_only(self):
        """Test that type_1_parser extracts year from month-year format (December 2020)"""
        test_citation = "Johnson, Bob (December 2020). Third Book. Publisher. p. 789. ISBN 1-234-56789-0."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Johnson, Bob")
        self.assertEqual(result["year"], "2020")
        self.assertEqual(result["title"], "Third Book")
        self.assertEqual(result["isbn"], "1-234-56789-0")

    def test_no_year(self):
        """Test that type_1_parser handles citations without year"""
        test_citation = "Smith, John. My Book Title. Publisher Name. p. 123. ISBN 0-123-45678-9"
        result = self.parser(test_citation)
        self.assertIsNone(result["authors"])
        self.assertIsNone(result["year"])
        self.assertIsNone(result["title"])
        self.assertEqual(result["isbn"], "0-123-45678-9")

    def test_remaining_text_clean(self):
        """Test that the remaining text is clean after extraction"""
        test_citation = "Butler, Susan (2009). The Dinkum Dictionary: The Origins of Australian Words. Text Publishing. p. 266. ISBN 978-1-921799-10-5"
        result = self.parser(test_citation)
        expected_remaining = "Text Publishing. p. 266."
        self.assertEqual(result["remaining_text"], expected_remaining)

    def test_remove_comma_after_parentheses(self):
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

    def test_publisher_with_comma(self):
        """Test that type_1_parser stops title at publisher when comma is present"""
        test_citation = "Ashton, Sally-Ann (2008), Cleopatra and Egypt, Blackwell, ISBN 978-1-4051-1390-8, retrieved 18 June 2020."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Ashton, Sally-Ann")
        self.assertEqual(result["year"], "2008")
        self.assertEqual(result["title"], "Cleopatra and Egypt")
        self.assertEqual(result["isbn"], "978-1-4051-1390-8")

    def test_title_with_colon(self):
        """Test that type_1_parser handles titles with colons"""
        test_citation = "Prose, Francine (2022). Cleopatra: Her History, Her Myth. Yale University Press. ISBN 978-0-300-25938-4."
        result = self.parser(test_citation)
        self.assertEqual(result["authors"], "Prose, Francine")
        self.assertEqual(result["year"], "2022")
        self.assertEqual(result["title"], "Cleopatra: Her History, Her Myth")
        self.assertEqual(result["isbn"], "978-0-300-25938-4")

    # New tests for the specified citations
    def test_brosius_persians_citation(self):
        """Test parsing Brosius citation with location and publisher"""
        test_citation = "Brosius, Maria (2006), The Persians: An Introduction, London & New York: Routledge, ISBN 978-0-415-32089-4"
        result = self.parser(test_citation)
        print(f"DEBUG Brosius: {result}")  # Debug print
        self.assertEqual(result["authors"], "Brosius, Maria")
        self.assertEqual(result["year"], "2006")
        self.assertEqual(result["title"], "The Persians: An Introduction")
        self.assertEqual(result["isbn"], "978-0-415-32089-4")

    def test_sigurdsson_encyclopedia_citation(self):
        """Test parsing Sigurðsson citation with editor and edition"""
        test_citation = "Sigurðsson, Haraldur, ed. (2015). The Encyclopedia of Volcanoes (2 ed.). Academic Press. ISBN 978-0-12-385938-9"
        result = self.parser(test_citation)
        print(f"DEBUG Sigurðsson: {result}")  # Debug print
        self.assertEqual(result["authors"], "Sigurðsson, Haraldur, ed.")
        self.assertEqual(result["year"], "2015")
        self.assertEqual(result["title"], "The Encyclopedia of Volcanoes (2 ed.)")
        self.assertEqual(result["isbn"], "978-0-12-385938-9")


class TestType3Parser(unittest.TestCase):
    """Test the type_3_parser function for citations with quoted chapter titles"""

    def setUp(self):
        from app import type_3_parser
        self.parser = type_3_parser

    def test_parser_exists(self):
        """Test that the type_3_parser function exists and is callable"""
        self.assertTrue(callable(self.parser))

    def test_extract_chapter_and_book_simple(self):
        """Test that type_3_parser extracts chapter and book information from quoted chapter format"""
        test_citation = "Mead, J. G.; Brownell, R. L. Jr. (2005). 'Order Cetacea'. In Wilson, D. E.; Reeder, D. M. (eds.). Mammal Species of the World: A Taxonomic and Geographic Reference (3rd ed.). Johns Hopkins University Press. ISBN 978-0-8018-8221-0"
        result = self.parser(test_citation)
        self.assertEqual(result["chapter_authors"], "Mead, J. G.; Brownell, R. L. Jr.")
        self.assertEqual(result["book_authors"], "Wilson, D. E.; Reeder, D. M. (eds.)")
        self.assertEqual(result["year"], "2005")
        self.assertEqual(result["chapter_title"], "Order Cetacea")
        self.assertEqual(result["book_title"], "Mammal Species of the World: A Taxonomic and Geographic Reference (3rd ed.)")
        self.assertEqual(result["isbn"], "978-0-8018-8221-0")
        # Check that extracted parts are removed from remaining text
        self.assertNotIn("Mead, J. G.; Brownell, R. L. Jr.", result["remaining_text"])
        self.assertNotIn("Order Cetacea", result["remaining_text"])
        self.assertNotIn("Wilson, D. E.; Reeder, D. M.", result["remaining_text"])
        self.assertNotIn("Mammal Species of the World", result["remaining_text"])
        self.assertNotIn("(2005)", result["remaining_text"])
        self.assertNotIn("ISBN", result["remaining_text"])

    def test_extract_chapter_and_book_complex(self):
        """Test that type_3_parser extracts chapter and book information from complex quoted chapter format"""
        test_citation = "Ashton, Sally-Ann (2001b), '163 Limestone head of Cleopatra VII', in Walker, Susan; Higgs, Peter (eds.), Cleopatra of Egypt: from History to Myth, Princeton University Press (British Museum Press),, ISBN 978-0-691-08835-8"
        result = self.parser(test_citation)
        self.assertEqual(result["chapter_authors"], "Ashton, Sally-Ann")
        self.assertEqual(result["book_authors"], "Walker, Susan; Higgs, Peter (eds.)")
        self.assertEqual(result["year"], "2001")
        self.assertEqual(result["chapter_title"], "163 Limestone head of Cleopatra VII")
        self.assertEqual(result["book_title"], "Cleopatra of Egypt: from History to Myth")
        self.assertEqual(result["isbn"], "978-0-691-08835-8")
        # Check that extracted parts are removed from remaining text
        self.assertNotIn("Ashton, Sally-Ann", result["remaining_text"])
        self.assertNotIn("163 Limestone head of Cleopatra VII", result["remaining_text"])
        self.assertNotIn("Walker, Susan; Higgs, Peter", result["remaining_text"])
        self.assertNotIn("Cleopatra of Egypt: from History to Myth", result["remaining_text"])
        self.assertNotIn("(2001b)", result["remaining_text"])
        self.assertNotIn("ISBN", result["remaining_text"])

    def test_chester_volcanic_citation(self):
        """Test parsing Chester citation with quoted chapter title and book"""
        test_citation = "Chester, DK; Duncan, AM (2007). 'Geomythology, theodicy, and the continuing relevance of religious worldviews on responses to volcanic eruptions'. In Grattan, J; Torrence, R (eds.). Living under the shadow: The cultural impacts of volcanic eruptions. Walnut Creek: Left Coast. ISBN 9781315425177"
        result = self.parser(test_citation)
        self.assertEqual(result["chapter_authors"], "Chester, DK; Duncan, AM")
        self.assertEqual(result["book_authors"], "Grattan, J; Torrence, R (eds.)")
        self.assertEqual(result["year"], "2007")
        self.assertEqual(result["chapter_title"], "Geomythology, theodicy, and the continuing relevance of religious worldviews on responses to volcanic eruptions")
        self.assertEqual(result["book_title"], "Living under the shadow: The cultural impacts of volcanic eruptions")
        self.assertEqual(result["isbn"], "9781315425177")


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