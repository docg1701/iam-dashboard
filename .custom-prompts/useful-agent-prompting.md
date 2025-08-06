# Custom command-line prompts to use with BMAD agents

## DEV Agent
### Develop Story from start minding the BMAD Method:

```markdown
*develop-story according to the BMAD Method. Read core-config. Read docs/architecture/index.md and then read all needed docs/architecture/*.md. If your are coding Frontend, read every UI/UX file in docs/architecture. Spawn 2 agents in parallel to speed it up.
``` 

### Develop Story Again fixing errors and bugs:

```markdown
[ULTRATHINK] *develop-story according to the BMAD Method. Read core-config. Read docs/architecture/index.md and then all needed docs/architecture/*.md. Spawn 2 agents in parallel. And fix all the the remaning issues of docs/stories/STORY-FILENAME
``` 

### Make the Agent do a through review and honest report about his own work

```markdown
[ULTRATHINK] I need you to do a real and honest through assessment of your work in this last story you developed. Do all the checking, testing and step-by-step reading. Don't assume anything, test and prove it. Be very true about it and then fix the report section of the story file.
```

## QA Agent

### Make a proper QA assesment
```markdown
[ULTRATHINK] *review docs/stories/FILENAME. I need you to do a real and honest through assessment of the DEV Agent's work in this story. Do all the checking, testing and step-by-step reading. Don't assume anything, test and prove it. Be very true about it.
```
