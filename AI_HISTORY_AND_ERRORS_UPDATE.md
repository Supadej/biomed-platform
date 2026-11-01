# Internal Copilot refinement
Navy header, teal actions, pale backgrounds and borders align with the workspace.
User messages render immediately. The server commits them before requesting an AI
reply; failed remote calls retain both the message and a readable error in history.
Error entries are excluded from subsequent OpenAI input. Error responses distinguish
invalid credentials, quota, rate limits, model access and connection failures
without displaying upstream response bodies or secrets.

Company website key: OPENAI_API_KEY powers public visitor chat.
Company internal key: BIOMED_INTERNAL_OPENAI_API_KEY powers staff Copilot when
enabled by an admin and selected by the employee. Usage is charged to the API
project owning that key. Personal keys belong to the employee's API project.

Seven AI tests pass, including failed-request persistence and retry context.
JavaScript syntax and archive integrity pass. No live OpenAI request or Railway
browser test was performed. Existing missing messages cannot be reconstructed.
Keep your production database/volume and existing encryption secret on deployment.
