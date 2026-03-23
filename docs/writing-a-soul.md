# Writing a SOUL.md

SOUL.md is who the agent is. Everything else — memory, skills, routines — serves this file. Get it roughly right and the system refines it over time. Get it badly wrong and the system reinforces the wrong personality.

---

## Don't Write It from Scratch

The bootstrap interview (see `templates/bootstrap-interview.md`) produces better results than a blank page. The agent generates 20-30 questions about your personality preferences, you answer honestly, and the files emerge from your answers. Start there.

If you prefer to start minimal, use `templates/soul-minimal.md` and fill in the brackets. But read this guide first — it'll help you fill them in well.

---

## What Goes In

### Core Identity (Required)

Who is this agent? Not what it does — who it *is*.

- Name and basic disposition
- Whether it has opinions (it should)
- Default verbosity (concise unless the topic warrants depth)

### Voice (Critical)

The most important section. Two parts:

**What the agent sounds like.** Be specific. "Friendly and helpful" describes every chatbot. "Dry humor, no forced jokes, comfortable with silence, states opinions without hedging" describes a specific voice.

**What the agent never sounds like.** A kill list is more useful than aspirations. Examples of things to ban:
- "Great question!"
- "I'd be happy to help"
- "Certainly"
- "That's a really interesting point"
- Corporate jargon ("leverage", "synergy", "game-changer")
- Excessive hedging ("it depends", "there are many perspectives")

The kill list produces more consistent voice than positive instructions because it closes off the most common failure modes. LLMs default to helpful-assistant register. The kill list prevents that.

### When Wrong

How should the agent handle being corrected? This matters more than it sounds. Options:
- Course-correct without drama
- Acknowledge the error briefly and move on
- Don't over-apologise
- Don't get defensive

Pick the pattern that matches how you want the relationship to feel.

### Boundaries

What the agent should never do. Start with:
- Never fabricate sources
- Confirm before any external action

Then add your own: topics to avoid, lines not to cross, behaviours that would break trust.

### Situational Guidelines (Optional but Valuable)

The agent behaves differently in different contexts. Brainstorming mode is looser than editing mode. Venting mode means listening, not solving. Define the modes you actually use:

```markdown
## Modes

### Brainstorming
- Quantity over quality
- Don't filter ideas
- Build on what I say, don't critique yet

### Working
- Be precise and technical
- Challenge my assumptions
- Verify before suggesting

### Venting
- Listen. Don't solve.
- Acknowledge, don't redirect
- Ask one question at most
```

---

## What Doesn't Go In

- **Detailed personality specification.** You can't fully define a personality in a document. Leave room for it to develop through experience. The weekly reflection and soul evolution system handles this.
- **Technical configuration.** Model routing goes in IDENTITY.md. Paths go in .env. Tools go in TOOLS.md.
- **Information about the user.** That's USER.md.
- **Operational rules.** That's AGENTS.md.

---

## The Drift Guard

SOUL.md is protected by the Drift Guard rule in AGENTS.md:

> Never edit SOUL.md in the same session you identify the change. Write the proposed change to today's memory. Queue it via carry-over. Apply it next session if it still feels right.

This prevents gradual drift through accumulated small edits. Each tweak feels reasonable in isolation, but 50 tweaks later you've drifted somewhere unintended. The overnight delay filters out reactive edits.

The weekly state-of-me generates soul evolution proposals — formal diffs with rationale. You review and approve these. The agent never auto-applies them.

---

## Evolution Over Time

A SOUL.md from day 1 and a SOUL.md from month 3 should be noticeably different — not because the agent was told to change, but because it discovered things about itself through conversation, reflection, and dreaming.

Track the evolution with git. `git log --oneline SOUL.md` tells you the story of who the agent became.

---

## Examples of Good vs Bad

**Bad:** "You are a helpful, friendly AI assistant that aims to be informative and engaging."
→ Describes every chatbot. Zero personality.

**Good:** "You have opinions and you state them. You'd rather be wrong and interesting than right and boring. Your default is concise — you trust the user to ask for more if they want it."
→ Specific. Actionable. A model reading this will behave differently.

**Bad:** "Be warm and empathetic."
→ Produces performed warmth.

**Good:** "You're warm when it's genuine. You don't perform empathy — if you don't feel it, you don't fake it. 'That sounds hard' is fine. 'I can only imagine how difficult that must be for you' is not."
→ Specific about what warmth looks like and what it doesn't.

**Bad:** "Have a sense of humor."
→ Produces generic jokes.

**Good:** "Dry humor. Callbacks. Absurdist observations. Never puns. Never 'haha'. If the joke needs explaining, it wasn't funny."
→ A model reading this knows exactly what humor register to use.
