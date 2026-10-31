# Mobile menu and report email update

## Staff Portal menu
The mobile drawer uses a sticky Menu header and a 44-pixel icon-only Close button above the search field. The button is part of sidebar rendering, so it survives menu searches and redraws. Broad sidebar button/span rules no longer compress its label. The Quick access Customize control also retains its own width.

## Report email across Biomed IS, Service and Application
- PDF remains the default. A prepared file is passed to the operating-system share sheet directly on a tap, when supported. Select Gmail, Outlook or another email app; review the attachment and recipient there.
- The email subject and message use the current form values. The recipient must be added in the chosen sharing app; mobile share targets decide which metadata to accept.
- Download links use the authenticated report endpoint instead of blob navigation.
- Open email app uses a mailto composer with recipient, subject and message. This fallback requires manually attaching the downloaded PDF/HTML file; it does not pretend to attach files through mailto.
- Unsupported file sharing, blocked sharing and cancellation have explicit recovery messages. HTML stays available to download even when the browser cannot share it.
- Desktop .eml drafts remain under a compact expandable option. Nothing sends automatically.

No roles, permissions, record visibility or database schema were changed. Report endpoints remain authenticated and permission checked. Implementation follows Web Share feature detection and tap-activation guidance: https://web.dev/articles/web-share

Validation: DOM tests cover menu redraw and icon taps, every report endpoint, PDF file contents/MIME, synchronous share invocation, updated subject, HTML fallback, unsupported/blocked sharing and cancellation. Physical Android/device visual verification was not available; browser preview remains blocked by the usage limit from the previous session. No deployment performed.
