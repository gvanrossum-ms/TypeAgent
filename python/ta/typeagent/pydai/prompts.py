BIG_PROMPT = """\
Convert the user's natural language question into a structured SearchQuery.
Follow the schema documentation exactly.

CRITICAL RULES:
1. Set rewritten_query to the original question with minor corrections (fix typos, remove "please")
   but NEVER omit meaningful phrases or time references!
2. For time ranges like "first 15 minutes", ALWAYS include BOTH start_date AND stop_date!

REQUIRED STRUCTURES:
- EntityTerm: {"name": "...", "is_name_pronoun": false, "type": ["book"], "facets": null}
- VerbsTerm: {"words": ["mention"], "tense": "Past"}
- ActionTerm: {"action_verbs": {"words": ["referenced"], "tense": "Past"},
              "actor_entities": "*", "target_entities": [entity], "is_informational": false}
- time_range: {"start_date": {"date": {"day": 1, "month": 4, "year": 2020},
                                "time": {"hour": 9, "minute": 0, "seconds": 0}},
                 "stop_date": {"date": {"day": 1, "month": 4, "year": 2020},
                                "time": {"hour": 9, "minute": 30, "seconds": 0}}}

FIELD USAGE:
- entity_search_terms: tangible things (people, places, books, etc.)
- search_terms: abstract concepts not covered by entities/actions
- action_search_term: when asking about actions/interactions
- facets: for entity properties like [{{"facet_name": "publication_year", "facet_value": "2008"}}]

ENTITY NAME RULES:
- Use name="*" when asking for "all books", "all movies", etc. to match any entity of that type
- Use specific names like "Asimov", "Harry Potter" for particular entities

ACTION PATTERNS:
- "What did X say about Y?" → action_verbs: ["say"], actor_entities: [X], target_entities: [Y]
- "Summarize X's thoughts to Y?" → action_verbs: ["summarize", "explain", "say"], actor_entities: [X], target_entities: [Y]
- "Who was that X we talked about?" → entity_search_terms: [EntityTerm(name="*", type=["person"])], search_terms: ["X"]
- "How did X get referenced?" → action_verbs: ["referenced"], actor_entities: "*", target_entities: [X]
- "Who mentioned X?" → action_verbs: ["mentioned"], actor_entities: "*", target_entities: [X]

IMPORTANT: Questions like "How did X get [verb]?" should use action_search_term with the verb!

TIME RANGE RULE:
time_range is ONLY for message timestamps, NOT content attributes!
- For relative times like "first 15 minutes", use the start of the CONVERSATION TIME RANGE as the reference.
- USE: "first 15 minutes", "messages between 2-3pm"
- DON'T USE: "published in 2008" (use entity facets instead)
"""
