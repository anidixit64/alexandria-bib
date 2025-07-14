#!/usr/bin/env python3

from app import type_1_parser, type_2_parser, type_3_parser, type_5_parser

def test_citation(citation, parser_name, parser_func):
    print(f"\n=== Testing with {parser_name} ===")
    print(f"Citation: {citation}")
    result = parser_func(citation)
    print(f"Result: {result}")
    return result

def main():
    citations = [
        "Helmholtz, Hermann (1924). Physiological Optics. Dover. ISBN 978-0-486-44260-0",
        "Miller, Ron (2005). Stars and Galaxies. Twenty-First Century Books. ISBN 978-0-7613-3466-8",
        "Aisin-Gioro, Puyi (1989) [First published 1964]. From Emperor to Citizen: The Autobiography of Aisin-Gioro Pu Yi 我的前半生 [The First Half of My Life; From Emperor to Citizen: The Autobiography of Aisin-Gioro Puyi] (in Chinese). Foreign Languages Press. ISBN 978-7-119-00772-4",
        "Sir Monier Monier-Williams; Ernst Leumann; Carl Cappeller (2002). A Sanskrit-English Dictionary: Etymologically and Philologically Arranged with Special Reference to Cognate Indo-European Languages. Motilal Banarsidass. ISBN 978-81-208-3105-6",
        "Verma, Archana (2007). Cultural and Visual Flux at Early Historical Bagh in Central India. Archana Verma. ISBN 978-1-4073-0151-8",
        "Harvey, Peter (2013), An Introduction to Buddhism: Teachings, History and Practices(2nd ed.), New York: Cambridge University Press,, ISBN 978-0-521-85942-4"
    ]
    
    print("\nExpected for Aisin-Gioro, Puyi:")
    print("Name: Aisin-Gioro, Puyi")
    print("Year: 1989")
    print("Title: From Emperor to Citizen: The Autobiography of Aisin-Gioro Pu Yi 我的前半生")
    print("ISBN: 978-7-119-00772-4\n")

    print("Expected for Sir Monier Monier-Williams et al.:")
    print("Name: Sir Monier Monier-Williams; Ernst Leumann; Carl Cappeller")
    print("Year: 2002")
    print("Title: A Sanskrit-English Dictionary: Etymologically and Philologically Arranged with Special Reference to Cognate Indo-European Languages")
    print("ISBN: 978-81-208-3105-6\n")

    print("Expected for Verma, Archana:")
    print("Name: Verma, Archana")
    print("Year: 2007")
    print("Title: Cultural and Visual Flux at Early Historical Bagh in Central India")
    print("ISBN: 978-1-4073-0151-8\n")

    print("Expected for Harvey, Peter:")
    print("Name: Harvey, Peter")
    print("Year: 2013")
    print("Title: An Introduction to Buddhism: Teachings, History and Practices(2nd ed.)")
    print("ISBN: 978-0-521-85942-4\n")

    parsers = [
        ("type_1_parser", type_1_parser),
        ("type_2_parser", type_2_parser),
        ("type_3_parser", type_3_parser),
        ("type_5_parser", type_5_parser)
    ]
    
    for citation in citations:
        print(f"\n{'='*60}")
        print(f"Testing citation: {citation}")
        print(f"{'='*60}")
        
        for parser_name, parser_func in parsers:
            test_citation(citation, parser_name, parser_func)

if __name__ == "__main__":
    main() 