# Corpus Expansion Candidates

Merged from four research runs (Claude Research, ChatGPT Deep
Research x3). Deduplicated by URL. One domain per category.
Verified = fetched as HTML by research tool. High-confidence =
confirmed via search snippets but blocked by robots.txt on
automated fetch.

See docs/eval-cheatsheet.md for the screening and fixture-
addition workflow.

## Screening Checklist (per candidate)

- [ ] URL resolves and returns full HTML (no JS-only rendering)
- [ ] No login wall or paywall
- [ ] Article is prose-dominant (not image-heavy or step-list-heavy)
- [ ] Source word count is reasonable (not extreme chrome bloat)
- [ ] Decant output passes visual review
- [ ] Baselined via --baseline interactive mode before committing

## Candidates

| ID | slug | url | cat | status | notes |
|----|------|-----|-----|--------|-------|
| C01 | npr-iran-war | https://www.npr.org/2026/03/16/nx-s1-5749333/iran-war-gasoline-prices-day-17 | 1 | verified | NPR custom CMS, embedded audio, clean semantic HTML |
| C02 | aljazeera-iran-economy | https://www.aljazeera.com/news/2026/3/16/the-tell-tale-signs-how-bad-has-the-iran-war-hit-the-global-economy | 1 | verified | Al Jazeera WordPress, inline images, H2 subheadings |
| C03 | abcnews-state-laws | https://abcnews.go.com/Politics/notable-new-state-laws-taking-effect-2026-cover/story?id=128811522 | 1 | verified | Disney CMS, SSR, distinct sections per law |
| C04 | apnews-immigration | https://apnews.com/article/trump-immigration-law-enforcement-ice-fa3d8b65321fb207dfbcfec4dae08b1e | 1 | verified | Wire service, minimal chrome |
| C07 | newsweek-cholesterol | https://www.newsweek.com/americas-cholesterol-guidelines-updated-acc-aha-11679770 | 1 | verified | News-magazine template, published/updated metadata |
| C08 | startribune-mayo-clinic | https://www.startribune.com/mayo-clinic-reports-record-147b-profit-in-2025/601593203 | 1 | high-confidence | Local/regional news, metered paywall |
| C09 | longreads-best-2025 | https://longreads.com/2025/12/15/best-of-2025-our-most-popular-originals-of-the-year/ | 2 | verified | WordPress editorial, prose commentary |
| C10 | atavist-castles | https://magazine.atavist.com/2020/castles-in-the-sky-san-francisco-denmark-diary-love-mystery | 2 | verified | Magazine chrome, subscribe/archive modules |
| C11 | restofworld-tiger | https://restofworld.org/2025/tiger-global-unicorn-investment-crash/ | 2 | verified | Hero illustration, author credits, sectioned layout |
| C12 | marshallproject-prison | https://www.themarshallproject.org/2026/03/10/prison-music-texas-rodeo-redemption-songs | 2 | verified | Investigative, newsletter CTAs, newsroom nav |
| C13 | bellingcat-buk | https://www.bellingcat.com/news/europe/2014/11/08/origin-of-the-separatists-buk-a-bellingcat-investigation/ | 2 | verified | Investigation post, deep-linking, report structure |
| C14 | noemamag-superintelligence | https://www.noemamag.com/the-politics-of-superintelligence/ | 3 | verified | Intellectual magazine, 2500+ words |
| C15 | brookings-china | https://www.brookings.edu/articles/how-china-reads-the-2025-u-s-national-security-strategy/ | 3 | verified | Think-tank policy essay |
| C16 | jacobin-shelley | https://jacobin.com/2022/09/percy-bysshe-shelley-poetry-politics-revolution | 3 | verified | Political/cultural argument, dense paragraphing |
| C17 | playerstribune-green | https://www.theplayerstribune.com/aj-green-nfl-football-rondale-moore | 3 | verified | First-person essay, strong branding elements |
| C18 | medlineplus-metformin | https://medlineplus.gov/druginfo/meds/a696005.html | 4 | verified | Drug monograph, rigid Q&A sections, dosage info, .gov template |
| C19 | drugs-metformin | https://www.drugs.com/metformin.html | 4 | verified | Tabbed sections, dosage tables, ad-heavy, inline FAQ accordion |
| C20 | healthdirect-arthritis | https://www.healthdirect.gov.au/rheumatoid-arthritis | 4 | verified | Australian gov health, symptom checker integration |
| C21 | webmd-diabetes | https://www.webmd.com/diabetes/metformin-side-effects | 4 | verified | Heavy nav chrome, ads, bulleted side-effects, adversarial fixture |
| C22 | mind-depression | https://www.mind.org.uk/information-support/types-of-mental-health-problems/depression/about-depression/ | 4 | high-confidence | UK mental health charity, multi-page chapter nav, video |
| C23 | nami-bipolar | https://www.nami.org/About-Mental-Illness/Mental-Health-Conditions/Bipolar-Disorder/ | 4 | high-confidence | US mental health nonprofit, crisis helpline callout |
| C24 | readingrockets-dyslexia | https://www.readingrockets.org/topics/dyslexia/articles/accommodating-students-dyslexia-all-classroom-settings | 5 | verified | SEN accommodations, prose-heavy, structured lists |
| C25 | openstax-photosynthesis | https://openstax.org/books/biology-ap-courses/pages/8-1-overview-of-photosynthesis | 5 | verified | OER textbook chapter, learning objectives, diagrams |
| C26 | khanacademy-blog | https://blog.khanacademy.org/khan-academy-goes-way-beyond-math-new-courses-launch-for-2024-school-year-in-stem-humanities-computer-science-and-more/ | 5 | verified | WordPress blog (not SPA), educational context |
| C27 | edutopia-strategies | https://www.edutopia.org/article/selecting-instructional-strategies-students-can-master/ | 5 | verified | Teaching strategies, topic tags, byline |
| C29 | scholastic-reading | https://www.scholastic.com/teachers/teaching-tools/articles/literacy/science-of-reading-resources.html | 5 | verified | Teacher resource, Science of Reading |
| C30 | colorincolorado-ell | https://www.colorincolorado.org/article/what-ell-educator | 5 | verified | Bilingual education, ELL-specific content |
| C31 | bbcgoodfood-victoria | https://www.bbcgoodfood.com/recipes/classic-victoria-sandwich-recipe | 6 | verified | Editorial recipe, skip-to-ingredients anchor, star ratings |
| C33 | sallysbaking-applepie | https://sallysbakingaddiction.com/apple-pie-recipe/ | 6 | verified | Ad-heavy blog, jump-to-recipe, dense cross-linking before card |
| C34 | pinchofyum-tikka | https://pinchofyum.com/chicken-tikka-masala | 6 | verified | Ratings widget, structured recipe card after long article text |
| C35 | giallozafferano-tiramisu | https://www.giallozafferano.com/recipes/Tiramisu.html | 6 | verified | Italian publisher in English, language switch, calorie panel |
| C36 | minimalistbaker-cake | https://minimalistbaker.com/one-bowl-vegan-chocolate-cake/ | 6 | verified | Vegan blog, disclosures, vote-based rating metadata |
| C37 | damndelicious-pasta | https://damndelicious.net/2014/10/11/one-pot-garlic-parmesan-pasta/ | 6 | verified | Long preamble, star rating count, video section header |
| C39 | instructables-elwire | https://www.instructables.com/Beginners-Guide-to-Start-an-EL-Wire-Project/ | 7 | verified | Step-based CMS, embedded images per step |
| C40 | thisoldhouse-diy | https://www.thisoldhouse.com/home-improvement/25-diy-fundamentals | 7 | verified | 25 numbered skills, home-improvement publisher |
| C41 | nerdwallet-will | https://www.nerdwallet.com/article/investing/estate-planning/how-to-write-a-will | 7 | high-confidence | Financial how-to, 7-step guide |
| C42 | nps-climate-action | https://www.nps.gov/pore/learn/nature/climatechange_action_home.htm | 7 | verified | Gov practical advice, step-like sections, nested lists |
| C43 | ssa-disability | https://www.ssa.gov/applyfordisability/ | 7 | verified | Structured apply guidance, process steps, prominent nav |
| C44 | canada-ai-guidance | https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/responsible-use-ai/guide-use-generative-ai.html | 8 | verified | Canadian federal guidance, WET framework, breadcrumbs |
| C45 | epa-climate-actions | https://www.epa.gov/climate-change/climate-change-regulatory-actions-and-initiatives | 8 | verified | US EPA, prose across sectors, section headers |
| C46 | australia-impact | https://oia.pmc.gov.au/resources/guidance-impact-analysis/australian-government-guide-policy-impact-analysis | 8 | verified | Australian gov, policy framework, downloadable attachments |
| C48 | travel-state-passports | https://travel.state.gov/content/travel/en/passports/how-apply.html | 8 | verified | Multi-step passport instructions, eligibility subsections |
| C49 | eu-commission-apply | https://commission.europa.eu/funding-tenders/how-apply/application-process_en | 8 | verified | EU institutional, layered structure, policy nav |
| C50 | insideclimate-2025 | https://insideclimatenews.org/news/28122025/2025-year-in-climate/ | 9 | verified | Long-form year-in-review, free, no paywall |
| C51 | nasa-globalwarming | https://www.earthobservatory.nasa.gov/Features/GlobalWarming/page5.php | 9 | verified | Multi-page/paginated explainer, continuity stitching test |
| C52 | sciencenews-animals | https://www.sciencenews.org/article/favorite-animal-stories-2025 | 9 | high-confidence | Nature writing, metered paywall, full text in HTML |
| C54 | history-constitution | https://www.history.com/topics/united-states-constitution/constitution | 10 | verified | History.com reference, extensive prose, inline video links |
| C55 | mentalfloss-hysteria | https://www.mentalfloss.com/history/dark-history-of-hysteria | 10 | verified | History explainer, extended prose, historical analysis |
| C56 | jstor-footnotes | https://daily.jstor.org/historys-footnotes/ | 10 | verified | Academic-adjacent explainer, peer-reviewed source links |
| C57 | iwm-dunkirk | https://www.iwm.org.uk/history/what-you-need-to-know-about-the-dunkirk-evacuations | 10 | verified | Museum explainer, image galleries, narrative subheads |
| C58 | loc-magna-carta | https://www.loc.gov/exhibits/magna-carta-muse-and-mentor/executive-power.html | 10 | verified | Exhibit-style, scrolling sections, exhibit nav chrome |
| C59 | stanford-epistemology | https://plato.stanford.edu/entries/epistemology/ | 11 | verified | Stanford Encyclopedia, extensive TOC, bibliography, academic tools |
| C60 | worldhistory-rome | https://www.worldhistory.org/Rome/ | 11 | verified | World History Encyclopedia, timeline sidebar, citation formatter |
| C61 | newworldencyclopedia | https://www.newworldencyclopedia.org/entry/Encyclopedia | 11 | verified | MediaWiki-style, inline citations, Wikipedia-fork |
| C62 | simple-wiki-photosynthesis | https://simple.wikipedia.org/wiki/Photosynthesis | 11 | verified | Simple English Wikipedia, simplified vocabulary |
| C63 | scholarpedia-deeplearning | http://www.scholarpedia.org/article/Deep_Learning | 11 | verified | Peer-reviewed wiki, math notation, 888+ references |
| C66 | copyright-gov-faq | https://www.copyright.gov/help/faq/ | 12 | verified | Gov FAQ, TOC-based hub, multi-page pattern |
| C67 | apple-support-2fa | https://support.apple.com/en-in/102641 | 12 | verified | Help article, step numbering, inline callouts |
| C68 | netflix-help | https://help.netflix.com/en/node/22 | 12 | verified | Short sections, inline answers, account warnings |
| C69 | mozilla-sync | https://support.mozilla.org/en-US/kb/how-do-i-set-sync-my-computer | 12 | verified | KB layout, on-page TOC, product badges, feedback widget |
| C70 | dropbox-2fa | https://help.dropbox.com/account-access/enable-2-factor-authentication | 12 | verified | In-this-article nav, icon callouts, security warnings |
| C71 | github-2fa | https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication | 12 | verified | Docs/help hybrid, sticky TOC, admonitions, code tokens |
| C72 | fightcancer-faq | https://www.fightcancer.org/about-our-organization/frequently-asked-questions | 12 | verified | Nonprofit FAQ, Q:/A: prefixes, bilingual toggle |
| C73 | cancer-org-risk | https://www.cancer.org/cancer/risk-prevention/understanding-cancer-risk/questions.html | 12 | verified | Health-org FAQ, heading-based Q&A, heavy nav chrome |
| C74 | zapier-note-apps | https://zapier.com/blog/best-note-taking-apps/ | 13 | verified | Software review roundup, prose-heavy, no product cards |
| C75 | tomsguide-espresso | https://www.tomsguide.com/home/coffee-makers/best-espresso-machines | 13 | verified | Classic roundup, product cards, buy buttons, pros/cons |
| C76 | outdoorgearlab-boots | https://www.outdoorgearlab.com/topics/shoes-and-boots/best-hiking-boots | 13 | verified | 41 items lab-tested, scoring methodology, comparison table |
| C78 | caranddriver-landrover | https://www.caranddriver.com/reviews/a70679541/2026-land-rover-discovery-test/ | 13 | verified | Auto review, VERDICT callout, spec blocks, CTA modules |
| C79 | pitchfork-kimgordon | https://pitchfork.com/reviews/albums/kim-gordon-play-me/ | 13 | verified | Album review, score widget, taxonomy nav elements |
| C80 | goodhousekeeping-robot | https://www.goodhousekeeping.com/home-products/a40510449/litter-robot-4-review/ | 13 | verified | Home product review, jump-to nav, question subsections |
| C81 | coffeegeek-espresso | https://coffeegeek.com/opinions/state-of-coffee/the-best-espresso-machine/ | 13 | verified | Essay-style review, opinionated, no product cards |
| C82 | lonelyplanet-summer | https://www.lonelyplanet.com/articles/where-to-go-in-summer | 14 | verified | Destination prose, SSR |
| C84 | timeout-london | https://www.timeout.com/london/things-to-do/101-things-to-do-in-london | 14 | verified | Large listicle, at-a-glance blocks, many short sections |
| C85 | unesco-heritage | https://whc.unesco.org/en/list/426/ | 14 | verified | UNESCO site detail, tabbed sections, templated blocks |
| C86 | si-wembanyama | https://www.si.com/nba/spurs/looks-like-spurs-latest-dynasty-is-forming-victor-wembanyama | 15 | verified | SI feature, locker room reporting, Maven CMS |
| C87 | cbssports-marchmadness | https://www.cbssports.com/college-basketball/news/2026-ncaa-tournament-cheat-sheet-stats-march-madness-history-bracket-picks/ | 15 | verified | Long-form analysis, statistical breakdowns, heavy nav chrome |
| C88 | deadspin-nfl-combine | https://deadspin.com/nfl-combine-winners-and-losers-who-boosted-their-2026-draft-stock/ | 15 | verified | Player-by-player analysis, embedded images, new CMS |
| C89 | yahoo-sports-ncaa | https://sports.yahoo.com/mens-college-basketball/article/2026-ncaa-tournament-will-feature-new-potentially-crucial-element-the-coachs-challenge-183306667.html | 15 | verified | Narrative feature, coach quotes, trending sidebar |
| C90 | bleacherreport-bracket | https://bleacherreport.com/articles/25407372-ncaa-tournament-2026-predictions-mens-sweet-16-bracket-after-selection-sunday | 15 | verified | Region-by-region breakdown, embedded bracket graphics |
| C91 | foxsports-nfl | https://www.foxsports.com/stories/nfl/2026-nfl-offseason-buzz-rumors | 15 | verified | Team-by-team sections, cross-promotion widgets |
| C92 | pmc-open-access | https://pmc.ncbi.nlm.nih.gov/articles/PMC8221498/ | 16 | verified | Systematic review, PRISMA diagrams, data tables, CC-BY |
| C93 | elife-editorial | https://elifesciences.org/articles/102432 | 16 | verified | eLife editorial, DOI, article metrics, open-access badge |
| C94 | frontiers-metrics | https://frontiersin.org/articles/10.3389/frma.2022.943932/full | 16 | verified | Full structured sections, data figures, CC-BY |
| C95 | nature-comms | https://www.nature.com/articles/s41467-024-50779-y | 16 | verified | Nature Communications OA, abstract, figures, methods |
| C96 | cochrane-evidence | https://www.cochrane.org/evidence | 16 | verified | Cochrane overview, systematic reviews, plain language summaries |
| C97 | arxiv-html | https://arxiv.org/html/2510.15842v1 | 16 | high-confidence | arXiv HTML paper, single-page, sections, references |
