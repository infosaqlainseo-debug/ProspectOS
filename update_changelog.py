import re

with open("CHANGELOG.md", "r") as f:
    content = f.read()

phase_19_text = """## [Phase 1.9] - 2026-10-09
### Added
- **Workflow Automation Engine**
- Created `Workflow` and `WorkflowRun` models to control automated progression through system stages.
- Added `/workflows` endpoints and Next.js frontend visualization UI.
- Built `WorkflowOrchestrator` to automatically enqueue ARQ tasks according to the configured state machine.
- Updated all intelligence ARQ tasks to trigger the Orchestrator without active polling.
- Fully verified end-to-end execution and transitions on local test databases using Docker Compose.

"""

content = content.replace("## [Unreleased]\n\n### Added\n- Initial project assessment and repository inspection (repository was empty).\n\n", "## [Unreleased]\n\n" + phase_19_text)

with open("CHANGELOG.md", "w") as f:
    f.write(content)
