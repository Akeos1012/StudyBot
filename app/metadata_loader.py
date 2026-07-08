import os
import json
from pathlib import Path
from typing import List, Dict, Any

class MetadataLoader:
    def __init__(self, notes_path="sample_notes"):
        self.notes_path = Path(notes_path)
        self.metadata_file = self.notes_path / "metadata.json"
        self.metadata = []
        self.notes_cache = {}
        
    def load_metadata(self) -> List[Dict[str, Any]]:
        """Load only metadata from notes, not full content"""
        
        # Check if metadata cache exists
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"✅ Loaded {len(self.metadata)} notes from cache")
                return self.metadata
            except Exception as e:
                print(f"⚠️ Could not load cache, rebuilding: {e}")
        
        # Build metadata from scratch
        print("📂 Building metadata index...")
        for md_file in self.notes_path.glob("**/*.md"):
            try:
                # Read only first 500 chars to extract metadata
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read(2000)  # Read enough for frontmatter + title
                
                # Parse frontmatter
                metadata = self._parse_frontmatter_light(content)
                topic = metadata.get("topic", md_file.parent.name)
                subtopic = metadata.get("subtopic", "")
                
                # Get content length without loading full file
                full_content = open(md_file, 'r', encoding='utf-8').read()
                content_length = len(full_content)
                
                # Debug: print when subtopic is found
                if subtopic:
                    print(f"  📌 Found subtopic in {md_file.stem}: {subtopic}")
                
                self.metadata.append({
                    "path": str(md_file),
                    "topic": topic,
                    "subtopic": subtopic,
                    "title": md_file.stem,
                    "content_length": content_length,
                    "metadata": metadata
                })
            except Exception as e:
                print(f"⚠️ Warning: Could not load {md_file.name}: {e}")
                continue
        
        # Save metadata cache
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved metadata cache with {len(self.metadata)} notes")
        except Exception as e:
            print(f"⚠️ Could not save metadata cache: {e}")
        
        return self.metadata
    
    def get_note_content(self, note_path: str) -> str:
        """Load full content for a single note"""
        if note_path in self.notes_cache:
            return self.notes_cache[note_path]
        
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Remove frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2]
            self.notes_cache[note_path] = content
            return content
        except Exception as e:
            print(f"⚠️ Could not load note: {e}")
            return ""
    
    def get_truncated_content(self, note_path: str, max_chars: int = 2000) -> str:
        """Get content truncated at sentence boundary"""
        content = self.get_note_content(note_path)
        
        if len(content) <= max_chars:
            return content
        
        # Truncate at max_chars
        truncated = content[:max_chars]
        
        # Find the last period, question mark, or exclamation point
        # to cut at a sentence boundary
        sentence_endings = ['. ', '? ', '! ', '.\n', '?\n', '!\n']
        last_end = -1
        
        for ending in sentence_endings:
            pos = truncated.rfind(ending)
            if pos > last_end:
                last_end = pos
        
        if last_end > 0:
            # Cut at the sentence boundary
            return truncated[:last_end + 1]  # Include the punctuation
        else:
            # No sentence boundary found, try to cut at a space
            last_space = truncated.rfind(' ')
            if last_space > max_chars - 50:  # Only if we're near the limit
                return truncated[:last_space] + '...'
            return truncated + '...'
    
    def get_notes_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Get metadata for notes in a topic"""
        return [n for n in self.metadata if n["topic"].lower() == topic.lower()]
    
    def get_subtopics_by_topic(self, topic: str) -> List[str]:
        """Get all subtopics for a given topic"""
        subtopics = set()
        for note in self.metadata:
            if note["topic"].lower() == topic.lower():
                subtopic = note.get("subtopic", "")
                if subtopic:
                    subtopics.add(subtopic)
        return sorted(list(subtopics))
    
    def get_notes_by_subtopic(self, topic: str, subtopic: str) -> List[Dict[str, Any]]:
        """Get metadata for notes in a specific subtopic"""
        return [
            n for n in self.metadata 
            if n["topic"].lower() == topic.lower() 
            and n.get("subtopic", "").lower() == subtopic.lower()
        ]
    
    def _parse_frontmatter_light(self, content: str) -> Dict[str, Any]:
        """Parse only frontmatter (lighter version)"""
        # Remove BOM if present (UTF-8 BOM is \ufeff)
        if content.startswith('\ufeff'):
            content = content[1:]
            print("  🔧 Removed BOM from file")
        
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = {}
                    for line in parts[1].split('\n'):
                        line = line.strip()
                        if ':' in line and not line.startswith('#'):
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            if value.startswith('[') and value.endswith(']'):
                                value = [v.strip() for v in value[1:-1].split(',')]
                            frontmatter[key] = value
                            # Debug: print when subtopic is parsed
                            if key == 'subtopic':
                                print(f"  ✅ Parsed subtopic: {value}")
                    return frontmatter
                except Exception as e:
                    print(f"⚠️ Warning: Could not parse frontmatter: {e}")
                    return {}
        return {}

if __name__ == "__main__":
    loader = MetadataLoader()
    metadata = loader.load_metadata()
    print(f"\n📊 Summary:")
    print(f"Total notes: {len(metadata)}")
    
    # Show topics
    topics = {}
    for note in metadata:
        topic = note["topic"]
        topics[topic] = topics.get(topic, 0) + 1
    
    print(f"Topics: {len(topics)}")
    for topic, count in sorted(topics.items())[:5]:
        print(f"  - {topic}: {count} notes")
    
    # Show subtopics for Database
    print(f"\n📂 Subtopics for Database:")
    db_subtopics = loader.get_subtopics_by_topic("Database")
    if db_subtopics:
        for subtopic in db_subtopics:
            notes = loader.get_notes_by_subtopic("Database", subtopic)
            print(f"  - {subtopic}: {len(notes)} notes")
    else:
        print("  No subtopics found (add 'subtopic: name' to your note frontmatter)")