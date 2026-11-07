# Ticket template

Copy this structure exactly. Translate headings and the Given/When/Then keywords when the ticket is not in English. Replace every `<…>`.

````markdown
# <KEY>-<NNN> · <Summary: short imperative title, as in the Jira "Summary" field>

| Field | Value |
|---|---|
| Type | Story · Task · Bug |
| Project folder | `<folder>/` (`<subfolder>/` if any) |
| Status | Draft, pending review |
| Created | <YYYY-MM-DD> |
| Labels | <e.g. api, text2sql, security> |

## User story

**As a** <role>, **I want** <capability>, **so that** <benefit>.

## Context

<2-5 sentences: what exists today, what is wrong or missing, why now. Link the files and docs read.>

**References read:** <files/docs that shaped the ACs; in travel-agency, the class references of the phase>

**Deviations from the reference pattern:** <only in travel-agency or where a reference exists; "None" otherwise>

## Scope

**In scope**
- <…>

**Out of scope**
- <…>

## Acceptance criteria

### Happy path

**AC-1 — <outcome>**
- **Given** <starting state>
- **When** <action>
- **Then** <observable result>
- **And** <further check on the same outcome>

### Edge cases

**AC-2 — <outcome>**
- **Given** …
- **When** …
- **Then** …

### Error states

**AC-n — <outcome>**
- **Given** …
- **When** …
- **Then** <what the caller sees>
- **And** <what does not change>

### Non-functional

<ACs in GWT, or "None for this ticket.">

## Definition of Done

- [ ] Every AC is covered by a passing automated test *(code tickets)* / checked by the review or command named in the AC *(data or document tickets)*
- [ ] The full test suite of the project is green
- [ ] Lint, format and type checks pass (where the project has them)
- [ ] `AGENTS.md` of the folder updated if the change makes it outdated
- [ ] Commits without AI attribution

## Assumptions and open questions

**Assumptions**
- <decision taken without explicit confirmation, and why>

**Open questions**
- <question still to answer before or during development, or "None">
````

## Pasting into Jira

- **Summary**: the title after the `·`.
- **Description**: *User story*, *Context* and *Scope*.
- **Acceptance Criteria** field (or the end of the description if there is none): the *Acceptance criteria* section as is.
- *Definition of Done* and *Assumptions and open questions*: end of the description, or a comment.
