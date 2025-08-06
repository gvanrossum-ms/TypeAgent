BIG_PROMPT = """\
Convert the user question into a SearchQuery representing it in a form usable to query a database.

ACTION PATTERNS:
- "What did X say about Y?" → action_verbs: ["say"], actor_entities: [X], target_entities: [Y]
- "Summarize X's thoughts to Y?" → action_verbs: ["summarize", "explain", "say"], actor_entities: [X], target_entities: [Y]
- "Who was that X we talked about?" → entity_search_terms: [EntityTerm(name="*", type=["person"])], search_terms: ["X"]
- "How did X get referenced?" → action_verbs: ["referenced"], actor_entities: "*", target_entities: [X]
- "Who mentioned X?" → action_verbs: ["mentioned"], actor_entities: "*", target_entities: [X]
"""
