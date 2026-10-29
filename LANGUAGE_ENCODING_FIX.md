# Language button encoding
HTML declares UTF-8 before scripts. Text, JavaScript, and JSON static responses
explicitly declare UTF-8. The shared language script uses Unicode escapes so Thai
button labels are independent of script decoding guesses. Its URL is versioned
to refresh cached copies.

Local HTTP checks confirmed UTF-8 on Biomed IS, Financial, and the shared script.
EN/TH switching and login recovery regressions pass. Railway visual testing is
not yet performed. Deploy preserving the production database, then hard refresh.
