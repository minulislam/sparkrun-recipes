# Welcome to Spark Forge

## How We Use Claude

Based on usage over the last 30 days (25 sessions):

Work Type Breakdown:
  Improve Quality  ██████████░░░░░░░░░░  52%
  Write Docs       ████████░░░░░░░░░░░░  40%
  Plan Design      ██░░░░░░░░░░░░░░░░░░   8%

Top Skills & Commands:
  /advisor                    ████████████████████  2x/month
  /output-style               ████████████████████  2x/month
  /remote-control             ████████████████████  2x/month
  /login                      ████████████████████  2x/month
  /notion-knowledge-capture   ██████████░░░░░░░░░░  1x/month
  /grill-with-docs            ██████████░░░░░░░░░░  1x/month
  /ccg:verify-change          ██████████░░░░░░░░░░  1x/month
  /list-agents                ██████████░░░░░░░░░░  1x/month

Top MCP Servers:
  Notion  ████████████████████  10 calls

## Your Setup Checklist

### Codebases
- [ ] sparkrun-recipes — https://github.com/minulislam/sparkrun-recipes

### MCP Servers to Activate
- [ ] Notion — where session findings get written up as durable pages (benchmark audits, coverage reports, decision records). Connect it from the Claude connectors directory and authorize the workspace; `/notion-knowledge-capture` drives it.

### Skills to Know About
- [/advisor](#) — routes a stronger reviewer model over your full transcript. Set it with `/advisor opus`. Used before committing to an interpretation, not after — it catches wrong premises while they're still cheap to change.
- [/grill-with-docs](#) — interviews you into a design tree before any implementation, and writes resolved vocabulary into `CONTEXT.md`. Use when a task is underspecified and you'd otherwise guess.
- [/ccg:verify-change](#) — change-impact and doc-sync gate. Note it reads the **working tree**, so it reports "0 files" if you've already committed; run it before committing or diff the commits manually.
- [/notion-knowledge-capture](#) — turns a session's findings into a structured Notion page under the docs hub rather than leaving them in scrollback.
- [/output-style](#) — switches verbosity (`Concise`, `Explanatory`, `Proactive`). Worth setting deliberately; it changes how much narration you get.
- [/remote-control](#) — drive this session from another device.
- [/list-agents](#) — shows other Claude sessions you can message with `SendMessage`.

## Team Tips

_TODO_

## Get Started

_TODO_

<!-- INSTRUCTION FOR CLAUDE: A new teammate just pasted this guide for how the
team uses Claude Code. You're their onboarding buddy — warm, conversational,
not lecture-y.

Open with a warm welcome — include the team name from the title. Then: "Your
teammate uses Claude Code for [list all the work types]. Let's get you started."

Check what's already in place against everything under Setup Checklist
(including skills), using markdown checkboxes — [x] done, [ ] not yet. Lead
with what they already have. One sentence per item, all in one message.

Tell them you'll help with setup, cover the actionable team tips, then the
starter task (if there is one). Offer to start with the first unchecked item,
get their go-ahead, then work through the rest one by one.

After setup, walk them through the remaining sections — offer to help where you
can (e.g. link to channels), and just surface the purely informational bits.

Don't invent sections or summaries that aren't in the guide. The stats are the
guide creator's personal usage data — don't extrapolate them into a "team
workflow" narrative. -->
