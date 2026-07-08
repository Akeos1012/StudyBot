# clean_data.py
from app.fact_cache import FactCache
from app.schema import ConceptType
import re
from collections import defaultdict

class DataCleaner:
    def __init__(self):
        self.cache = FactCache()
        self.cache.load()
        
    def find_duplicates(self):
        """Find duplicate or near-duplicate concepts"""
        facts = self.cache.get_all_facts()
        concept_map = defaultdict(list)
        
        for f in facts:
            # Normalize for comparison
            normalized = self._normalize_concept(f['concept'])
            concept_map[normalized].append(f)
        
        duplicates = {k: v for k, v in concept_map.items() if len(v) > 1}
        return duplicates
    
    def _normalize_concept(self, concept):
        """Normalize concept for deduplication"""
        # Remove extra spaces
        concept = re.sub(r'\s+', ' ', concept).strip()
        # Lowercase for comparison
        return concept.lower()
    
    def find_corrupted_concepts(self):
        """Find concepts that are clearly corrupted"""
        facts = self.cache.get_all_facts()
        corrupted = []
        
        for f in facts:
            concept = f['concept']
            
            # Check for duplicated words
            words = concept.split()
            if len(words) != len(set(words)):
                corrupted.append({
                    'concept': concept,
                    'issue': 'duplicate words',
                    'suggestion': ' '.join(set(words))
                })
            
            # Check for redundant words
            redundant = ['Data', 'World', 'Augmentation']
            if any(word in concept for word in redundant):
                # Check if concept contains redundant combinations
                if 'Data' in concept and 'Augmentation' in concept:
                    # Suggest simplified form
                    simplified = concept.replace('World Data', '').replace('Data Augmentation', 'Augmentation').strip()
                    if simplified:
                        corrupted.append({
                            'concept': concept,
                            'issue': 'redundant words',
                            'suggestion': simplified
                        })
        
        return corrupted
    
    def clean(self):
        """Clean the data"""
        print("🧹 Cleaning data...")
        
        # Find duplicates
        duplicates = self.find_duplicates()
        if duplicates:
            print(f"\n📋 Found {len(duplicates)} duplicate groups:")
            for norm, items in list(duplicates.items())[:5]:
                concepts = [f['concept'] for f in items]
                print(f"  {norm}: {concepts}")
        
        # Find corrupted concepts
        corrupted = self.find_corrupted_concepts()
        if corrupted:
            print(f"\n💀 Found {len(corrupted)} corrupted concepts:")
            for c in corrupted:
                print(f"  {c['concept']} → {c['suggestion']}")
        
        return {
            'duplicates': duplicates,
            'corrupted': corrupted
        }
    
    def suggest_fixes(self):
        """Suggest concrete fixes"""
        print("\n🔧 Suggested fixes:")
        print("1. Run: python -c \"from app.fact_cache import FactCache; c=FactCache(); c.load(); facts=c.get_all_facts()\"")
        print("2. Manually fix 'World Data Data Augmentation' → 'Data Augmentation'")
        print("3. Implement canonical naming: Use consistent concept names")
        print("4. Add validation: Reject concepts with duplicate words")

if __name__ == "__main__":
    cleaner = DataCleaner()
    results = cleaner.clean()
    cleaner.suggest_fixes()