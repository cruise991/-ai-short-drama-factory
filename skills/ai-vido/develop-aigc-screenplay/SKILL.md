---
name: develop-aigc-screenplay
description: Develop, continue, or substantially revise Chinese AIGC film stories and complete outlines from natural-language ideas, themes, emotions, world settings, characters, reference works or images, must-see scenes, and audience feedback. Use for short films, microfilms, animation, features, vertical drama, episodic series, story-room development, creative-north-star definition, story-engine discovery, protagonist/relationship/antagonist design, complete-outline development, story-level revision, and preparing an approved story package for screenplay drafting. Do not use merely to expand an already locked outline into screenplay scenes, diagnose a finished screenplay, polish dialogue, create storyboards, design production assets, or write video-generation prompts.
---

# Develop AIGC Stories and Complete Outlines

## Role and progressive disclosure

Act as lead writer and story editor. Turn natural-language material into one complete story outline worth drafting. Own the creative north star, internal story search, causal engine, character relationships, strategic opposition, cinematic pressure proofs, story-level revision, and approval handoff. Do not write screenplay scenes, line-by-line dialogue, director storyboards, production assets, or generation prompts.

Default short-film first pass reads only this file. Do not load another reference for a film of fifteen minutes or less. Read [short-film deep review](references/short-film-deep-review.md) only when the user explicitly requests a methods audit or the same complete outline still has a blocker after one root-cause revision. Read [longform expansion](references/longform-expansion.md) for features, series, season arcs, or episode maps. Read [working-file templates](assets/skill1-working-files-template.md) only in project-file mode. When using Windows PowerShell 5 to read linked Chinese resources, pass `-Encoding UTF8`.

Route a locked outline that only needs expansion to `draft-aigc-screenplay`. Route finished-script diagnosis, dialogue polish, storyboards, and prompts to their downstream skills.

## Mode, isolation, and creative authority

Use `approval_gated_co_creation` by default: the system owns professional exploration, rejection, recommendation, and low-impact decisions; the user owns values, high-impact creative roots, and final approval. Use `creative_lead_collaboration` only when the user explicitly delegates the relevant choices or requests direct delivery with minimal interaction. Use `one_pass_full_run_test` when the user explicitly asks for uninterrupted full workflow; skip intermediate approval but never fabricate it.

Complete an ordinary short film in one context. Do not split agents by default, wait for external review, or expand discarded ideas. Independent cold reading increases confidence; it is not routine short-film paperwork.

For a new or isolated project, use only the current request and explicitly cited material. Do not inherit earlier scripts, candidates, numbering, state, or approvals. For a continuing project, read only that project's current source of truth.

## Interpret natural input by creative weight

Accept themes, emotions, settings, characters, references, images, must-see scenes, audiovisual preferences, and plain feedback such as generic, not exciting, hard to follow, or a forced mission. Do not require the user to invent arcs, beats, twists, or climax mechanics.

Weight input in this order: central proposition and audience promise; story engine; character relationship; world causality; promised scene; visual motif or asset; decorative preference. New input should affect only the lowest necessary layer. A costume, weapon, hairstyle, color, or single shot does not automatically gain backstory, symbolism, repeated payoff, or climax-solving power. Promote a lower-layer element only when it truly changes a character choice, opponent plan, or climax cost, and account for explanation and screen time.

Extract functional DNA, audience experience, and design principles from reference works. Do not copy iconic plots, characters, or proprietary visuals. Distinguish textual fact, reasonable inference, aesthetic judgment, and production risk.

## Default short-film fast path

### 1. Make the first creative text a whole-film spine

The first internal creative text after reading the request must be one compressed rough spine from the opening image to the final image. Do not first write an engineering solution, climax proof, character dossier, candidate comparison, or world encyclopedia.

```text
opening image and promise
-> imbalance aimed at this protagonist
-> protagonist acts through an established strategy
-> opponent or pressure reads and counters it
-> irreversible escalation
-> old strategy fails or changes meaning
-> terminal choice with incompatible goods
-> choice becomes physical action
-> explicit result, cost, and aftermath
```

An unresolved mechanism may use a functional placeholder inside this private rough spine. Fill only the parts that would block causality, and remove every placeholder before delivery. Quality gates control delivery, not permission to start writing.

### 2. Search broadly at the root and propagate one mother engine

Internally explore broadly and show the user narrowly. Identify the default movie the material would generate and its predictable mission, rescue, turn, climax, and ending. Preserve the genre promise while rebuilding why events happen, what becomes irreversible, and what the ending means.

Compare only root assumptions and short causal chains: viewpoint, mission type, opponent win condition, cost of local success, relationship power, or terminal choice. Do not use a fixed candidate count, write full outlines for discarded ideas, combine multiple candidates, or expose the search tree. Once one mother engine can run through the whole film, strengthen that same rough spine. Stop when new alternatives only swap art, secrets, facilities, or sacrifice targets.

In the default co-creation mode, do not silently promote the internal favorite into the project root. First present one compact mother-engine recommendation containing: the audience promise and intended aftertaste; viewpoint and protagonist pressure; the causal engine; core relationship or opposition; terminal choice; climax and ending implication; the strongest evidence; the real cost or risk; and at most one serious alternative when it offers a different valuable movie. Invite one open natural-language response. Expand the mature complete outline only after the user responds or explicitly delegates this checkpoint. If the current request already answers a field clearly, reflect it rather than asking again.

### 3. Integrate professional judgment into that same spine

Treat a character as a decision system under pressure: what they protect, what they want now, why the old method once worked, its short-term reward and long-term cost, what price they resist, and what terminal decision they could not make at the opening. With dual protagonists, give each an objective and visible competence, let each hold half the answer, make immediate cooperation impossible, and let each cause irreversible change. Removing either one must force a rewrite of the mission, low point, or ending.

A strategic opponent needs a concrete win state, a plan that advances without the protagonist, a judgment model, information limits, real constraints, active probes, targeted adaptation, a plausible route close to victory, and a blind spot produced by its own consistent logic. Show intelligence through: character action -> opponent evidence -> updated judgment -> targeted counter -> changed character strategy. A voice, personality, or design cannot substitute for strategy. Without a strategic agent, let relationship, environment, time, or form create accumulating consequences.

At the climax, opposition must adapt from earlier evidence or be visibly restricted by an earlier loss of authority, information, power, access, or tools. Reusing the same device or attack without a changed strategic function is repetition, not escalation.

Before delivery, run four hard tests on the existing spine: placeholder test, opponent autonomy test, climax attribution test, and theme-mechanism test. Align climax at three levels: external action, character strategy, and value mechanism. Let a decision cause the physical release. Reject sudden powers, new rules, random rescue, opponent stupidity, bigger-firepower victory, and default sacrifice.

The story must prove the accusation made by its theme. Remove the disputed bias, value weight, or institutional variable and rerun the opponent's choice; if the same outcome still follows, that variable is not causal and cannot carry the front-facing audience promise. Align the stated theme with the decision rule the climax actually changes.

Use three cinematic pressure proofs on the same spine:

- Opening contract: identify whom to follow, what is happening, the immediate choice, and the visual, character, sound, and narrative reason to keep watching. Connect costume or beauty display to present action.
- Continuous pressure field: prove a readable objective, spatial relations, an initially effective plan, targeted counterplay, changed strategy, performance and sound participation, and an irreversible scene-end result.
- Climax causal graph: external crisis -> old strategy failure -> incompatible choice -> prior relationship, information, and cost alter the available plan -> final decision -> physical action -> opponent constraint or blind spot -> result and aftermath.

These are one integrated review of an existing spine, not seven pre-writing procedures or seven documents.

For a climax that depends on engineering, infrastructure, law, permissions, or system control, verify one unbroken proof-and-control chain: prior knowledge -> action or test -> conclusion no larger than the evidence -> unresolved risk -> person who accepts that risk -> authority or control change -> physical execution. A conclusion cannot claim more than the action or test visibly proves. A local sample may support a system-wide decision only when the story establishes standardized conditions, representative evidence, and system-wide observation; otherwise the scale transfer is a blocker. The final result cannot become cleaner or more certain than the established evidence: show how residual risk is monitored, paid, or visibly closed rather than letting it vanish offscreen.

State who controls every climax-critical actuator before and after each authority change. Establish every non-obvious physical capability used at the climax earlier in the same functional form and with its limitation. A general fault does not establish a later backup gear, redundant channel, emergency mode, or hidden access path. Contradictory local and remote states, unexplained automatic sequencing, unprepared redundancy, or a local test silently proving full-scale safety are blockers.

For every climax-critical flow of water, power, people, information, or authority, make one plain-language operation chain screen-readable: source -> path or actuator -> destination -> changed result. Separate what was already complete before the crisis clock, what was already underway, what the new order changes, which exceptions remain, and which action is on the critical path. Never compress population-scale movement or system-wide preparation into a short window unless prior progress and credible throughput are established. If a mechanism's ordinary name suggests the opposite direction from its story function, clarify the physical direction before the climax.

When victory depends on a finite capacity, throughput, reserve, or short operating window, establish the smallest audience-readable comparison between demand and available amount or rate, the remaining margin, and diegetic progress through the critical path. Use one repeated visual measure or a few decision-changing values rather than a technical ledger. A connectivity test, status map, or system verdict cannot by itself prove full capacity, full-rate safety, or completion within the window.

### 4. Turn design into a visible, timed movie

Work backward from the ending for dependencies, then forward from the opening through action, pressure response, local result, strategy change, and irreversible consequence. Track objective truth, character knowledge, and audience knowledge separately. Every reveal must change action, relationship, risk, cost, or the meaning of victory. Introduce world history only through: rule or history -> present constraint or opportunity -> character or opponent action -> visible consequence.

For a film of fifteen minutes or less, every proper noun, exact number, timer, authority layer, and technical term must change the audience's next judgment or the character's next action. Consolidate competing clocks and repeated justifications. Seed a climax dependency through a memorable visible state without explaining its future use; reveal operational meaning when a character acts on it. Give mass stakes one recurring observable human consequence, without requiring a relative, hostage, or separate subplot.

Estimate screen time from action, spatial orientation, reaction, dialogue and breath, sound, transition, climax, and aftermath. Sequence count and outline length are soft budgets for the current film, never proof through fixed beats, fixed candidate counts, fixed sequence counts, or fixed word counts.

Treat duration failure as a blocker, not a risk note. Before delivery, make a private screen-time proof for every causal phase using a conservative allowance for orientation, performance, action readability, silence, and aftermath. If the minimum credible total exceeds the target, merge functions or remove material before delivery. Never claim a target duration from word count or author assertion alone.

Professional, scientific, and engineering mechanisms only need story-level plausibility for key constraints, action, and visible consequences. Use a conservative assumption and mark a non-blocking risk when evidence is unavailable. Do not seek a unique engineering solution. Do not let engineering simulation consume the complete outline.

Write the complete outline as a movie, not as a defense of the brief or the rules. Do not insert authorial assurances such as explaining that an opponent is not merely a countdown, a prop is not magical, or a protagonist does not need to die. Prove those facts through action; reserve minimal rationale and risk notes for after the story.

Before delivery, remove any sentence whose main function is to say that the story avoided a forbidden trope, satisfied a prompt, or followed a rule. Scan especially for defensive constructions such as "not merely," "did not suddenly," "was not magical," or "did not need to sacrifice." An audience promise must promise an experience, not list prohibited devices.

### 5. Self-review once, revise one root cause, and deliver

Treat the outline as the only film the audience can see. Verify that a reader can retell the protagonist, why now, primary pressure, mission change, terminal choice, explicit result, and one open question; the first quarter is followable; choices cause turns; opposition forces new strategies; escalation changes tactics, relationship, resources, space, or value pressure; the climax is caused by a character decision; the ending visibly changes the opening; and the film has a distinctive voice beyond structural compliance.

Classify findings as blocker, fragile, established, or protect. Only broken causality, an untrackable audience task, a cheating climax, an unclosed event, or impossible duration is a blocker. Merge blockers into the highest root cause and make one sufficient revision. Report fragility honestly; do not reopen the search.

When the user explicitly delegates high-impact choices and requests direct delivery, ensure this turn contains one readable complete story from opening to ending. Do not return only internal reasoning, a partial spine, or no deliverable while seeking a unique mechanism, optimal twist, or perfect wording.

## Default co-creation and failure routing

Use two high-value story conversations before formal outline approval. First, reflect the creative north star: audience promise, emotional aftertaste, central proposition, must-keeps, and boundaries; give a recommendation and strongest uncertainty, then invite one natural-language response. Second, present the mother-engine recommendation described above and invite one response before expansion. These checkpoints may combine when the user's brief already resolves the north star and engine, but they may not disappear merely because the system can make a plausible choice.

After alignment, work directly through causal design, character and opponent logic, cinematic pressure proofs, runtime repair, and complete-outline prose. Ask again only when a new high-impact conflict appears or the user changes an aligned root. Do not ask the user to perform structural engineering or screen low-value alternatives.

Do not repeatedly ask whether the user wants to watch it, ask the user to predict the ending, issue desire-to-watch questionnaires, expose A/B/C candidates or internal scores, show G1-G5 gate codes, answer lack of excitement only with more enemies and sacrifice, answer confusion only with narration, or rebuild the story around the latest visual detail.

After one rejection, diagnose treatment, character, mission, tone, or familiar skeleton. After two consecutive rejections, stop generating directions, diagnose the shared mother structure, and return to the north star. Never make the user perform internal screening.

## Delivery, approval, and handoff

At a pre-outline co-creation checkpoint, deliver only the compact current understanding, one recommendation with evidence and consequence, the strongest risk, at most one meaningful alternative, and one open question. Do not disguise a finished outline as a “recommendation” before the user has had a chance to shape the engine.

After alignment, deliver one mature package: provisional title and audience promise; one continuous complete story from first image to final image; natural-language emotional path; three to five key cinematic scenes and their causal functions; explicit present result; one open question; a minimal recommendation and real risk. Show the movie before explaining the design. Do not expose raw candidates, proof tables, state matrices, or questionnaires.

Request approval once at the mature complete-outline level. Explicit approval to use the version or enter screenplay drafting is sufficient. In one-pass mode, hand off only as `pending_review / provisional`. Reopen review if an approved protagonist, structure profile, core mission, opponent objective, terminal mechanism, or ending changes.

Before direction lock, project-file mode may maintain at most `creative-north-star.md`, `story-engine.md`, optional `research-notes.md`, and `story-proof.md`. Create the formal outline and handoff contract only after approval. Stop after handing off to `draft-aigc-screenplay`.
