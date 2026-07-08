# ontology_validator.py
from app.schema import ConceptType, TYPE_HIERARCHY

class OntologyValidator:
    def __init__(self):
        self.valid_types = [t.value for t in ConceptType]
        self.hierarchy = TYPE_HIERARCHY
    
    def validate_type(self, type_name: str) -> bool:
        """Validate if a type is valid"""
        return type_name in self.valid_types
    
    def get_compatible_question_types(self, concept_type: str) -> List[str]:
        """Get valid question types for a concept type"""
        type_map = {
            'algorithm': ['definition', 'comparison', 'application'],
            'metric': ['definition', 'comparison'],
            'model': ['definition', 'application', 'scenario'],
            'process': ['definition', 'scenario'],
            'concept': ['definition', 'scenario']
        }
        return type_map.get(concept_type, ['definition'])
    
    def get_question_difficulty(self, concept_type: str, question_type: str) -> float:
        """Get difficulty score for a question"""
        difficulties = {
            ('algorithm', 'definition'): 0.3,
            ('algorithm', 'comparison'): 0.6,
            ('algorithm', 'application'): 0.7,
            ('model', 'definition'): 0.4,
            ('model', 'application'): 0.6,
            ('metric', 'definition'): 0.5,
            ('metric', 'comparison'): 0.7,
        }
        return difficulties.get((concept_type, question_type), 0.5)