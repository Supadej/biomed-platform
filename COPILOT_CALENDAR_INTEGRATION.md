# Copilot Staff Portal Calendar tools (OpenAI)

This version connects Calendar instead of just describing its interface.

Enable:
1. Deploy source keeping production database, volume, API keys and encryption secret.
2. Open /copilot-access.html (AI Chat Management > My Copilot access).
3. Enable Staff Portal, Read my authorised Staff Portal Calendar (OpenAI), and
   Prepare Calendar drafts for confirmation (OpenAI). Save my access.
4. Admin employee limits must allow these; the employee role must have
   ai.internal.use, crm_view, crm.events.view and, for drafts, crm.events.create.
5. Select the saved personal or company OpenAI key in Copilot.
6. Ask 'Show my calendar tomorrow' or 'Prepare a meeting on 2 November 2026
   from 10:00 to 11:00 at Biomed office.'
7. Review the draft and click Confirm save to Calendar. A success message
   includes the actual Calendar Event ID. No automatic saving by the model.

Capabilities:
- Uses native CRM Calendar permission checks and own/all event visibility.
- Reads at most 100 visible events in a requested range of up to 93 days.
  Only event ID, title, date/time and all-day status are returned to OpenAI.
- Drafts events for the signed-in employee only; no reassignment, invites,
  collaborators, product/contact linking, edit/delete or recurrence in this version.
- Free-text location is stored in event Description; this is not a LocationID.
- Model tools cannot save events. Only the explicit authenticated confirmation
  endpoint can save; it rechecks permissions and owner and uses native Calendar save.
- Drafts expire after 30 minutes. Repeated confirmation does not duplicate an event.
- Pending drafts reappear on opening Copilot. Drafts and access preferences persist.
- Current role/session and admin limits are checked again before every model tool.
- Bangkok timezone is explicit. Missing times/duration should be clarified.
- Other systems still have summary-only access, not automatic record changes.
- Gemini does not receive Calendar tools or Calendar records.

Validation:
Five Calendar tests cover actual native event save after confirmation, duplicate
prevention, ownership, expiry, own-only reads, date ranges, permission revocation,
and a mocked Responses function-call loop. Existing access, AI and Gemini tests
and JavaScript syntax checks pass. No live OpenAI tool call or browser/Railway
end-to-end test was performed.

OpenAI reference:
https://developers.openai.com/api/docs/guides/function-calling
