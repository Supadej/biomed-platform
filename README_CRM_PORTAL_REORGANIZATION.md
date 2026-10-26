# Staff Portal CRM reorganization

- The separate CRM application menu has been removed from platform headers. Direct entry to the old CRM homepage redirects to Staff Portal. The backend, bridge UI and original CRM code remain in this archive to avoid loss of data or breaking integrations.
- Staff Portal > Overview > Calendar: native event log with date/time/location.
- Staff Portal > CRM > External Helpdesk: separate external case log.
- Staff Portal > CRM > Project & Activity: project and activity register.
- Staff Portal > CRM > Sales Plan: manual opportunities and import of locally bridged Biomed IS documents. Source references are deduplicated; source amounts are not authoritative financial values.
- Incentive scheme target association is rejected unless positive target exists and actual/target >= 100%. The current implementation attaches an eligible scheme to the first unlinked opportunity owned by the signed-in user.

**Implementation boundary:** New portal registers use existing Staff Portal storage and basic portal-role checks, not the original CRM relational database. Automatic source detection reads the Biomed IS snapshots already bridged into Staff Portal, and is not a background sync. No existing CRM tickets/projects/leads have been migrated. The old CRM backend is intentionally retained for compatibility. Review fine-grained permissions and end-to-end workflows before production deployment.
