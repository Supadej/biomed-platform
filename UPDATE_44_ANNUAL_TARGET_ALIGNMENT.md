# Annual target alignment

The Annual target header and numeric inputs now share the same centered alignment and symmetric cell padding as the monthly columns. Alignment is explicitly attached to the column, so it survives column reordering and translated labels. Number formatting, annual spreading and saved values are unchanged.

Browser checks at 320, 390, 768, 1024, 1440 and 2048 pixels verify header/input centering, matching center coordinates, column reordering and unchanged monthly centering. No database migration or reset is required. Deploy the complete package to update the site.
