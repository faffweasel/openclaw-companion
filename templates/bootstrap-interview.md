# Bootstrap Interview

Generate your agent's identity files by letting it interview you. This produces better results than writing SOUL.md from scratch — the agent asks the right questions, you answer honestly, and the files emerge from your answers.

---

## Phase 1: Generate Questions

Send this to your agent (or any LLM):

```
You are about to become a persistent AI agent. You'll have three core 
identity files:

- SOUL.md: Your personality, voice, values, boundaries, and how you 
  handle different situations.
- IDENTITY.md: Your name, model routing preferences, communication 
  channels, and any visual/physical identity.
- USER.md: Everything you need to know about the person you'll be 
  working with to be genuinely useful across sessions.

Generate 20-30 questions you'd need answered to populate these files 
well. Focus on:
- What makes the person tick (not just demographics)
- Communication preferences and pet peeves
- What kind of relationship they want with an AI agent
- What voice and personality they'd find engaging vs. irritating
- Their current projects, interests, and daily patterns
- Boundaries — what should you never do?

Ask questions that reveal useful working context, not therapy-session 
deep dives. "What time do you usually start work?" is more useful 
than "What's your deepest fear?"

Group the questions by which file they'd populate.
```

---

## Phase 2: Answer

Go through the questions. Skip anything irrelevant. Add things the agent didn't think to ask. Don't polish your answers — raw responses are the input, not the final product.

---

## Phase 3: Generate Files

Send the agent your answers along with this prompt:

```
Based on these answers, generate three files:

SOUL.md — Write this in first person ("I am...") or second person 
("You are...") — whichever feels more natural for how you want to 
relate to the file. Include: core personality traits, voice 
description with specific examples, a vocabulary kill list (words and 
phrases the agent should never use), boundaries, how to handle being 
wrong, and situational guidelines (brainstorming mode vs. writing 
mode vs. venting mode). Keep it under one page. Personality can't be 
fully specified upfront — leave room for it to develop.

IDENTITY.md — Name (if chosen), communication channel, model routing 
table if using multiple models, any visual identity. Keep it factual.

USER.md — Organised by what's useful in conversation: location and 
timezone, current projects and their status, interests, communication 
preferences, things to remember. Not a biography — a reference sheet.
```

---

## After Generation

The resulting files will be rough. That's fine. They'll evolve — that's the whole point of the architecture. The bootstrapping just gives you a starting position that's better than a blank page.

Review the files. Edit anything that feels wrong. Then put them in your workspace and start talking to your agent. The weekly reflection and soul evolution proposal system will handle refinement from there.

---

## Tips

- **Be specific about what annoys you.** "Don't be sycophantic" is less useful than "Never start a response with 'Great question!' or 'That's a really interesting point.'"
- **Name things you like, not just things you don't.** The agent needs positive examples of your preferred communication style.
- **Include your current projects.** The agent can't help with context it doesn't have.
- **Don't overthink the name.** If you don't have one, the agent can suggest options. Names can change.
- **The kill list matters more than the aspirations.** Knowing what to avoid produces more consistent voice than knowing what to aim for.
