import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .schema import create_fact, is_weak_concept, detect_concept_type, ConceptType

class FactExtractor:
    def __init__(self, notes_path="sample_notes"):
        self.notes_path = Path(notes_path)
        
        # Bad concepts to filter out
        self.bad_concepts = {
            "these", "this", "that", "they", "most", "how", "why", "what", "when", "where",
            "approach", "method", "process", "concept", "example", "examples",
            "used", "used for", "behavior", "function", "variable",
            "algorithm", "structure", "system", "data", "information",
            "layer", "layers", "overview", "summary", "conclusion", "references",
            "introduction", "simple analogy", "performance layer", "control layer",
            "hardware layer", "software layer", "execution layer", "learning layer",
            "optimization layer", "model lifecycle", "performance & algorithm layer",
            "data structures optimization layer", "system control layer",
            "model optimization layer", "core learning layer", "software execution layer",
            "technique examples", "example techniques", "techniques", "types", "types of",
            "categories", "category", "classification", "examples", "notes",
            "definition", "overview", "introduction", "summary"
        }
        
        # Invalid patterns to reject
        self.invalid_patterns = [
            r'.*&.*layer',
            r'.*layer$',
            r'^types?\s+of',
            r'^why\s',
            r'^how\s',
            r'^simple analogy',
            r'^performance',
            r'^overview',
            r'^summary',
            r'^introduction',
            r'^conclusion',
            r'^references',
            r'^examples?$',
            r'^technique examples?$',
            r'^notes$',
            r'^definition$',
        ]
        
        # Invalid concepts to reject (exact matches)
        self.invalid_concepts = {
            "Examples", "Technique Examples", "Overview", "Introduction", "Summary",
            "Notes", "Definition", "Concept", "Example", "Layer", "Types", "Categories",
            "Classification", "Techniques", "Methods", "Approaches", "Processes"
        }
        
        # Acronym mapping
        self.acronyms = {
            "Ai": "AI",
            "Cpu": "CPU",
            "Gpu": "GPU",
            "Sql": "SQL",
            "Api": "API",
            "Dbms": "DBMS",
            "Iot": "IoT",
            "Ml": "ML",
            "Nlp": "NLP",
            "Os": "OS",
            "Ram": "RAM",
            "Rom": "ROM",
            "Bios": "BIOS",
            "Usb": "USB",
            "Hdmi": "HDMI",
            "Pci": "PCI",
            "Ssd": "SSD",
            "Hdd": "HDD",
            "Lan": "LAN",
            "Wan": "WAN",
            "Vpn": "VPN",
            "Dns": "DNS",
            "Dhcp": "DHCP",
            "Tcp": "TCP",
            "Udp": "UDP",
            "Ip": "IP",
            "Http": "HTTP",
            "Https": "HTTPS",
            "Ftp": "FTP",
            "Ssh": "SSH",
            "Smtp": "SMTP",
            "Pop3": "POP3",
            "Imap": "IMAP",
        }
        
        # Manual concept type overrides (for specific concepts)
        self.concept_type_overrides = {
            # Algorithms
            "Quick Sort": "algorithm",
            "Merge Sort": "algorithm",
            "Bubble Sort": "algorithm",
            "Binary Search": "algorithm",
            "Linear Search": "algorithm",
            "Dynamic Programming": "algorithm",
            "Greedy": "algorithm",
            "Divide and Conquer": "algorithm",
            "Backtracking": "algorithm",
            "Recursion": "algorithm",
            
            # Models
            "Deep Learning": "model",
            "Neural Network": "model",
            "CNN": "model",
            "RNN": "model",
            "Transformer": "model",
            "GPT": "model",
            "BERT": "model",
            "Regression": "model",
            "Classification": "model",
            "Clustering": "model",
            
            # Metrics
            "Time Complexity": "metric",
            "Space Complexity": "metric",
            "Big O": "metric",
            "Accuracy": "metric",
            "Precision": "metric",
            "Recall": "metric",
            "F1 Score": "metric",
            "Perplexity": "metric",
            
            # Data Structures
            "Array": "data_structure",
            "Linked List": "data_structure",
            "Stack": "data_structure",
            "Queue": "data_structure",
            "Tree": "data_structure",
            "Graph": "data_structure",
            "Hash Map": "data_structure",
            "Heap": "data_structure",
            "Trie": "data_structure",
            
            # Systems
            "DBMS": "system",
            "Database": "system",
            "Operating System": "system",
            "File System": "system",
            
            # Frameworks
            "TensorFlow": "framework",
            "PyTorch": "framework",
            "Django": "framework",
            "React": "framework",
            
            # Paradigms
            "OOP": "paradigm",
            "Functional Programming": "paradigm",
            "Procedural": "paradigm",
            
            # Processes
            "Normalization": "process",
            "Backpropagation": "process",
            "Gradient Descent": "process",
            "Training": "process",
            "Inference": "process",
        }
    
    def normalize_concept(self, text: str) -> str:
        """Normalize concept text - title case, collapse spaces, fix acronyms"""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # collapse spaces
        text = text.title()  # title case (e.g., "deep learning" -> "Deep Learning")
        
        # Fix acronyms
        for k, v in self.acronyms.items():
            text = text.replace(k, v)
        
        # Fix "Ai Model" specifically
        text = text.replace("Ai Model", "AI Model")
        text = text.replace("Ai", "AI")
        
        return text
    
    def get_concept_type(self, concept: str, definition: str = "") -> str:
        """Get concept type with override support"""
        # Check manual overrides first
        if concept in self.concept_type_overrides:
            return self.concept_type_overrides[concept]
        
        # Try auto-detection
        detected = detect_concept_type(concept, definition)
        if detected and detected != "concept":
            return detected
        
        # Default to "concept"
        return "concept"
    
    def score_fact(self, fact: Dict[str, Any]) -> int:
        """Score a fact based on quality indicators"""
        score = 0
        concept = fact.get('concept', '')
        definition = fact.get('definition', '')
        
        # Concept quality
        if len(concept) > 3:
            score += 2
        if len(concept.split()) <= 3:
            score += 2
        if concept[0].isupper():
            score += 1
        
        # Definition quality
        word_count = len(definition.split())
        if word_count >= 8:
            score += 3
        elif word_count >= 5:
            score += 1
        
        # Source weight
        if fact.get('is_header', False):
            score += 3
        elif fact.get('is_bullet', False):
            score += 1
        
        # Sentence clarity
        if fact.get('sentence', '').strip().endswith('.'):
            score += 1
        
        # Penalize weak patterns
        if concept.lower() in ['concept', 'example', 'type', 'method']:
            score -= 5
        if 'layer' in concept.lower():
            score -= 3
        
        # Bonus for strong concept types
        concept_type = fact.get('concept_type', '')
        if concept_type in ['algorithm', 'model', 'data_structure']:
            score += 2
        
        return score
    
    def filter_weak_facts(self, facts: List[Dict[str, Any]], min_score: int = 5) -> List[Dict[str, Any]]:
        """Filter out weak facts based on score"""
        scored_facts = []
        for f in facts:
            f['score'] = self.score_fact(f)
            if f['score'] >= min_score:
                scored_facts.append(f)
        
        print(f"  📊 Filtered {len(facts) - len(scored_facts)} weak facts (score < {min_score})")
        return scored_facts
    
    def _create_fact_with_type(self, concept: str, definition: str, topic: str, source: str, 
                               sentence: str = "", is_header: bool = False, is_bullet: bool = False,
                               weight: int = 5) -> Dict[str, Any]:
        """Create a fact with concept type detection"""
        concept_type = self.get_concept_type(concept, definition)
        
        fact = create_fact(
            concept=concept,
            definition=definition,
            topic=topic,
            source=source,
            concept_type=concept_type
        )
        
        source_note = Path(str(source)).name if str(source) and str(source) != 'inline' else 'inline'
        statement = self._sanitize_fact_text(sentence or definition or concept)
        statement = statement[:220]
        fact_id = f"{self._slugify(topic)}_{self._slugify(source_note)}_{self._slugify(concept)[:20]}"
        
        if sentence:
            fact['sentence'] = sentence[:220]
        fact['is_header'] = is_header
        fact['is_bullet'] = is_bullet
        fact['weight'] = weight
        fact['fact_id'] = fact_id
        fact['source_note'] = source_note
        fact['supporting_fact'] = statement
        
        # Compatibility fields for the existing quiz pipeline
        fact['statement'] = statement
        fact['answer'] = concept
        
        return fact

    def _slugify(self, text: str) -> str:
        return re.sub(r'[^a-z0-9]+', '_', str(text or '').lower()).strip('_')

    def _sanitize_fact_text(self, text: str) -> str:
        cleaned = str(text or '').strip()
        cleaned = re.sub(r'^\s*#+\s*', '', cleaned)
        cleaned = re.sub(r'^\s*[-*+]\s*', '', cleaned)
        cleaned = re.sub(r'^\s*\d+\.\s*', '', cleaned)
        cleaned = re.sub(r'\[\[(.*?)\]\]', r'\1', cleaned)
        cleaned = re.sub(r'[*_`>#]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned.rstrip(' .')

    def _build_atomic_fact(self, text: str, topic: str, source: str, weight: int = 7) -> Optional[Dict[str, Any]]:
        cleaned = self._sanitize_fact_text(text)
        if not cleaned or len(cleaned.split()) < 4:
            return None
        if len(cleaned.split()) > 24:
            cleaned = ' '.join(cleaned.split()[:24]).rstrip(' .')
        if any(marker in cleaned.lower() for marker in ['#', '[[', ']]', '---', 'http', 'https']):
            return None
        if cleaned.lower().startswith(('how ', 'why ', 'what ', 'when ', 'where ', 'conclusion', 'summary', 'overview', 'references')):
            return None
        if not re.search(r'\b(uses|supports|allows|enables|provides|stores|manages|reduces|improves|refers|means|helps|contains|includes)\b', cleaned.lower()):
            return None

        answer = cleaned
        for pattern in [r'(?:uses|supports|allows|enables|provides|stores|manages|reduces|improves|offers)\s+(.+)$', r'(?:refers to|means|stands for|is|are)\s+(.+)$']:
            match = re.search(pattern, cleaned, re.I)
            if match:
                answer = match.group(1).strip()
                break
        answer = self._sanitize_fact_text(answer)
        if len(answer.split()) > 8:
            answer = ' '.join(answer.split()[:8]).rstrip(' .')

        fact = self._create_fact_with_type(
            concept=answer,
            definition=cleaned,
            topic=topic,
            source=source,
            sentence=cleaned,
            weight=weight,
        )
        fact['answer'] = answer
        fact['statement'] = cleaned
        fact['supporting_fact'] = cleaned
        return fact

    def _extract_atomic_facts(self, content: str, topic: str, source: str) -> List[Dict[str, Any]]:
        facts = []
        seen = set()
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('```') or line.startswith('#'):
                continue
            if line.lower().startswith(('example', 'examples', 'conclusion', 'summary', 'overview', 'references')):
                continue
            line = self._sanitize_fact_text(line)
            if not line or len(line.split()) < 4:
                continue
            fact = self._build_atomic_fact(line, topic, source)
            if not fact:
                continue
            key = fact['supporting_fact'].lower()
            if key not in seen:
                seen.add(key)
                facts.append(fact)
        return facts

    def extract_facts(self, content: str, topic: str, source: str = "inline") -> List[Dict[str, Any]]:
        """Public API for extracting facts from arbitrary content."""
        if not content or not str(content).strip():
            return []
        return self._extract_facts(content, topic, source)

    def _get_topic_keywords(self, topic: str) -> List[str]:
        """Return a lightweight keyword set for relevance filtering."""
        topic_text = (topic or "").strip().lower()
        if not topic_text:
            return []

        keywords = set()
        words = [w for w in re.split(r'[^a-z0-9]+', topic_text) if w]
        keywords.update(words)
        keywords.add(topic_text)

        if "algorithm" in topic_text or "algorithms" in topic_text:
            keywords.update([
                "algorithm", "algorithms", "recursion", "sorting", "search", "dynamic programming",
                "greedy", "backtracking", "divide and conquer", "complexity", "optimization"
            ])
        if "database" in topic_text or "sql" in topic_text:
            keywords.update(["database", "dbms", "table", "query", "normalization", "schema", "index", "sql"])
        if "machine" in topic_text and "learning" in topic_text:
            keywords.update(["machine learning", "deep learning", "neural network", "model", "training", "inference"])

        return sorted(keywords)
    
    def _extract_header_facts(self, content: str, topic: str, source: str) -> List[Dict[str, Any]]:
        """Extract facts from headers"""
        facts = []
        seen = set()
        
        headers = re.findall(r'^#+\s*(.+)$', content, flags=re.MULTILINE)
        for header in headers:
            header = header.strip()
            header_normalized = self.normalize_concept(header)
            header_lower = header_normalized.lower()
            
            # Skip bad headers
            if header_lower in self.bad_concepts:
                continue
            if header_normalized in self.invalid_concepts:
                continue
            if header_lower.startswith(("how ", "why ", "what ", "when ", "where ")):
                continue
            
            # Check invalid patterns
            if any(re.match(p, header_lower) for p in self.invalid_patterns):
                continue
            
            # Reject headers with "Layer" in them
            if 'layer' in header_lower:
                continue
            
            # Check for weak concepts
            if is_weak_concept(header_normalized):
                continue
            
            if len(header) > 2 and len(header) < 50 and len(header.split()) <= 4:
                key = header_lower
                if key not in seen:
                    seen.add(key)
                    facts.append(self._create_fact_with_type(
                        concept=header_normalized,
                        definition=header_normalized,
                        topic=topic,
                        source=source,
                        is_header=True,
                        weight=10
                    ))
        
        return facts
    
    def _extract_bullet_facts(self, content: str, topic: str, source: str) -> List[Dict[str, Any]]:
        """Extract facts from bullet points"""
        facts = []
        seen = set()
        
        # Find bullet points (lines starting with -, *, or numbers)
        bullet_pattern = r'^[\s]*[-*+]\s+(.+)$'
        number_pattern = r'^[\s]*\d+\.\s+(.+)$'
        
        # Combine patterns
        pattern = f'{bullet_pattern}|{number_pattern}'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            bullet_text = match.group(1) or match.group(2)
            if not bullet_text:
                continue
                
            bullet_text = bullet_text.strip()
            if len(bullet_text) < 20:
                continue
                
            # Try to extract concept from bullet
            # Look for "X is Y" patterns within the bullet
            match2 = re.search(r'([A-Z][a-zA-Z\s]{2,})\s+(is|are|means|refers to|stands for)\s+([^,.!?]+)', bullet_text, re.IGNORECASE)
            if match2:
                concept = self.normalize_concept(match2.group(1))
                concept = re.sub(r'^(The|A|An)\s+', '', concept, flags=re.IGNORECASE)
                definition = match2.group(3).strip()
                
                concept_lower = concept.lower()
                if (len(concept.split()) <= 4 and 
                    len(definition.split()) >= 5 and
                    concept_lower not in self.bad_concepts and
                    'layer' not in concept_lower and
                    not is_weak_concept(concept)):
                    
                    key = concept_lower
                    if key not in seen:
                        seen.add(key)
                        facts.append(self._create_fact_with_type(
                            concept=concept,
                            definition=definition,
                            topic=topic,
                            source=source,
                            sentence=bullet_text[:200],
                            is_bullet=True,
                            weight=7
                        ))
        
        return facts
    
    def _extract_sentence_facts(self, content: str, topic: str, source: str) -> List[Dict[str, Any]]:
        """Extract facts from regular sentences"""
        facts = []
        seen = set()
        
        # Clean content
        content = re.sub(r'\*\*|\*|__|_', '', content)
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        content = re.sub(r'\[\[(.*?)\]\]', r'\1', content)
        content = re.sub(r'^[\s]*[-*+]\s+', '', content, flags=re.MULTILINE)
        content = re.sub(r'^[\s]*\d+\.\s+', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s+', ' ', content)
        
        sentences = re.split(r'[.!?\n]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 25:
                continue
            
            if sentence.lower().startswith(('the', 'this', 'that', 'there', 'it is', 'they are')):
                continue
            
            sentence = sentence.replace('\n', ' ').strip()
            sentence = re.sub(r'\s+', ' ', sentence)
            
            # Pattern 1: "X is Y" or "X are Y"
            match = re.search(r'([A-Z][a-zA-Z\s]{2,})\s+(is|are|refers to|means|stands for|consists of|is used for)\s+([^,.!?]+)', sentence, re.IGNORECASE)
            if match:
                concept = self.normalize_concept(match.group(1))
                concept = re.sub(r'^(The|A|An)\s+', '', concept, flags=re.IGNORECASE)
                definition = match.group(3).strip()
                
                concept_lower = concept.lower()
                
                if concept in self.invalid_concepts:
                    continue
                if 'layer' in concept_lower:
                    continue
                if any(re.match(p, concept_lower) for p in self.invalid_patterns):
                    continue
                if len(concept) < 3 or len(concept) > 50:
                    continue
                if len(concept.split()) > 4:
                    continue
                if len(definition.split()) < 8:
                    continue
                if concept_lower in self.bad_concepts:
                    continue
                if concept_lower.startswith(("how ", "why ", "what ", "when ", "where ")):
                    continue
                if is_weak_concept(concept):
                    continue
                
                key = concept_lower
                if key not in seen:
                    seen.add(key)
                    facts.append(self._create_fact_with_type(
                        concept=concept,
                        definition=definition,
                        topic=topic,
                        source=source,
                        sentence=sentence[:200],
                        weight=5
                    ))
                continue
            
            # Pattern 2: "X (Y)" - acronym pattern
            match = re.search(r'([A-Z]{2,})\s+\(([^)]+)\)', sentence)
            if match:
                concept = self.normalize_concept(match.group(1))
                definition = match.group(2)
                concept_lower = concept.lower()
                
                if concept in self.invalid_concepts:
                    continue
                if 'layer' in concept_lower:
                    continue
                if concept_lower in self.bad_concepts:
                    continue
                if len(definition.split()) < 8:
                    continue
                if is_weak_concept(concept):
                    continue
                
                key = concept_lower
                if key not in seen:
                    seen.add(key)
                    facts.append(self._create_fact_with_type(
                        concept=concept,
                        definition=definition,
                        topic=topic,
                        source=source,
                        sentence=sentence[:200],
                        weight=5
                    ))
                continue
            
            # Pattern 3: "X — Y" or "X - Y"
            match = re.search(r'([A-Z][a-zA-Z\s]{2,})\s+[—\-]\s+([^,.!?]+)', sentence)
            if match:
                concept = self.normalize_concept(match.group(1))
                concept = re.sub(r'^(The|A|An)\s+', '', concept, flags=re.IGNORECASE)
                definition = match.group(2).strip()
                
                concept_lower = concept.lower()
                
                if concept in self.invalid_concepts:
                    continue
                if 'layer' in concept_lower:
                    continue
                if any(re.match(p, concept_lower) for p in self.invalid_patterns):
                    continue
                if len(concept.split()) > 4:
                    continue
                if len(definition.split()) < 8:
                    continue
                if concept_lower in self.bad_concepts:
                    continue
                if concept_lower.startswith(("how ", "why ", "what ", "when ", "where ")):
                    continue
                if is_weak_concept(concept):
                    continue
                
                key = concept_lower
                if key not in seen:
                    seen.add(key)
                    facts.append(self._create_fact_with_type(
                        concept=concept,
                        definition=definition,
                        topic=topic,
                        source=source,
                        sentence=sentence[:200],
                        weight=5
                    ))
                continue
        
        return facts
    
    def _extract_facts(self, content: str, topic: str, source: str) -> List[Dict[str, Any]]:
        """Extract all facts from content with concept typing"""
        facts = []
        
        # 1. Extract headers
        header_facts = self._extract_header_facts(content, topic, source)
        facts.extend(header_facts)
        
        # 2. Extract bullets
        bullet_facts = self._extract_bullet_facts(content, topic, source)
        facts.extend(bullet_facts)
        
        # 3. Extract sentence facts
        sentence_facts = self._extract_sentence_facts(content, topic, source)
        facts.extend(sentence_facts)
        
        # 4. Add atomic facts from concise note statements
        atomic_facts = self._extract_atomic_facts(content, topic, source)
        facts.extend(atomic_facts)
        
        # 5. Deduplicate
        unique_facts = {}
        for f in facts:
            key = f.get("supporting_fact", f.get("statement", f["concept"])).lower()
            if key in unique_facts:
                # Keep the one with higher weight or longer definition
                if f.get("weight", 0) > unique_facts[key].get("weight", 0):
                    unique_facts[key] = f
                elif len(str(f.get("definition", ""))) > len(str(unique_facts[key].get("definition", ""))):
                    unique_facts[key] = f
            else:
                unique_facts[key] = f
        
        facts = list(unique_facts.values())
        
        # 6. Filter weak facts
        facts = self.filter_weak_facts(facts, min_score=5)
        
        # 6. Log concept type distribution
        type_counts = {}
        for f in facts:
            ct = f.get('concept_type', 'concept')
            type_counts[ct] = type_counts.get(ct, 0) + 1
        
        if type_counts:
            print(f"  📊 Concept types: {', '.join([f'{k}: {v}' for k, v in type_counts.items()])}")
        
        return facts
    
    def extract_from_file(self, file_path: str, topic: str) -> List[Dict[str, Any]]:
        """Extract facts from a single markdown file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.extract_facts(content, topic, file_path)
    
    def extract_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Extract all facts for a topic"""
        folder = self.notes_path / topic
        if not folder.exists():
            return []
        
        all_facts = []
        for md_file in folder.glob("*.md"):
            facts = self.extract_from_file(str(md_file), topic)
            all_facts.extend(facts)
        
        # Deduplicate across files
        unique_facts = {}
        for f in all_facts:
            key = f["concept"].lower()
            if key in unique_facts:
                if f.get("weight", 0) > unique_facts[key].get("weight", 0):
                    unique_facts[key] = f
                elif len(f["definition"]) > len(unique_facts[key]["definition"]):
                    unique_facts[key] = f
            else:
                unique_facts[key] = f
        
        facts = list(unique_facts.values())
        
        # Log type distribution for topic
        type_counts = {}
        for f in facts:
            ct = f.get('concept_type', 'concept')
            type_counts[ct] = type_counts.get(ct, 0) + 1
        
        if type_counts:
            print(f"  📊 {topic} types: {', '.join([f'{k}: {v}' for k, v in type_counts.items()])}")
        
        return facts
    
    def extract_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract facts for all topics"""
        all_facts = {}
        for folder in self.notes_path.iterdir():
            if folder.is_dir() and not folder.name.startswith('.'):
                topic = folder.name
                facts = self.extract_topic(topic)
                if facts:
                    all_facts[topic] = facts
                    print(f"  ✅ {topic}: {len(facts)} facts")
        return all_facts

if __name__ == "__main__":
    extractor = FactExtractor()
    all_facts = extractor.extract_all()
    print(f"\nTotal: {sum(len(v) for v in all_facts.values())} facts across {len(all_facts)} topics")