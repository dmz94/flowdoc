# Typography Guidelines for Dyslexia-Friendly Design

**Status:** Revised  
**Last Updated:** February 11, 2026  
**Sources:** BDA Style Guide 2023, IDA, peer-reviewed studies (2013-2025)

---

## Font Choices

### Primary Recommendation (BDA Endorsed)
- **Arial**
- **Verdana**
- **Tahoma**
- **Century Gothic**
- **Trebuchet**
- **Calibri**
- **Open Sans**
- **Comic Sans** (despite poor reputation, BDA explicitly lists it as a recommended sans serif option)

**Justification:** BDA recommends sans serif fonts because "letters can appear less crowded." These fonts are tested across general legibility research and have no negative effects on dyslexic readers.

### Secondary Option (Promising, Not Independently Validated - v2 Consideration)
- **Lexend** (Google Fonts)

**Justification:** Designed to reduce visual stress and improve reading fluency through variable letter spacing. Originated from Dr. Bonnie Shaver-Troup's EdD research (Azusa Pacific University) and subsequent work with Google. Integrated into Google products. The peer-reviewed evidence base for dyslexia-specific improvement is limited - primarily the creator's doctoral research and internal testing. Treat as promising but not firmly established by independent replication. Available on Google Fonts with variable weight support.

**v2 Note:** Lexend is a candidate for future font toggles but is not included in v1.

### Tertiary Option (Low-Vision Optimized, Design Principles Relevant - v2 Consideration)
- **Atkinson Hyperlegible** (Atkinson Hyperlegible Next for variable weights)

**Justification:** Designed by Braille Institute for low-vision readers, not dyslexia specifically. Core design principles benefit dyslexic readers: unambiguous letterforms (B vs 8, 1 vs I vs l clearly distinct), open counters, longer ascenders/descenders. Free for personal and commercial use. Available on Google Fonts. No dyslexia-specific peer-reviewed research, but design philosophy addresses character differentiation, which is relevant to dyslexic readers. Multiple weights available, including variable font (Atkinson Hyperlegible Next, 2025).

**v2 Note:** Atkinson Hyperlegible is a candidate for future font toggles but is not included in v1.

### Optional User-Preference Font (v1: OpenDyslexic Only)
- **OpenDyslexic** (free, open-source, SIL-OFL license)

**v1 Decision:** OpenDyslexic is provided as a user preference toggle. Flowdoc does not claim OpenDyslexic improves outcomes for everyone.

**Research Context:** Most controlled studies show no reliable improvement in reading speed or accuracy compared to standard sans serif fonts (Wery & Diliberto 2017; Kuster et al. 2018; Rello & Baeza-Yates 2013). For a related specialized font, Dyslexie, one study (Marinus et al. 2016) found a 7% speed improvement over Arial, but the advantage disappeared when Arial's spacing was matched - suggesting spacing, not letterforms, explained the difference. For OpenDyslexic, one preliminary study (Franzen et al. 2019, conference abstract) found improved reading comprehension in adults reading longer texts, despite no speed improvement; this has not been replicated in a full peer-reviewed paper. Individual preference varies, and many users report subjective comfort with OpenDyslexic.

**Implementation Rule:** If OpenDyslexic is selected, embed the font so the output HTML remains self-contained. Otherwise, use the system font stack (Arial, Verdana) and embed no fonts.

**v1 Scope:** OpenDyslexic is the only font toggle in v1. Additional specialized fonts (Dyslexie, Lexend, Atkinson Hyperlegible) are deferred to v2.

**Not Recommended as Defaults:**
- Times New Roman (serif font; reduced tracking makes text harder to read for dyslexic readers)
- Fonts with thick styling, italics, or underlines

---

## Font Size

- **Baseline (print/desktop):** 12-14 point minimum (BDA recommendation)
- **Web equivalent:** 16-19px or 1-1.2em
- **Screen-optimised range:** Research (Rello et al. 2016) suggests 18-22pt may be optimal for screen reading and comprehension, well above BDA's baseline. The 12-14pt recommendation should be treated as a minimum, not a target, for digital contexts.
- **Headings:** Minimum 20% larger than body text, using bold for additional emphasis

**Justification:** BDA specifies 12-14pt as an accessible baseline. Screen-reading research suggests larger sizes improve both readability and comprehension. Design should accommodate user scaling beyond defaults.

---

## Spacing

### Letter Spacing (Tracking)
- **BDA guidance:** Increased inter-letter spacing improves readability, ideally around 35% of the average letter width
- **Caution:** BDA notes that excessive letter spacing can *reduce* readability. Set a reasonable upper bound; do not increase without limit.
- **Effect:** Reduces visual crowding, which particularly affects dyslexic readers (Zorzi et al. 2012)

### Word Spacing
- **BDA guidance:** Inter-word spacing should be at least 3.5 times the inter-letter spacing
- **Note:** Letter and word spacing interact - increasing letter spacing without proportionally adjusting word spacing can reduce readability by blurring word boundaries

### Line Height (Leading)
- **BDA recommendation:** 1.5 (150%) line spacing is preferable
- **Note:** Should be proportional to inter-word spacing
- **Effect:** Greater vertical space makes it easier to follow each line horizontally and locate line starts/ends

### Line Length
- **BDA guidance:** Lines should be approximately 60-70 characters
- **Effect:** Prevents eye-tracking fatigue from overly long lines; avoids excessive line-breaks from overly short lines

### Paragraph Spacing
- **Add extra space between paragraphs** to break up text blocks
- **Between headings and body:** Extra space around headings

### Margins and Layout
- **Avoid narrow columns** (like newspaper layouts)
- **Single color backgrounds only** - no patterns or images behind text
- **Padding:** Adequate white space around content

**Justification:** Spacing reduces cognitive load and visual stress. BDA guidance emphasises proportional relationships between letter, word, and line spacing - not simply "more is better" for any single dimension.

---

## Color & Contrast

### Text & Background
- **Text Color:** Dark text on light background (not white)
- **Recommended Backgrounds:** Cream, off-white, soft pastels
- **Minimum Contrast Ratio:** WCAG AA standard (4.5:1 for normal text, 3:1 for large text)

### Colors to Avoid
- **Green and red/pink** - difficult for color-blind individuals
- **Bright white backgrounds** - can appear dazzling and cause visual strain

### Digital Considerations
- **No background patterns or distracting surrounds**
- **Allow user control:** Offer choice of background colors for personalization

**Justification:** BDA recommends dark text on pale (non-white) background to reduce visual stress. Avoidance of problematic color combinations supports both dyslexic and color-blind readers.

---

## Layout & Structure

### Text Alignment
- **Left-aligned, ragged right edge** (no full justification)
- **Rationale:** Makes it easier to find the start/finish of each line

### Headings & Organization
- **Use consistent heading hierarchy** with Styles/formatting tools (not manual formatting)
- **Use section headings regularly** in long documents
- **Include table of contents** for navigation
- **Use bullet points and numbering** rather than continuous prose where appropriate

### Links and Navigation
- **Hyperlinks should be clearly differentiated** from headings and body text
- **Place hyperlinks at end of sentences** where possible (not embedded mid-text)
- **Ensure link text is descriptive** (not "click here")

### Visual Support
- **Use images, flowcharts, graphics** to support text
- **Avoid:**
  - Block capitals (much harder to read)
  - ALL CAPS mid-sentence (may be read as single letters by text readers)
  - Underlines and italics (make words appear crowded)
  - Unnecessary symbols/asterisks (problematic for text readers)

**Justification:** Structure and visual hierarchy reduce cognitive load. Consistency helps assistive technology and user navigation.

---

## Writing Style (BDA Guidance)

BDA's Style Guide includes readability guidance beyond typography that affects spacing and whitespace decisions in v1, and will directly inform content transformation features in v2:

- **Use short, simple sentences** in a direct style
- **Give instructions clearly;** avoid long sentences of explanation
- **Avoid jargon and abbreviations** where possible; always provide the expanded form when first used
- **Use active voice** where possible
- **Avoid dense paragraphs;** space content out

---

## Recommendations by Format

### Digital/Web
- Use WCAG 2.1 AA compliance as minimum standard
- Consider dyslexia-friendly mode toggle (not mandatory, but accessible)
- Ensure text can be resized without loss of functionality
- Avoid moving text and auto-playing media

### Documents (Word/PDF)
- Use Styles for consistent formatting
- Avoid automatic numbering (some text readers skip these)
- Use hyperlinks at end of sentences (not embedded in text)
- Provide alternative formats (text reader friendly, accessible PDF)

---

## Research Summary & Authority

**British Dyslexia Association (BDA):** Primary authority. The 2018 Style Guide was reviewed by researchers at the University of Southampton (Abi James, BDA Technology Committee chair and accessibility researcher). The 2023 version is a revision of that guide. Most comprehensive, evidence-based typography guidance available for dyslexia.

**International Dyslexia Association (IDA):** US-based. Does not publish a typography style guide. Does publish guidance discussing evidence on "special fonts" (OpenDyslexic, Dyslexie, etc.) and is skeptical of strong claims for their efficacy. Endorses WCAG accessibility standards and structured literacy instruction.

**Key Research Findings:**
- No single font "fixes" dyslexia; font choice is one part of accessibility
- Formatting (spacing, alignment, color) matters more than specialized font letterforms
- **OpenDyslexic:** Most studies show no reliable improvement in reading speed or accuracy (Wery & Diliberto 2017; Rello & Baeza-Yates 2013; Zikl et al. 2015). Preliminary evidence (Franzen et al. 2019, conference abstract) suggests possible comprehension benefits in longer texts for adult readers; not yet replicated in full peer-reviewed study. User preferences vary.
- **Dyslexie:** No consistent advantage attributable to letterforms. Apparent speed improvements over Arial disappear when spacing is matched (Marinus et al. 2016; Kuster et al. 2018). Evidence suggests spacing settings, not letter shapes, explain any observed benefit.
- **EasyReading:** One large Italian school study (Bachmann & Mengheri 2018) found statistically significant reading improvements vs Times New Roman, including in a dyslexia subgroup. However, EasyReading changes multiple variables simultaneously (letterforms, spacing, overall design), so the benefit cannot be attributed to letterforms alone.
- **Lexend:** Shows promise in reading fluency improvements, but independent peer-reviewed replication for dyslexia-specific outcomes is limited.
- Standard sans serif fonts (Arial, Verdana) perform as well as or better than specialized fonts in speed/accuracy research
- Individual preference is valid even when objective metrics don't change

---

## Implementation Strategy

1. **Default:** Use Arial or Verdana for all primary content
2. **Headings:** Use at least 20% larger, bold
3. **Spacing:** 1.5x line-height (BDA recommendation); letter spacing ~35% of average letter width; word spacing at least 3.5x letter spacing
4. **Line length:** Target 60-70 characters per line
5. **Colors:** Dark on cream/soft pastel, WCAG AA contrast minimum
6. **Layout:** Left-aligned, generous margins, no full justification
7. **v1 Font Toggle:** OpenDyslexic only (via `--font opendyslexic` CLI flag)
   - When selected: embed font for self-contained output
   - When not selected: use system font stack, embed nothing
8. **Testing:** Validate with WCAG tools and user feedback

---

## v2 Roadmap

The typography decisions above are **format-agnostic** and will transfer directly to all future output formats. v2 expands Flowdoc's scope in two directions: additional output formats and content transformation.

### Additional Output Formats
- **DOCX:** Font stack, sizing, spacing, and layout rules apply via document styles
- **PDF:** Same typography decisions apply; CSS-to-PDF pipeline carries over all spacing, color, and contrast rules
- **Markdown:** Typography applied via CSS; core decisions unchanged

### Additional Font Toggles (v2)
- **Lexend:** Variable letter spacing, promising but limited independent validation
- **Atkinson Hyperlegible:** Low-vision optimized, unambiguous letterforms
- **Dyslexie:** Paid option, spacing-dependent benefits

### Text-to-Speech Compatibility
BDA explicitly frames its Style Guide as supporting TTS use. These require content modification capability, not available in v1:
- Add punctuation after bullet points (semicolons, commas, or full stops) to create pauses in TTS
- Remove or replace symbols that get spoken awkwardly (asterisks, long dashes, unnecessary special characters)
- Avoid text in capital letters mid-line - TTS may read as single letters
- Replace automatic numbering - some text readers skip these

### Content Cleanup and Editing
Extends Flowdoc from format-only conversion to content transformation, informed by BDA writing style guidance:
- **Readability scoring:** Assess document complexity against BDA plain language principles
- **Sentence simplification:** Break long sentences, convert passive to active voice
- **Jargon expansion:** Detect abbreviations and provide expanded forms on first use
- **Paragraph breaking:** Split dense text blocks into shorter, spaced paragraphs
- **Symbol cleanup:** Remove or replace characters that interfere with TTS or screen readers

---

## Sources

- British Dyslexia Association. (2023). *Dyslexia Friendly Style Guide*. https://www.bdadyslexia.org.uk/
- Kuster, S. M., van Weerdenburg, M., Gompel, M., & Bosman, A. M. T. (2018). Dyslexie font does not benefit reading in children with or without dyslexia. *Annals of Dyslexia*, 68(1), 25-42.
- Marinus, E., Mostard, M., Segers, E., Schubert, T. M., Madelaine, A., & Wheldall, K. (2016). A special font for people with dyslexia: Does it work and, if so, why? *Dyslexia*, 22(3), 233-244.
- Wery, J. J., & Diliberto, J. A. (2017). The effect of a specialized dyslexia font, OpenDyslexic, on reading rate and accuracy. *Annals of Dyslexia*, 67(2), 114-127.
- Rello, L., & Baeza-Yates, R. (2013). Good fonts for dyslexia. *Proceedings of the 15th International ACM SIGACCESS Conference on Computers and Accessibility*, Article 14.
- Galliussi, J., Perondi, L., Chia, G., Gerbino, W., & Bernardis, P. (2020). Inter-letter spacing, inter-word spacing, and font with dyslexia-friendly features: Testing text readability in people with and without dyslexia. *Annals of Dyslexia*, 70(1), 141-152.
- Franzen, L., Stark, Z., & Johnson, A. (2019). The dyslexia font OpenDyslexic facilitates visual processing of text and improves reading comprehension in adult dyslexia. *Annals of Eye Science*, 4, AB004. [Conference abstract; not full peer-reviewed paper]
- Zorzi, M., et al. (2012). Extra-large letter spacing improves reading in dyslexia. *Proceedings of the National Academy of Sciences*, 109(28), 11455-11459.
- Rello, L., Pielot, M., & Marcos, M.-C. (2016). Make it big! The effect of font size and line spacing on online readability. *Proceedings of the 2016 CHI Conference on Human Factors in Computing Systems*, 3637-3648.
- Machado, M. A., et al. (2025). A preliminary evaluation of Dyslexie's influence on adult dyslexic reading performance. *Behavior Analysis in Practice*.
- Duranovic, M., Senka, S., & Babic-Gavric, B. (2018). Influence of increased letter spacing and font type on the reading ability of dyslexic children. *Annals of Dyslexia*, 68(3), 218-228.
- International Dyslexia Association. (2025). *Dyslexia Definition & Understanding*. https://dyslexiaida.org/
- Braille Institute. (2025). *Atkinson Hyperlegible Font*. https://www.brailleinstitute.org/freefont/
- OpenDyslexic. (n.d.). *OpenDyslexic Font*. https://opendyslexic.org/
- Lexend. (n.d.). *The Lexend Font Family*. https://www.lexend.com/
