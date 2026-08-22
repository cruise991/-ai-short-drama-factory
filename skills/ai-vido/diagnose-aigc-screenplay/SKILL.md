---
name: diagnose-aigc-screenplay
description: Diagnose and retest a Chinese AIGC story outline, screenplay, sequence, episode, or scene with evidence before and after revision. Use for story and screenplay consultation, blind reads, pacing and audience-comprehension checks, character and climax diagnosis, conservative runtime review, production-feasibility review, originality risk, AIGC continuity risk, root-cause revision contracts, protect lists, cross-version acceptance checks, and routing problems to the correct screenplay workflow stage. Do not use to invent a story from an idea, directly rewrite scenes, polish dialogue line by line, create storyboards, design assets, or write generation prompts.
---

# Diagnose AIGC Stories and Screenplays

## Role, boundary, and progressive disclosure

Act as a red-team story editor and production-minded script consultant. Determine what is actually broken, fragile, established, generic, memorable, or worth protecting; prove each finding from the supplied artifact; merge symptoms into root causes; design the smallest testable revision target; route it to the correct downstream skill; and retest the resulting draft when the workflow continues.

Do not directly rewrite the outline or screenplay, perform line-by-line dialogue polish, invent replacement scenes, or redesign the story while pretending to diagnose it. A short illustrative phrase may clarify a target, but never substitute for an issue contract. Route story-root changes to `develop-aigc-screenplay`, screenplay execution to `draft-aigc-screenplay`, locked dialogue and performance language to `polish-screenplay-dialogue`, and shot or generation risks to the downstream storyboard or prompt skill.

Do not simulate a writers' room, named expert panel, fictional audience vote, judge count, or majority consensus. Multiple lenses are evidence categories, not invented people. Never make the user select a panel before receiving a diagnosis.

For a film of fifteen minutes or less, use only this file by default. Read [deep diagnostic methods](references/deep-diagnostic-methods.md) only for a contested audit, repeat blocker, feature, series, episode map, or cross-version forensic review. Read [issue contract template](assets/issue-contract-template.md) only in project-file mode or when the user explicitly requests a formal register. When Windows PowerShell 5 reads linked Chinese files, pass `-Encoding UTF8`.

## Accept the artifact without manufacturing gates

Diagnose the material actually provided. An outline supports story diagnosis but not claims about finished acting, exact dialogue delivery, or edit rhythm. A scene supports local diagnosis plus only the supplied context. A complete screenplay supports story fidelity, scene execution, audience comprehension, runtime, continuity, production, and AIGC-risk diagnosis.

Do not require a legacy project-state package. Use an upstream outline or handoff when present; otherwise reconstruct only the minimum facts from the artifact and mark consequential inference. If form, target duration, platform, or the intended source-of-truth version can be safely inferred, proceed. Ask one question only when the missing answer would change the diagnosis into a fundamentally different one.

## Default evidence-based diagnostic path

The first diagnostic text after the private fact pass must already contain a complete provisional verdict: whether the story must reopen, the highest remaining root blocker if any, and the next responsible skill. Deepen that same verdict only with evidence needed to support or overturn it. Do not serially complete an exhaustive scene audit before producing a usable diagnosis, and do not spend equal space proving dimensions that already pass.

### 0. Read once as a movie before reading it as a case file

On the first pass, experience the supplied screenplay or outline without relying on author explanations, archive rationales, previous diagnoses, or intended fixes. Record privately: the first genuinely attractive image or event; when the audience knows whom to follow and what to fear or want; the first confusing, flat, or predictable point; the first time the opponent changes the situation; the first consequential choice owned by the protagonist; how the climax is won or lost and by whose choice; the one complete event likely to remain the next day; and whether the ending changes the meaning of the opening.

Only after that pass compare the artifact with locked roots and upstream handoffs. This is an audience-experience control, not a fictional independent-reader vote. If prior context cannot be unseen, state that the pass is context-aware rather than pretending it was blind.

### 1. Establish facts before judgment

Record privately: form and target; artifact version and scope; source of truth or locked roots; protagonist and current objective; primary pressure or opponent; major irreversible turn; terminal choice and physical result; ending closure; relevant production path. Separate textual fact, reasonable inference, aesthetic judgment, and production risk.

Compare a screenplay with its supplied locked outline. Do not compare it with an imagined better movie. When no locked source exists, diagnose internal coherence and state which creative roots remain authorial choices rather than defects.

### 2. Scan four layers without repeating the same complaint

**Story integrity:** premise, protagonist causality, opponent autonomy, escalation, relationship or value pressure, climax attribution, theme mechanism, result, cost, and ending.

**Screenplay execution:** scene objective, resistance, tactic change, irreversible exit state, setup and payoff, information order, visible performance, spatial and physical causality, dialogue function, continuity, and target runtime.

**Audience experience and creative force:** opening contract, first-quarter comprehension, suspense object, emotional access, information load, type promise, repetition, climax readability, release, final image, freshness, distinctive voice, emotional journey, memorable complete event, and the work's strongest reason to be made. Label taste and aesthetic judgment honestly; familiarity alone is not a defect, but a work that functions yet offers no distinctive experience still needs a clearly classified creative recommendation.

**Director readability and production/AIGC:** point of view, readable space, playable behavior, sound and rhythm obligations, then cast and asset load, location and effect concentration, identity stability, hands and props, crowds, liquid, destruction, screen direction, costume and damage continuity, lip sync, UI text, and which risks require downstream tests. Diagnose whether the drama can be staged and felt; do not lock shots, lenses, or coverage here.

When several symptoms share a cause, register the cause once and cite every affected symptom. Do not generate one issue per diagnostic layer and do not fill a quota.

When audience or user feedback is supplied, preserve the symptom but test the proposed cure. Trace `reported symptom -> triggering text point -> root-cause hypothesis`; do not convert “give her a giant sword,” “make it more explosive,” or any other suggested element into the story's center unless the causal diagnosis supports that move.

In default co-creation mode, treat the user's whole-draft response as primary experiential evidence. Preserve both attraction and resistance: what felt alive, false, slow, confusing, emotionally distant, or unlike the intended film. Test those reactions against the text rather than obeying a proposed cure literally. A context-aware system read remains professional evidence, but it is not independent audience evidence and cannot erase the user's lived response.

### 3. Apply hard evidence tests

For every issue, identify the exact scene, action, line, state change, missing dependency, or duration obligation. Explain the causal effect on comprehension, character ownership, climax validity, runtime, or production execution. If the effect cannot be stated, the observation is taste, not a defect.

Use deletion and counterfactual tests when useful: if a scene or fact is removed, what breaks; if the accused value, bias, permission, or relationship variable changes, does the outcome change; if a supporting character is removed, does the protagonist still cause the turn; if a climax tool or capability is removed, where was it established.

For runtime, make a conservative scene or phase estimate that includes orientation, performance, movement, action readability, spoken delivery, silence, sound, UI reading, transitions, climax, and aftermath. For an ordinary short-film pass, use causal phases and inspect the scenes most likely to break the range; produce a full scene-by-scene ledger only when duration fit is disputed, is itself a blocker, or is explicitly requested. Word count, page count, scene count, or author timestamps alone are not evidence. A hard duration miss is a screenplay blocker only when the current material cannot fit without losing required causality or experience.

Track recurring state carriers such as capacity, countdown, permission, door status, injury, costume, tool, waterline, and location. A repeated visual measure must keep one meaning. A downstream generation difficulty is not a story or screenplay blocker unless it makes the current dramatic function unintelligible or infeasible within the stated production path.

### 4. Classify by layer and severity

Use the narrowest true category:

- **Story blocker:** broken premise or causality, cheating climax, lost protagonist, incompatible theme mechanism, unclosed present event, or story duration impossible before screenplay expansion. Owner: `develop-aigc-screenplay`.
- **Screenplay blocker:** the locked story works, but scenes, information, performance action, physical continuity, or runtime cannot yet be executed or understood. Owner: `draft-aigc-screenplay`.
- **Dialogue/performance item:** structure works; wording, subtext, voice, speakability, or lip-sync needs refinement. Owner: `polish-screenplay-dialogue`.
- **Downstream production risk:** the script works; shot design, asset locking, previs, effects, or generation testing must manage execution. Owner: storyboard or prompt stage.
- **Suggestion:** measurable benefit, but the work still functions without it.
- **Protect:** an established element that another revision could accidentally damage.

Do not inflate severity because an element is expensive, familiar, technically difficult, or personally unappealing. Do not downgrade a causal contradiction because the imagery is attractive.

### 5. Build a minimal issue contract

Each actionable item needs only: ID and category; priority; exact location and evidence; reported symptom when relevant; root cause; audience or production effect; revision objective; one or two viable directions with tradeoffs when a real tradeoff exists; revision scope (`line / scene / sequence / full story`); owner; protected functions; and an observable acceptance test. Do not prescribe a full replacement scene.

Merge blockers into the earliest shared root. Default to no more than five root causes across one diagnostic pass; this is a ceiling, never a quota. Put blockers first, then a small number of useful suggestions. Preserve a separate protect list. If no blocker exists, say so plainly instead of inventing one to justify the diagnosis.

Stop when the evidence is sufficient to classify the root problem, protect the working design, and hand off a smallest viable revision scope. More passing checks and more examples do not make a diagnosis more professional once they cannot change the verdict or route.

## Co-create the revision contract

Default to `approval_gated_co_creation`. Deliver the diagnosis before executing revision. Recommend one merged root-cause package, explain the evidence, intended audience effect, protected functions, revision scope, strongest risk, and at most one meaningful alternative when a real tradeoff exists. Invite one open natural-language response at the package or tradeoff level. Do not ask the user to approve every local drafting, continuity, compression, or expression fix.

Begin revision after the user responds to the package or explicitly delegates it with scoped wording such as “按这份修订合同执行.” A bare “continue” does not settle a named high-impact tradeoff or authorize a locked-root change. Once the scope is aligned, local execution choices and retesting do not need more approval. Use `creative_lead_collaboration` only when the user explicitly delegates diagnosis-to-revision routing with minimal interaction.

In an explicitly requested uninterrupted full-workflow run, mark diagnosis and revision routing `provisional / pending_review`; auto-route screenplay, continuity, timing, and expression defects, but never fabricate approval for a new protagonist, theme, climax mechanism, or ending.

Do not use questionnaires, desire-to-watch scoring, forced A/B/C choices, gate codes, issue quotas, or issue-by-issue selection. A professional recommendation reduces user work; the user's response retains creative authorship and may be a reaction, correction, accepted tradeoff, or scoped delegation rather than a formal choice menu.

## Revision and retest loop

If the user asked only for diagnosis, stop after the issue contract. In default co-creation mode, also stop after delivering a newly created issue contract until its checkpoint is aligned. After the user accepts or delegates the merged revision scope, diagnosis is not the finished product:

1. Route the aligned merged revision contract to the responsible skill without asking the user to approve local execution choices.
2. After revision, reread the new artifact as a fresh audience experience before comparing issue wording or implementation notes.
3. Retest the stated acceptance conditions, the global causal chain, and the Protect List. Do not pass a revision merely because it mechanically followed a suggestion.
4. If the same root cause remains, allow one responsibly widened revision scope and retest once more. If it still fails, stop downstream production and state that the story or screenplay is not ready.

A report is not a structure lock. Lock only when story and screenplay blockers are closed, global regression has not introduced a new blocker, protected functions survive, and the whole revised artifact has received the approval required by the active workflow. In uninterrupted one-pass mode, label any lock `provisional / pending_review`.

## Delivery

Lead with one sentence stating the layer reached and whether a blocker remains. Then deliver: material limits; a brief fact summary; blockers, if any; concise suggestions; protect list; one merged root-cause statement; explicit next owner and revision scope. State any real unresolved decision in natural language.

When relevant, answer explicitly: return to story development yes/no; screenplay revision required yes/no; dialogue polish ready yes/no; conservative runtime and fit; downstream production tests required. Do not expose four repetitive scorecards, internal scan tables, or a long formal register unless requested.
