from app.fact_extractor import FactExtractor
from app.metadata_loader import MetadataLoader

loader = MetadataLoader()
loader.load_metadata()
notes = loader.get_notes_by_topic('Algorithms')

content = ""
for n in notes[:3]:
    content += loader.get_truncated_content(n['path'], 1000) + "\n\n"

extractor = FactExtractor()
facts = extractor.extract_facts(content, 'Algorithms')

print(f"Facts extracted: {len(facts)}")
for i, f in enumerate(facts):
    print(f"  {i+1}. Statement: {f.get('statement', '')[:60]}...")
    print(f"     Answer: {f.get('answer', '')}")