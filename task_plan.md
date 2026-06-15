# Task Plan

Goal: implement a Windows-friendly course project prototype for multi-agent low-overhead communication, state transfer, and shared memory.

## Phases

- [x] Inspect available course files and current workspace.
- [x] Create a standalone demo project.
- [x] Implement backend workflow and shared memory.
- [x] Implement frontend dashboard.
- [x] Add report, PPT, assignment, and demo materials.
- [x] Verify with tests and run instructions.

## Decisions

- Use Python + FastAPI for the backend.
- Use SQLite for shared memory and run history.
- Use a vanilla HTML/CSS/JS dashboard to keep setup simple.
- Agent behavior is rule-based, not real LLM calls.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
| CodeGraph not initialized | Checked CodeGraph status | Continue with native file tools because this is a new project scaffold. |
| SQLite insert result was not returned | First pytest run | Read the inserted row inside the same connection before returning. |
| Short Chinese task similarity was too strict | API smoke test | Lowered memory match threshold and added course-task keywords. |
