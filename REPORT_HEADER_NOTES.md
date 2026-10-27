# Standard report header

The supplied Biomed Diagnostics logo is embedded without changing its artwork or pixels. Its transparent padding is cropped by the SVG viewport only. The ISO seal uses a transparent-background edit, with its circular white ring retained.

The built-in image editor was used for the ISO image. Edit prompt: remove only the light blue rectangular area outside the circular rim; preserve the seal design, colors, proportions and lettering, including MEDICAL DEVICES, QUALITY MANAGEMENT and ISO 13485:2016; output true transparency with no shadows or added graphics.

Assets: assets/report-biomed-logo.png and assets/report-iso13485-transparent.png. The shared portrait and landscape SVG headers embed both PNGs, making each header self-contained. report-branding.js is the common header/printing helper; report-branding.json records the company copy and physical dimensions.

The logos retain the same physical size on A4 portrait and A4 landscape pages. The common header repeats in the print margin on continuation pages, while item-grid column headers repeat within the document. Company identity/address copy is retained from the previous report header. Transaction calculations, signatures and document data are unchanged.

The document print button waits for the header asset to load. Browser printing of IS, Budget and active Staff Portal views also uses the common branding. CSV exports and downloaded receipt images are data/source attachments rather than formatted report pages.
