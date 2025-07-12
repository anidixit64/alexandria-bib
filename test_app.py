import unittest
import json
import sys
import os

# Add the current directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

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

if __name__ == '__main__':
    unittest.main() 