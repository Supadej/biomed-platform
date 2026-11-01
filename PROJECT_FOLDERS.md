# Project folders

Project & Activity now opens with project folders before activity stages.
Create or edit a folder using its Name and Description. Open stages to enter
that project's activity board; use Project folders to return. New activities
and stages inherit the opened project. Existing projects and activities are
retained; no database migration or reset is needed.

Permissions use the existing CRM Projects, Project stages and Project activities
view/create/edit/delete controls in Roles & responsibilities. Users without
Projects view retain their existing activity access; they cannot manage folders.

Delete folder shows stage and visible activity counts and requires confirmation.
Deletion requires delete permission and record scope for every affected child.
It soft-deletes activities, their collaborator/contact assignments, stages and
the project in one transaction, retaining audit records. Unrelated projects
remain unchanged. Hidden children, stale counts/versions, bridge snapshots or
external references stop deletion. External links, including legacy Sales Plan
ProjectID references, must be reassigned first. The ordinary project form delete
route directs users to the folder deletion flow.

Local tests cover folder counts, linked deletion and assignment cleanup,
permission rejection, changed counts and rollback/external link protection.
DOM tests exercise opening folders and switching the activity views. Live
Railway rendering and production data have not been verified.
