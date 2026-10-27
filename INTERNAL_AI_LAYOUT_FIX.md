# Internal AI layout correction

The widget used an aside element, inheriting global sidebar height, positioning,
background and mobile-drawer styles in Budgeting and Biomed IS. Its wrapper now
uses a div, with explicit floating-widget dimensions and spacing. The inner
heading also uses a scoped div to avoid global header rules.

Hidden states are enforced; the closed widget occupies only its launcher.
The open panel is constrained to viewport width and height, with scrolling chat
history and settings. The script reference is refreshed in all three applications.

JavaScript syntax, login translation regression, and six AI backend tests pass.
Desktop, tablet, and mobile visual testing on Railway remains outstanding.
Deploy preserving the existing production database, then hard refresh.
