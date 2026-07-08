from app.fact_extractor import FactExtractor

extractor = FactExtractor()
content = "Database normalization reduces redundancy. 1NF requires atomic values in each cell. Normalization improves data integrity."
facts = extractor.extract_facts(content, "Database")

print("Extracted facts:")
for f in facts:
    print(f"  Statement: {f['statement'][:50]}...")
    print(f"  Answer: {f['answer']}")
    print()