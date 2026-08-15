def get_canonical_grounding_context(concept: str, supporting_fact: str) -> str:
    """
    Constructs a canonical grounding context by ensuring the concept name 
    appears exactly once at the beginning if it is not already present.
    """
    if not concept:
        return supporting_fact
    
    if not supporting_fact:
        return concept
    
    c_lower = concept.lower()
    s_lower = supporting_fact.lower()
    
    # If the concept is already present at the start of the supporting fact,
    # just return the supporting fact.
    if s_lower.startswith(c_lower):
        return supporting_fact
        
    # If the concept is present but not at the start, this is an ambiguous case,
    # but based on the current architecture, we should assume the fact 
    # needs to be prefixed for grounding to work correctly.
    # We should avoid duplicating it.
    if c_lower in s_lower:
        # Check if it starts with the concept
        if s_lower.startswith(c_lower):
            return supporting_fact
        # If it contains it but doesn't start with it, 
        # it might be safer to prepend it to ensure it anchors grounding at the start
        return f"{concept} {supporting_fact}"
    
    # If the supporting fact is a continuation, prepend the concept
    return f"{concept} {supporting_fact}"
