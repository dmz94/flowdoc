# About Decant

Decant started with a practical problem: converting a recipe
PDF into a format that was easier for my dyslexic son to read.

I used PDF-XChange Editor to manually reformat the document
with dyslexia-friendly typography (including OpenDyslexic). It
worked, but it was slow, repetitive, and fragile. After doing
that, I discovered the recipe site could export the same
content as HTML.

That was the unlock: HTML already contains structure (headings,
paragraphs, lists). If you can rely on semantic structure, you
can build a tool that re-renders content for readability
without solving the much harder problem of inferring structure
from fixed-layout formats.

I have spent years building systems that ingest structured
content and re-emit it in different forms. At Oxford University
Press, I ran the technology team for the dictionary division.
We stored data in structured formats (XML/JSON) and built
parsers and renderers to extract, transform, and present
content reliably. The same general approach applies here:

- parse structured input
- map it into a minimal internal model
- render to a stable, readable output

Although the trigger was a recipe, the underlying issue is
broader. Articles, manuals, technical docs, educational
materials, and work documents often have content that is
"there," but presented in a way that creates unnecessary
barriers for dyslexic readers.

I stopped coding professionally years ago, but I really missed
it -- and sometimes wished I had stayed a coder rather than
move into management. But I also enjoy pulling the bits and
pieces together: product, architecture, priorities, quality.
AI tools -- specifically Claude as an architecture and
engineering partner -- made it possible to do both. I play the
roles I know: product owner, architect, team lead. The AI
writes the code. It is the closest I have come to running a
real engineering team since my last engineering role.

The name? When you decant wine, you pour it off the sediment --
the good stuff stays, the crud stays behind. That is what this
tool does to web articles.
