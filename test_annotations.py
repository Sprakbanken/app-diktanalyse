#!/usr/bin/env python3
"""Test script to understand annotation output format"""

from poetry_analysis.rhyme_detection import tag_text
from poetry_analysis.alliteration import find_line_alliterations, extract_alliteration
from poetry_analysis.anaphora import extract_poem_anaphora
import json


text = """
Peter Piper picked a peck
Stille skimrer snøen
Stille synker solen
Stille stiger stjernene
Glitrer gjennom grenene


Peter Piper picked a peck
Stille skimrer snøen
Stille synker solen
Stille stiger stjernene
Glitrer gjennom grenene
"""


print("=" * 60)
print("TEST TEXT:")
print(text)
print("=" * 60)

print("\nEND RHYMES:")
end_rhymes = list(tag_text(text))
print(json.dumps(end_rhymes, indent=2, ensure_ascii=False))

print("\nALLITERATION:")
alliteration = list(extract_alliteration(text.splitlines()))
print("ALLITERATION RESULT:")
print(json.dumps(alliteration, indent=2, ensure_ascii=False))
print("\nType:", type(alliteration))
if alliteration:
    print("First item type:", type(alliteration[0]))
    print("First item:", alliteration[0])

print("\nANAPHORA:")
anaphora = list(extract_poem_anaphora(text))
print(json.dumps(anaphora, indent=2, ensure_ascii=False))
