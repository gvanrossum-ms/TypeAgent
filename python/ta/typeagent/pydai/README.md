Pydantic.AI Experiments
=======================

This seems to produce better results for knowledge extracting than
promptscript, and has 11.3k starts (promptscript has 3 :-).

- `python analyze.py` extracts knowledge from a few paragraphs
  taken out of the Adrian Tchaikovsky podcast transcript.
  It finds plenty even without any prompt tuning.
  (I haven't compared to what typescript does here.)

- `python query.py` is supposed to translate a human question into
  a `SearchQuery` instance. It's not doing so great, and I need to
  think about how to give it a better prompt. (Maybe ask Copilot?)

Setup
-----

- Make a venv and activate it
- Run `pip install -r requirements.txt`
