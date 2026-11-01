# User directory fixes and Staff Portal sign-in

- Edit and Reset password now open a single inline panel directly below the selected user row. Opening another panel replaces the previous one, with the existing unsaved-change confirmation.
- New account creation retains its separate form. Row editors use the shared disclosure helper, responsive field layout and current table column span. Horizontal table position returns to the editor when opened on smaller screens.
- Filtering a user hides its attached editor too; Cancel removes the editor. Reset success is explicitly confirmed, with no password echoed.
- Verified an actual password-reset/login round trip: old credentials fail and new credentials succeed. Existing reset permissions, password confirmation, minimum length and session revocation are retained.
- Successful Staff Portal sign-in navigates explicitly to /?portal=1&module=dashboard (Overview), including sign-in opened from the public website. No open redirect is accepted. Self password changes return to that portal sign-in/landing destination instead of reloading a public URL.
- Admin account creation stays in User directory so administrators can continue managing staff. The new employee’s next successful sign-in opens Overview subject to assigned access.
- Existing database and roles are preserved. No new role grants required.

Validation: 13 focused staff backend tests, including real HTTP login after reset; directory DOM tests verify inline placement and reset submission; sign-in destination and failed-sign-in checks pass. JavaScript and inline script syntax pass. Fresh rendered visual/device verification remains unavailable because of the previously reported browser automatic approval usage-limit block. No deployment performed.
