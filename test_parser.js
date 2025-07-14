const citation = "Underhill, David (1993). Australia's dangerous creatures (4th rev. ed.). Sydney: Reader's Digest Services. ISBN 978-0864380180";

console.log('Citation:', citation);
console.log('Has quotes:', citation.includes('"') || citation.includes("'"));
console.log('Has editor:', citation.includes('(ed.') || citation.includes('(eds.'));
console.log('Has parenthetical year:', citation.match(/\([^)]*\d{4}[^)]*\)/));
console.log('Has standalone year:', citation.match(/\b(19|20)\d{2}\b/) && !citation.includes('('));

// Test the determineParser logic
function determineParser(citation) {
  console.log('Determining parser for citation:', citation);
  
  // Check for chapter citations (has quoted chapter titles)
  if (citation.includes('"') || (citation.includes("'") && citation.match(/['"][^'"]*['"]\s*(?:in|In|\.)/))) {
    console.log('Selected type3 (quoted chapter title found)');
    return 'type3'; // Chapter citations with quotes
  }
  
  // Check for editor citations (contains "(ed.)" or "(eds.)")
  if (citation.includes('(ed.') || citation.includes('(eds.')) {
    console.log('Selected type5 (editor found)');
    return 'type5'; // Editor citations
  }
  
  // Check for parenthetical dates (Type 1) - look for year in parentheses
  if (citation.match(/\([^)]*\d{4}[^)]*\)/)) {
    console.log('Selected type1 (parenthetical year found)');
    return 'type1';
  }
  
  // Check for standalone years (Type 2)
  if (citation.match(/\b(19|20)\d{2}\b/) && !citation.includes('(')) {
    console.log('Selected type2 (standalone year found)');
    return 'type2';
  }
  
  // Default to Type 1 for unknown formats
  console.log('Selected type1 (default)');
  return 'type1';
}

console.log('\n--- Testing determineParser ---');
const result = determineParser(citation);
console.log('Final result:', result); 