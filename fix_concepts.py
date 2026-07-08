# fix_concepts.py
from app.fact_cache import FactCache
import re

def clean_concept(concept):
    \"\"\"Clean up concept names\"\"\"
    # Remove leading numbers like "4. "
    concept = re.sub(r'^\d+\.\s+', '', concept)
    # Remove extra spaces
    concept = re.sub(r'\s+', ' ', concept).strip()
    return concept

def main():
    print("🔧 Starting concept cleanup...")
    
    cache = FactCache()
    cache.load()
    
    # Get all facts
    all_facts = cache.get_all_facts()
    print(f"📚 Found {len(all_facts)} facts to process")
    
    # Clean concepts
    cleaned_count = 0
    cleaned_facts = []
    
    for f in all_facts:
        original = f.get('concept', '')
        cleaned_concept = clean_concept(original)
        
        if cleaned_concept != original:
            print(f"🔄 Cleaning: '{original}' → '{cleaned_concept}'")
            f['concept'] = cleaned_concept
            # Also clean sentence and definition if they contain the original
            if 'sentence' in f and original in f['sentence']:
                f['sentence'] = f['sentence'].replace(original, cleaned_concept)
            if 'definition' in f and original in f['definition']:
                f['definition'] = f['definition'].replace(original, cleaned_concept)
            cleaned_count += 1
        
        cleaned_facts.append(f)
    
    # Save cleaned facts
    cache.facts = {f['concept'].lower(): f for f in cleaned_facts}
    cache.save()
    
    print(f"✅ Saved {len(cleaned_facts)} cleaned facts")
    print(f"🔄 Cleaned {cleaned_count} concepts")
    
    # Show sample of cleaned concepts
    print("\n📊 Sample cleaned concepts:")
    for i, f in enumerate(list(cache.facts.values())[:5]):
        print(f"  {i+1}. {f['concept']} → {f.get('concept_type', 'unknown')}")

if __name__ == "__main__":
    main()
