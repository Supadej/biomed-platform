var url = ""; // empty string for production

const currentYear = new Date().getFullYear();
const Translator = [];

// ==================== COLOR DATA (merged from colors.json) ====================
const colorsData = {
    "red": [
        { "name": "RED", "code": "#D0312D" },
        { "name": "CHERRY RED", "code": "#990F02" },
        { "name": "ROSE", "code": "#E3242B" },
        { "name": "JAM", "code": "#60100B" },
        { "name": "MERLOT", "code": "#541E1B" },
        { "name": "GARNET", "code": "#610C04" },
        { "name": "CRIMSON", "code": "#B90E0A" },
        { "name": "RUBY", "code": "#900603" },
        { "name": "SCARLET", "code": "#900D09" },
        { "name": "WINE", "code": "#4E0707" },
        { "name": "BRICK", "code": "#7E2811" },
        { "name": "APPLE", "code": "#A91B0D" },
        { "name": "MAHOGANY", "code": "#420C09" },
        { "name": "BLOOD", "code": "#710C04" },
        { "name": "SANGRIA RED", "code": "#5E1916" },
        { "name": "BERRY", "code": "#7A1712" },
        { "name": "CURRANT", "code": "#680C07" },
        { "name": "BLUSH RED", "code": "#BC544B" },
        { "name": "CANDY", "code": "#D21404" },
        { "name": "LIPSTICK", "code": "#9B1003" },
        { "name": "CARMINE", "code": "#960018" },
        { "name": "PERSIAN RED", "code": "#CA3433" },
        { "name": "VERMILION", "code": "#7E191B" },
        { "name": "IMPERIAL RED", "code": "#ED2939" },
        { "name": "INDIAN RED", "code": "#CD5C5C" },
        { "name": "CHILI RED", "code": "#C21807" },
        { "name": "MAROON", "code": "#800000" },
        { "name": "FIRE BRICK", "code": "#B22222" },
        { "name": "DESIRE", "code": "#EA3C53" },
        { "name": "RASPBERRY", "code": "#D21F3C" },
        { "name": "CANDY APPLE", "code": "#FF0800" },
        { "name": "HIBISCUS", "code": "#B43757" },
        { "name": "U.S. FLAG", "code": "#BF0A30" },
        { "name": "FERRARI", "code": "#FF2800" },
        { "name": "BURGUNDY", "code": "#8D021F" },
        { "name": "DARK RED", "code": "#8B0000" },
        { "name": "PRISMATIC RED", "code": "#D03D33" },
        { "name": "49ERS RED", "code": "#AA0000" },
        { "name": "CARDINALS RED", "code": "#BD2031" },
        { "name": "AJAX RED", "code": "#D2122E" },
        { "name": "ALABAMA CRIMSON", "code": "#9E1B32" },
        { "name": "ALIZARIN CRIMSON", "code": "#E32636" },
        { "name": "AMARANTH RED", "code": "#F4364C" },
        { "name": "AMERICAN ROSE", "code": "#FF033E" },
        { "name": "ANGELS RED", "code": "#BA0021" },
        { "name": "ARSENAL RED", "code": "#DB0007" },
        { "name": "AUBURN RED", "code": "#A52A2A" },
        { "name": "BU SCARLET", "code": "#CC0000" },
        { "name": "BILLS RED", "code": "#C60C30" },
        { "name": "BITTERSWEET SHIMMER", "code": "#BF4F51" }
    ],
    "orange": [
        { "name": "ORANGE", "code": "#ED7014" },
        { "name": "TANGERINE", "code": "#FA8128" },
        { "name": "MERIGOLD", "code": "#FCAE1E" },
        { "name": "CIDER", "code": "#B56727" },
        { "name": "RUST", "code": "#8D4004" },
        { "name": "GINGER", "code": "#BE5504" },
        { "name": "TIGER", "code": "#FC6A03" },
        { "name": "FIRE", "code": "#DD571C" },
        { "name": "BRONZE", "code": "#B2560D" },
        { "name": "CANTALOUPE", "code": "#FDA172" },
        { "name": "APRICOT", "code": "#ED820E" },
        { "name": "CLAY", "code": "#80400B" },
        { "name": "HONEY", "code": "#EC9706" },
        { "name": "CARROT", "code": "#ED7117" },
        { "name": "SQUASH", "code": "#C95B0C" },
        { "name": "SPICE", "code": "#7A3803" },
        { "name": "MARMALADE", "code": "#D16002" },
        { "name": "AMBER", "code": "#893101" },
        { "name": "SANDSTONE", "code": "#D67229" },
        { "name": "YAM", "code": "#CC5801" },
        { "name": "TANGELO", "code": "#FC4C02" },
        { "name": "FLAME", "code": "#E34A27" },
        { "name": "FULVOUS", "code": "#E68000" },
        { "name": "DARK ORANGE", "code": "#FF8C00" },
        { "name": "VIVID ORANGE", "code": "#FF5E0E" },
        { "name": "ORANGE-RED", "code": "#FF4500" },
        { "name": "METALLIC ORANGE", "code": "#E26310" },
        { "name": "PUMPKIN", "code": "#F5761A" },
        { "name": "SMASHED PUMPKIN", "code": "#FD673A" },
        { "name": "INTERNATIONAL ORANGE", "code": "#FF4F00" },
        { "name": "SPANISH ORANGE", "code": "#F06105" },
        { "name": "PRINCETON ORANGE", "code": "#FF8F00" },
        { "name": "DEEP SAFFRON", "code": "#FFA52C" },
        { "name": "ALLOY ORANGE", "code": "#C35214" },
        { "name": "HALLOWEEN ORANGE", "code": "#EE5921" },
        { "name": "GAMBOGE", "code": "#E89611" },
        { "name": "MEDIUM VERMILION", "code": "#CF5B2E" },
        { "name": "PASTEL ORANGE", "code": "#FEBA4F" },
        { "name": "PHILIPPINE ORANGE", "code": "#F26E01" },
        { "name": "ROYAL ORANGE", "code": "#FF9944" },
        { "name": "CORAL", "code": "#FF7F50" },
        { "name": "DARK CORAL", "code": "#D75341" },
        { "name": "CADMIUM ORANGE", "code": "#E6812F" },
        { "name": "RAJAH", "code": "#FABA5F" },
        { "name": "MANGO TANGO", "code": "#FB8842" },
        { "name": "ORANGE PEEL", "code": "#FF9F00" },
        { "name": "VIVID TANGELO", "code": "#EC7625" },
        { "name": "PERSIMMON", "code": "#EC5800" },
        { "name": "BROWNS ORANGE", "code": "#FF3C00" },
        { "name": "BURNT ORANGE", "code": "#CC5500" }
    ],
    "yellow": [
        { "name": "TAN", "code": "#E6DBAC" },
        { "name": "BEIGE", "code": "#EEDC9A" },
        { "name": "MACAROON", "code": "#F9E076" },
        { "name": "HAZEL WOOD", "code": "#C9BB8E" },
        { "name": "GRANOLA", "code": "#D6B85A" },
        { "name": "OAT", "code": "#DFC98A" },
        { "name": "EGG NOG", "code": "#FAE29C" },
        { "name": "FAWN", "code": "#C8A951" },
        { "name": "SUGAR COOKIE", "code": "#F3EAAF" },
        { "name": "SAND", "code": "#D8B863" },
        { "name": "SEPIA", "code": "#E3B778" },
        { "name": "LATTE", "code": "#E7C27D" },
        { "name": "OYSTER", "code": "#DCD7A0" },
        { "name": "BISCOTTI", "code": "#E3C565" },
        { "name": "PARMESAN", "code": "#FDE992" },
        { "name": "HAZELNUT", "code": "#BDA55D" },
        { "name": "SANDCASTLE", "code": "#DAC17C" },
        { "name": "BUTTERMILK", "code": "#FDEFB2" },
        { "name": "SAND DOLLAR", "code": "#EDE8BA" },
        { "name": "SHORTBREAD", "code": "#FBE790" },
        { "name": "CITRINE", "code": "#E4D00A" },
        { "name": "FLAX", "code": "#EEDC82" },
        { "name": "XANTHIC", "code": "#EEED09" },
        { "name": "SUNSHINE YELLOW", "code": "#FFFD37" },
        { "name": "CANARY YELLOW", "code": "#FFEF00" },
        { "name": "LEMON YELLOW", "code": "#FDFF00" },
        { "name": "PALE GOLDENROD", "code": "#EEE8AA" },
        { "name": "LIGHT KHAKI", "code": "#F0E68C" },
        { "name": "CLOVER LIME", "code": "#FCE883" },
        { "name": "ROYAL YELLOW", "code": "#FADA5E" },
        { "name": "GOLD", "code": "#FFD700" },
        { "name": "SAFETY YELLOW", "code": "#EED202" },
        { "name": "LAGUNA", "code": "#F8E473" },
        { "name": "BRIGHT YELLOW", "code": "#FFFD01" },
        { "name": "GREENISH YELLOW", "code": "#EEEA62" },
        { "name": "SUNFLOWER", "code": "#FFDA03" },
        { "name": "BUMBLEBEE", "code": "#FCE205" },
        { "name": "BUTTER", "code": "#FFFD74" },
        { "name": "YELLOW TAN", "code": "#FFE36E" },
        { "name": "BANANA", "code": "#FFE135" },
        { "name": "TUSCANY", "code": "#FCD12A" },
        { "name": "DIJON", "code": "#C49102" },
        { "name": "MUSTARD", "code": "#FEDC56" },
        { "name": "MAXIMUM YELLOW", "code": "#FAFA37" },
        { "name": "MELLOW YELLOW", "code": "#F8DE7E" },
        { "name": "UNMELLOW YELLOW", "code": "#FFFF66" },
        { "name": "LEMON CURRY", "code": "#CCA01D" },
        { "name": "AUREOLIN", "code": "#FDEE00" },
        { "name": "ELECTRIC YELLOW", "code": "#FFFF33" },
        { "name": "PASTEL YELLOW", "code": "#FFFE71" }
    ],
    "green": [
        { "name": "GREEN", "code": "#3CB043" },
        { "name": "CHARTREUSE", "code": "#B0FC38" },
        { "name": "JUNIPER", "code": "#3A5311" },
        { "name": "SAGE", "code": "#728C69" },
        { "name": "LIME", "code": "#AEF359" },
        { "name": "FERN", "code": "#5DBB63" },
        { "name": "OLIVE", "code": "#98BF64" },
        { "name": "EMERALD", "code": "#028A0F" },
        { "name": "PEAR", "code": "#74B72E" },
        { "name": "MOSS", "code": "#466D1D" },
        { "name": "SHAMROCK", "code": "#03AC13" },
        { "name": "SEAFOAM", "code": "#3DED97" },
        { "name": "PINE", "code": "#234F1E" },
        { "name": "PARAKEET", "code": "#03C04A" },
        { "name": "MINT", "code": "#99EDC3" },
        { "name": "SEAWEED", "code": "#354A21" },
        { "name": "PICKLE", "code": "#597D35" },
        { "name": "PISTACHIO", "code": "#B2D3C2" },
        { "name": "BASIL", "code": "#32612D" },
        { "name": "CROCODILE", "code": "#607D3B" },
        { "name": "AMAZON", "code": "#3B7A57" },
        { "name": "AVOCADO", "code": "#568203" },
        { "name": "CELADON", "code": "#ACE1AF" },
        { "name": "FOREST GREEN", "code": "#0B6623" },
        { "name": "HUNTER GREEN", "code": "#3F704D" },
        { "name": "ARTICHOKE GREEN", "code": "#8F9779" },
        { "name": "JUNGLE GREEN", "code": "#29AB87" },
        { "name": "TROPICAL RAINFOREST", "code": "#00755E" },
        { "name": "PERSIAN GREEN", "code": "#00A693" },
        { "name": "SEA GREEN", "code": "#2E8B57" },
        { "name": "JADE GREEN", "code": "#00A86B" },
        { "name": "LAUREL GREEN", "code": "#A9BA9D" },
        { "name": "ARMY GREEN", "code": "#4B5320" },
        { "name": "KELLY GREEN", "code": "#4CBB17" },
        { "name": "PARIS GREEN", "code": "#50C878" },
        { "name": "PAKISTAN GREEN", "code": "#006600" },
        { "name": "SPRING", "code": "#00F0A8" },
        { "name": "CHATEAU", "code": "#48A860" },
        { "name": "SWAMP", "code": "#A8C090" },
        { "name": "MANTIS", "code": "#74C365" },
        { "name": "FUN", "code": "#007848" },
        { "name": "VIRIDIAN", "code": "#609078" },
        { "name": "RESEDA GREEN", "code": "#6C7C59" },
        { "name": "VERDUN", "code": "#487800" },
        { "name": "CASTLETON GREEN", "code": "#00563B" },
        { "name": "BOTTLE GREEN", "code": "#006A4E" },
        { "name": "CADMIUM GREEN", "code": "#006B3C" },
        { "name": "CAMOUFLAGE GREEN", "code": "#78866B" },
        { "name": "DOLLAR BILL", "code": "#85BB65" },
        { "name": "INCHWORM", "code": "#B2EC5D" }
    ],
    "blue": [
        { "name": "BLUE", "code": "#3944BC" },
        { "name": "SLATE", "code": "#757C88" },
        { "name": "SKY", "code": "#63C5DA" },
        { "name": "NAVY", "code": "#0A1172" },
        { "name": "INDIGO", "code": "#281E5D" },
        { "name": "COBALT", "code": "#1338BE" },
        { "name": "TEAL", "code": "#48AAAD" },
        { "name": "OCEAN", "code": "#016064" },
        { "name": "PEACOCK", "code": "#022D36" },
        { "name": "AZURE", "code": "#1520A6" },
        { "name": "CERULEAN", "code": "#0492C2" },
        { "name": "LAPIS", "code": "#2832C2" },
        { "name": "SPRUCE", "code": "#2C3E4C" },
        { "name": "STONE", "code": "#59788E" },
        { "name": "AEGEAN", "code": "#1F456E" },
        { "name": "BLUEBERRY", "code": "#241571" },
        { "name": "DENIM", "code": "#151E3D" },
        { "name": "ADMIRAL", "code": "#051094" },
        { "name": "SAPPHIRE", "code": "#52B2BF" },
        { "name": "ARCTIC", "code": "#82EEFD" },
        { "name": "TURQUOISE", "code": "#40E0D0" },
        { "name": "STEEL", "code": "#4682B4" },
        { "name": "B'DAZZLED", "code": "#2E5894" },
        { "name": "POWDER BLUE", "code": "#B0E0E6" },
        { "name": "US AIR FORCE ACADEMY BLUE", "code": "#004F98" },
        { "name": "BABY BLUE", "code": "#89CFF0" },
        { "name": "BEAU BLUE", "code": "#BCD4E6" },
        { "name": "LITTLE BOY BLUE", "code": "#6CA0DC" },
        { "name": "TIFFANY BLUE", "code": "#81D8D0" },
        { "name": "CAROLINA BLUE", "code": "#4B9CD3" },
        { "name": "TURKISH BLUE", "code": "#4F97A3" },
        { "name": "MAYA BLUE", "code": "#73C2FB" },
        { "name": "CORNFLOWER BLUE", "code": "#6495ED" },
        { "name": "BLUE SAPPHIRE", "code": "#126180" },
        { "name": "EGYPTIAN BLUE", "code": "#1034A6" },
        { "name": "YALE BLUE", "code": "#00356B" },
        { "name": "SPACE CADET", "code": "#1D2951" },
        { "name": "IMPERIAL BLUE", "code": "#005A92" },
        { "name": "RUDDY BLUE", "code": "#76ABDF" },
        { "name": "AIR SUPERIORITY BLUE", "code": "#72A0C1" },
        { "name": "AQUAMARINE BLUE", "code": "#6BCAE2" },
        { "name": "ARGENTINA BLUE", "code": "#6CB4EE" },
        { "name": "ASTROS NAVY", "code": "#002D62" },
        { "name": "BAYERN BLUE", "code": "#0066B2" },
        { "name": "BERRY BLUE", "code": "#4F86F7" },
        { "name": "BLUE YONDER", "code": "#5072A7" },
        { "name": "BLEU DE FRANCE", "code": "#318CE7" },
        { "name": "BLUE-GRAY", "code": "#6699CC" },
        { "name": "BOEING BLUE", "code": "#0039A6" },
        { "name": "BRAVES NAVY", "code": "#13274F" }
    ],
    "purple": [
        { "name": "PURPLE", "code": "#A32CC4" },
        { "name": "MAUVE", "code": "#7A4988" },
        { "name": "DARK VIOLET", "code": "#710193" },
        { "name": "BOYSENBERRY", "code": "#630436" },
        { "name": "ELECTRIC LAVENDER", "code": "#E39FF6" },
        { "name": "PLUM", "code": "#601A35" },
        { "name": "STRONG MAGENTA", "code": "#A1045A" },
        { "name": "DEEP LILAC", "code": "#B65FCF" },
        { "name": "GRAPE", "code": "#663046" },
        { "name": "ROYAL PERIWINKLE", "code": "#BE93D4" },
        { "name": "SANGRIA PURPLE", "code": "#4D0F28" },
        { "name": "EGGPLANT", "code": "#311432" },
        { "name": "JAZZBERRY JAM", "code": "#67032F" },
        { "name": "IRIS", "code": "#9867C5" },
        { "name": "HEATHER", "code": "#9E7BB5" },
        { "name": "AMETHYST", "code": "#A45EE5" },
        { "name": "RAISIN", "code": "#290916" },
        { "name": "MEDIUM ORCHID", "code": "#AF69EF" },
        { "name": "DARK MULBERRY", "code": "#4C0121" },
        { "name": "DEEP WINE", "code": "#2C041C" },
        { "name": "THISTLE", "code": "#D8BFD8" },
        { "name": "ORCHID", "code": "#DA70D6" },
        { "name": "ELECTRIC VIOLET", "code": "#8F00FF" },
        { "name": "MEDIUM PURPLE", "code": "#9370DB" },
        { "name": "DARK ORCHID", "code": "#9932CC" },
        { "name": "DARK MAGENTA", "code": "#8B008B" },
        { "name": "VERONICA", "code": "#A020F0" },
        { "name": "HELIOTROPE", "code": "#DF73FF" },
        { "name": "PURPUREUS", "code": "#9A4EAE" },
        { "name": "NORTHWESTERN PURPLE", "code": "#4E2A84" },
        { "name": "KSU PURPLE", "code": "#512888" },
        { "name": "POMP AND POWER", "code": "#86608E" },
        { "name": "MARDI GRAS", "code": "#880085" },
        { "name": "EMINENCE", "code": "#6C3082" },
        { "name": "PANSY PURPLE", "code": "#78184A" },
        { "name": "PALATINATE", "code": "#72246C" },
        { "name": "DARK PURPLE", "code": "#301934" },
        { "name": "BYZANTIUM", "code": "#702963" },
        { "name": "ENGLISH VIOLET", "code": "#563C5C" },
        { "name": "AFFAIR", "code": "#6F4685" },
        { "name": "LONG DISTANCE", "code": "#6F456E" },
        { "name": "PRINCE CHARMING", "code": "#493F5E" },
        { "name": "LIPSTICK STAIN", "code": "#8E4785" },
        { "name": "POMPADOUR", "code": "#720058" },
        { "name": "GRAPE COLOR", "code": "#6F2DA8" },
        { "name": "PIZZA EDGE", "code": "#9A2CA0" },
        { "name": "TYRIAN PURPLE", "code": "#66023C" },
        { "name": "ULTRA VIOLET", "code": "#645394" },
        { "name": "ELECTRIC PURPLE", "code": "#BF00FF" },
        { "name": "STUDIO", "code": "#7851A9" }
    ],
    "pink": [
        { "name": "PINK", "code": "#F699CD" },
        { "name": "ROSE", "code": "#FC94AF" },
        { "name": "FRENCH FUCHSIA", "code": "#FC46AA" },
        { "name": "PUNCH", "code": "#F25278" },
        { "name": "BLUSH PINK", "code": "#FEC5E5" },
        { "name": "WATERMELON", "code": "#FE7F9C" },
        { "name": "FLAMINGO", "code": "#FDA4BA" },
        { "name": "ROUGE", "code": "#F26B8A" },
        { "name": "LIGHT SALMON", "code": "#FDAB9F" },
        { "name": "CORAL PINK", "code": "#FE7D6A" },
        { "name": "PEACH", "code": "#FC9483" },
        { "name": "STRAWBERRY", "code": "#FC4C4E" },
        { "name": "ROSEWOOD", "code": "#9E4244" },
        { "name": "LEMONADE", "code": "#FCBACB" },
        { "name": "TAFFY", "code": "#FA86C4" },
        { "name": "BUBBLEGUM", "code": "#FD5DA8" },
        { "name": "BALLET SLIPPER", "code": "#F79AC0" },
        { "name": "LEMONADE CREPE", "code": "#F2B8C6" },
        { "name": "MAGENTA PROCESS", "code": "#E11584" },
        { "name": "HOT PINK", "code": "#FF1694" },
        { "name": "AMARANTH PINK", "code": "#E52B50" },
        { "name": "RAZZMATAZZ", "code": "#E3256B" },
        { "name": "CARNATION", "code": "#FFA6C9" },
        { "name": "SALMON", "code": "#FF9999" },
        { "name": "LIGHT PINK", "code": "#FFB6C1" },
        { "name": "PASTEL PINK", "code": "#FFD1DC" },
        { "name": "CHERRY BLOSSOM", "code": "#FFB7C5" },
        { "name": "BABY PINK", "code": "#F4C2C2" },
        { "name": "DARK PINK", "code": "#E75480" },
        { "name": "BRIGHT PINK", "code": "#FF007F" },
        { "name": "NEON PINK", "code": "#FF6EC7" },
        { "name": "MAGENTA", "code": "#FF00FF" },
        { "name": "TULIP PINK", "code": "#FF8E8E" },
        { "name": "PIGGY PINK", "code": "#FDDDE6" },
        { "name": "COTTON CANDY", "code": "#FFBCD9" },
        { "name": "CAMEO PINK", "code": "#EFBBCC" },
        { "name": "FRENCH PINK", "code": "#F64A8A" },
        { "name": "PERSIAN PINK", "code": "#F77FBE" },
        { "name": "CANDY PINK", "code": "#E4717A" },
        { "name": "CHERRY PINK", "code": "#DE3163" },
        { "name": "DARK TERRA COTTA", "code": "#CC4E5C" },
        { "name": "DEEP PINK", "code": "#FF1493" },
        { "name": "DUST STORM", "code": "#E5CCC9" },
        { "name": "NADESHIKO PINK", "code": "#F6ADC6" },
        { "name": "WILD STRAWBERRY", "code": "#FF43A4" },
        { "name": "RUBINE RED", "code": "#D10056" },
        { "name": "HOLLYWOOD CERISE", "code": "#F400A1" },
        { "name": "MEXICAN PINK", "code": "#E4007C" },
        { "name": "STEEL PINK", "code": "#CC3366" },
        { "name": "ROSE BONBON", "code": "#F9429E" }
    ],
    "brown": [
        { "name": "BROWN OIL", "code": "#231709" },
        { "name": "ROASTED COFFEE", "code": "#4B371C" },
        { "name": "MOCHA", "code": "#3C280D" },
        { "name": "PEANUT BROWN", "code": "#795C34" },
        { "name": "CAROB", "code": "#362511" },
        { "name": "HICKORY", "code": "#371D10" },
        { "name": "WOOD", "code": "#3F301D" },
        { "name": "PECAN", "code": "#4A2511" },
        { "name": "WALNUT", "code": "#432616" },
        { "name": "CARAMEL", "code": "#65350F" },
        { "name": "GINGERBREAD", "code": "#5E2C04" },
        { "name": "SYRUP", "code": "#481F01" },
        { "name": "DARK CHOCOLATE", "code": "#2E1503" },
        { "name": "TORTILLA", "code": "#9A7B4F" },
        { "name": "UMBER", "code": "#352315" },
        { "name": "TAWNY", "code": "#80471C" },
        { "name": "BRUNETTE", "code": "#3B1E08" },
        { "name": "CINNAMON BROWN", "code": "#652A0E" },
        { "name": "PENNY", "code": "#532915" },
        { "name": "CEDAR BROWN", "code": "#4A3728" },
        { "name": "BEAVER", "code": "#9F8170" },
        { "name": "BISTRE", "code": "#3D2B1F" },
        { "name": "BOLE", "code": "#79443B" },
        { "name": "BURNT UMBER", "code": "#8A3324" },
        { "name": "CAFE AU LAIT", "code": "#A67B5B" },
        { "name": "CAFE NOIR", "code": "#4B3621" },
        { "name": "COFFEE", "code": "#6F4E37" },
        { "name": "DEEP COFFEE", "code": "#704241" },
        { "name": "COPPER", "code": "#B87333" },
        { "name": "DARK BROWN", "code": "#654321" },
        { "name": "TAUPE", "code": "#483C32" },
        { "name": "ECRU", "code": "#C2B280" },
        { "name": "GOLDEN BROWN", "code": "#996515" },
        { "name": "KHAKI", "code": "#C3B091" },
        { "name": "OCHRE", "code": "#CC7722" },
        { "name": "LIGHT BROWN", "code": "#B5651D" },
        { "name": "SADDLE BROWN", "code": "#8B4513" },
        { "name": "RUSSET", "code": "#80461B" },
        { "name": "SIENNA", "code": "#A0522D" },
        { "name": "ANTIQUE BRASS", "code": "#CD9575" },
        { "name": "BURLYWOOD", "code": "#DEB887" },
        { "name": "PERU", "code": "#CD853F" },
        { "name": "TUMBLEWEED", "code": "#DEAA88" },
        { "name": "DARK VANILLA", "code": "#D1BEA8" },
        { "name": "WOOD BROWN", "code": "#C19A6B" },
        { "name": "CHAMOISEE", "code": "#A0785A" },
        { "name": "DEER", "code": "#BA8759" },
        { "name": "DIRT", "code": "#9B7653" },
        { "name": "COCONUT", "code": "#965A3E" },
        { "name": "WINDSOR TAN", "code": "#A75502" }
    ],
    "black": [
        { "name": "BLACK", "code": "#000000" },
        { "name": "EBONY", "code": "#080402" },
        { "name": "CROW", "code": "#0D0907" },
        { "name": "CHARCOAL", "code": "#28231D" },
        { "name": "MIDNIGHT", "code": "#040406" },
        { "name": "INK", "code": "#070504" },
        { "name": "RAVEN", "code": "#050301" },
        { "name": "OIL", "code": "#050100" },
        { "name": "GREASE", "code": "#0A0806" },
        { "name": "ONYX", "code": "#030104" },
        { "name": "PITCH", "code": "#030001" },
        { "name": "SOOT", "code": "#160D08" },
        { "name": "SABLE", "code": "#060606" },
        { "name": "JET BLACK", "code": "#030303" },
        { "name": "COAL", "code": "#0C0908" },
        { "name": "METAL", "code": "#0E0C0A" },
        { "name": "OBSIDIAN", "code": "#020403" },
        { "name": "JADE", "code": "#000302" },
        { "name": "SPIDER", "code": "#040200" },
        { "name": "LEATHER", "code": "#0B0705" },
        { "name": "ASPHALT", "code": "#0C0404" },
        { "name": "LICORICE", "code": "#1A1110" },
        { "name": "NIGHT", "code": "#0C090A" },
        { "name": "CHARLESTON GREEN", "code": "#232B2B" },
        { "name": "DARK JUNGLE GREEN", "code": "#1A2421" },
        { "name": "EERIE BLACK", "code": "#1B1B1B" },
        { "name": "RAISIN BLACK", "code": "#242124" },
        { "name": "SMOKY BLACK", "code": "#100C08" },
        { "name": "BLACK ROCK", "code": "#010127" },
        { "name": "NEUTRAL BLACK", "code": "#0B0B0B" },
        { "name": "BLACK DENIM", "code": "#191C27" },
        { "name": "VAMPIRE BLACK", "code": "#0F0404" },
        { "name": "COOL BLACK", "code": "#151922" },
        { "name": "FROST BLACK", "code": "#191C20" },
        { "name": "POWER BLACK", "code": "#0E0C01" },
        { "name": "PREMIUM BLACK", "code": "#100E09" },
        { "name": "BLACK MAGIC", "code": "#0B0510" },
        { "name": "ALIEN BLACK", "code": "#1A2228" },
        { "name": "BLACK CHOCOLATE", "code": "#1B1811" },
        { "name": "GOTHIC GRAPE", "code": "#120321" },
        { "name": "METROPOLIS", "code": "#1A1A1A" },
        { "name": "NIGHT SHADOW", "code": "#1C1C1C" },
        { "name": "DARK RAISIN", "code": "#1A0F0F" },
        { "name": "TEA BAG", "code": "#161311" },
        { "name": "TECH BLACK", "code": "#0D0E0E" },
        { "name": "DULL BLACK", "code": "#161616" },
        { "name": "DARK BLACK", "code": "#010203" },
        { "name": "NATURAL BLACK", "code": "#07000B" },
        { "name": "RETRO BLACK", "code": "#1F201F" },
        { "name": "DEEP BLACK", "code": "#050203" }
    ],
    "gray": [
        { "name": "GUNMETAL", "code": "#2A3439" },
        { "name": "SHADOW", "code": "#373737" },
        { "name": "GRAPHITE", "code": "#594D5B" },
        { "name": "IRON", "code": "#322D31" },
        { "name": "PEWTER", "code": "#696880" },
        { "name": "CLOUD", "code": "#C5C6D0" },
        { "name": "SILVER", "code": "#ADADC9" },
        { "name": "SMOKE", "code": "#59515E" },
        { "name": "DARK SLATE", "code": "#3E3D53" },
        { "name": "ANCHOR", "code": "#41424C" },
        { "name": "ASH", "code": "#564C4D" },
        { "name": "PORPOISE", "code": "#4D4C5C" },
        { "name": "DOVE", "code": "#7C6E7F" },
        { "name": "FOG", "code": "#655967" },
        { "name": "FLINT", "code": "#7F7D9C" },
        { "name": "CHARCOAL GRAY", "code": "#232023" },
        { "name": "PEBBLE", "code": "#333333" },
        { "name": "LEAD", "code": "#3F3F4E" },
        { "name": "COIN", "code": "#9897A9" },
        { "name": "FOSSIL", "code": "#787276" },
        { "name": "ARSENIC", "code": "#3B444B" },
        { "name": "NEVADA", "code": "#666A6D" },
        { "name": "SCORPION", "code": "#5E5E5E" },
        { "name": "BATTLESHIP GRAY", "code": "#848482" },
        { "name": "CARBON GRAY", "code": "#625D5D" },
        { "name": "DAVY'S GRAY", "code": "#555555" },
        { "name": "DIM GRAY", "code": "#696969" },
        { "name": "GRAY CLOUD", "code": "#B6B6B4" },
        { "name": "GRAY DOLPHIN", "code": "#5C5858" },
        { "name": "GRAY WOLF", "code": "#504A4B" },
        { "name": "GUNMETAL", "code": "#2A3439" },
        { "name": "MARENGO", "code": "#4C5866" },
        { "name": "MEDIUM GRAY", "code": "#BEBEBE" },
        { "name": "NICKEL", "code": "#727472" },
        { "name": "STONE GRAY", "code": "#928E85" },
        { "name": "OUTER SPACE", "code": "#414A4C" },
        { "name": "ROCKET METALLIC", "code": "#8A7F8D" },
        { "name": "SILVER CHALICE", "code": "#ACACAC" },
        { "name": "SMOKEY GRAY", "code": "#726E6D" },
        { "name": "SONIC GRAY", "code": "#757575" },
        { "name": "SPANISH GRAY", "code": "#989898" },
        { "name": "TAUPE GRAY", "code": "#8B8589" },
        { "name": "VAMPIRE GRAY", "code": "#565051" },
        { "name": "X11 GRAY", "code": "#BBBCB6" },
        { "name": "DARK SILVER", "code": "#746D69" },
        { "name": "PASTEL GRAY", "code": "#CCCDC6" },
        { "name": "MISTY GRAY", "code": "#BCC2C2" },
        { "name": "VINTAGE GRAY", "code": "#989692" },
        { "name": "ZOMBIE GRAY", "code": "#63645E" },
        { "name": "PERFECT GRAY", "code": "#A1A1A1" }
    ],
    "white": [
        { "name": "WHITE", "code": "#FFFFFF" },
        { "name": "PEARL", "code": "#FBFCF8" },
        { "name": "ALABASTER", "code": "#FEF9F3" },
        { "name": "SNOW", "code": "#F5FEFD" },
        { "name": "PALE IVORY", "code": "#FDF6E4" },
        { "name": "CREAM", "code": "#FFFADA" },
        { "name": "EGGSHELL", "code": "#FFF9E3" },
        { "name": "COTTON", "code": "#FBFBF9" },
        { "name": "CHIFFON", "code": "#FBFAF2" },
        { "name": "PINK SALT", "code": "#F8EEEC" },
        { "name": "LACE", "code": "#F8F2ED" },
        { "name": "COCONUT MILK", "code": "#FFF1E6" },
        { "name": "LINEN", "code": "#F3EAD3" },
        { "name": "BONE", "code": "#E7DECC" },
        { "name": "DAISY", "code": "#FAFAFA" },
        { "name": "POWDER", "code": "#FBFCFA" },
        { "name": "FROST", "code": "#ECFBFC" },
        { "name": "PORCELAIN", "code": "#FFFEFC" },
        { "name": "PARCHMENT", "code": "#FBF5DF" },
        { "name": "RICE", "code": "#FAF5EF" },
        { "name": "SEASHELL", "code": "#FFF5EE" },
        { "name": "PEPPERMINT", "code": "#F1F9EC" },
        { "name": "MILK", "code": "#FDFFF5" },
        { "name": "GHOST WHITE", "code": "#F8F8FF" },
        { "name": "WHITE SMOKE", "code": "#F5F5F5" },
        { "name": "BABY POWDER", "code": "#FEFEFA" },
        { "name": "IVORY", "code": "#FFFFF0" },
        { "name": "FLORAL WHITE", "code": "#FFFAF0" },
        { "name": "LINK WHITE", "code": "#ECF3F9" },
        { "name": "ROSE WHITE", "code": "#FFFAFA" },
        { "name": "VISTA WHITE", "code": "#FDFCFA" },
        { "name": "SNOW DRIFT", "code": "#F8FBF8" },
        { "name": "ISLAND SPICE", "code": "#FFFCEC" },
        { "name": "SOFT PEACH", "code": "#F6F1F4" },
        { "name": "HARP", "code": "#EBF5F0" },
        { "name": "COUGH MIXTURE", "code": "#F6F4F1" },
        { "name": "CUP CAKE", "code": "#EBF6F7" },
        { "name": "MAGNOLIA", "code": "#F8F4FF" },
        { "name": "ANTI-FLASH WHITE", "code": "#F2F3F4" },
        { "name": "CASCADING WHITE", "code": "#F7F5F6" },
        { "name": "COTTON BALL", "code": "#F2F7FD" },
        { "name": "PHOTON WHITE", "code": "#F8F8E8" },
        { "name": "WHITE HEAT", "code": "#FDF9EF" },
        { "name": "WHITEWASH", "code": "#FEFFFC" },
        { "name": "SHADOW WHITE", "code": "#EEF1EA" },
        { "name": "ACOUSTIC WHITE", "code": "#EFECE1" },
        { "name": "AIRCRAFT WHITE", "code": "#EDF2F8" },
        { "name": "CERAMIC", "code": "#FCFFF9" },
        { "name": "BRIGHT WHITE", "code": "#F4F5F0" },
        { "name": "BRILLIANT WHITE", "code": "#EDF1FE" }
    ]
};

// Color categories for getColor function
const colorCategories = ["red", "orange", "yellow", "green", "blue", "purple", "pink", "brown", "black", "gray", "white"];

/**
 * Get a color by input number - cycles through color categories
 * @param {number} inputNumber - The number to determine which color to return
 * @returns {Object} Object containing color info and recommended text color
 */
function getColor(inputNumber) {
    if (typeof inputNumber !== 'number' || isNaN(inputNumber)) {
        inputNumber = 0;
    }
    
    // Calculate the color category and index within that category
    const colorCategory = inputNumber % colorCategories.length;
    const colorIndex = Math.floor(inputNumber / colorCategories.length);
    
    // Get the color array for this category
    const categoryColors = colorsData[colorCategories[colorCategory]];
    
    // Wrap around if colorIndex exceeds available colors
    const safeIndex = colorIndex % categoryColors.length;
    
    // Get the color and its hex code
    const color = categoryColors[safeIndex];
    const hexCode = color.code;
    
    // Calculate the brightness of the color to determine the text color
    const r = parseInt(hexCode.slice(1, 3), 16);
    const g = parseInt(hexCode.slice(3, 5), 16);
    const b = parseInt(hexCode.slice(5, 7), 16);
    const brightness = Math.round((r * 299 + g * 587 + b * 114) / 1000);
    const textColor = brightness > 125 ? "black" : "white";
    
    // Return the color and the text color
    return { color: color, textColor: textColor };
}

/**
 * Get all colors data
 * @returns {Object} The complete colors data object
 */
function getAllColors() {
    return colorsData;
}

/**
 * Get colors by category
 * @param {string} category - The color category (red, orange, yellow, green, blue, purple, pink, brown, black, gray, white)
 * @returns {Array} Array of colors in that category
 */
function getColorsByCategory(category) {
    return colorsData[category] || [];
}
// ==================== END COLOR DATA ====================

for (let year = 2023; year <= currentYear + 2; year++) {
  for (let quarter = 1; quarter <= 4; quarter++) {
    Translator.push(`Q${quarter} ${year}`);
  }
}

const permissionsType = [
  { value: 0, name: 'noType', description: 'Placeholder it do nothing' },
  { value: 1, name: 'user_manage', description: 'Manage users (Can view/edit any users)' },
  { value: 2, name: 'user_permission_manage', description: 'Manage user permissions(Can view/edit any permission of users)' },
  { value: 3, name: 'lead_creation', description: 'Create leads' },
  { value: 4, name: 'lead_manage', description: 'Manage leads (Can view/edit any leads)' },
  { value: 5, name: 'contact_manage', description: 'Manage contacts (Can create/view/edit any contacts)' },
  { value: 6, name: 'event_manage', description: 'Manage events (Can view/edit any events)' },
  { value: 7, name: 'project_manage', description: 'Manage projects (Can view/edit any projects)' },
  { value: 8, name: 'log_manage', description: 'Manage logs (Can view/edit any logs)' },
  { value: 9, name: 'helpdesk_manage', description: 'Manage helpdesk (Can view/edit any helpdesk ticket)' },
  { value: 10, name: 'crm_access', description: 'No use right now' },
  { value: 11, name: 'project_access', description: 'Create projects' },
  { value: 12, name: 'event_access', description: 'Create events' },
  { value: 13, name: 'contact_access', description: 'Export contacts' },
  { value: 18, name: 'helpdesk_access', description: 'Access helpdesk (Can view/create any helpdesk ticket)' },
  { value: 19, name: 'inventory_access', description: 'Access inventory (Can view inventory)' },
  { value: 20, name: 'brand_manage', description: 'Manage brands (Can view/edit any brand)' },
  { value: 21, name: 'product_manage', description: 'Manage products (Can view/edit any product)' },
  { value: 22, name: 'stock_manage', description: 'Manage stock (Can view/edit any stock)' }

];

const permissionsTypeIndividual = [
  { value: 14, name: 'lead_manage_individual', description: 'Manage individual leads (View/edit leads of specific users)' },
  { value: 15, name: 'helpdesk_manage_individual', description: 'Manage individual helpdesk tickets (View/edit helpdesk tickets of specific users)' },
  { value: 16, name: 'event_manage_individual', description: 'Manage individual events (View/edit events of specific users)' },
  { value: 17, name: 'project_manage_individual', description: 'Manage individual projects (View/edit projects of specific users)' }
];


function isDefined(input) {
  if (input !== undefined && input !== null) return true;
  return false;
}




function sendLoginRequest(username, password, callback) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url + "/biomedapi/login", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4) {
      if (xhr.status === 200) {
        /*var response = JSON.parse(xhr.responseText);
                var token = response.token;*/
        // Save token to cookie
        document.cookie = "jwtToken=" + xhr.responseText;
        sessionStorage.setItem("jwtToken", xhr.responseText);
        myUserRequest(function (error, response) {
          if (error) {
            console.error(error);
            // Handle error
          } else {
            xalert(
              "Welcome " + response.FirstName + " " + response.LastName,
              0,
              -1
            );
            ////console.log(response);
            // Handle response
          }
        }, true);

        callback(null, xhr.responseText);
      } else if (xhr.status === 400) {
        callback(new Error("Incorrect Username/Password"), null);
      } else {
        callback(new Error(xhr.responseText), xhr.status);
      }
    }
  };
  var data = JSON.stringify({ username: username, password: password });
  xhr.send(data);
}

function myPermission(callback) {
  myUserRequest((error, user) => {

    if (error) {
      console.error('Failed to fetch user:', error);
      xalert('Failed to fetch user', 1, -1);
      return;
    }
    //console.log(user);
    var permissions = user.Permissions;
    var mainPermissions = permissions.filter(permission => !permission.Type.includes("individual"));
    var individualPermissions = permissions.filter(permission => permission.Type.includes("individual"));
    var FullPermissions = {
      "MainPermissions":mainPermissions,
      "IndividualPermissions":individualPermissions  
    };
    //console.log(FullPermissions);
    callback(null, FullPermissions);

  });

}

function getQuarterDateRange(quarter, year) {

  const yearAmp = year -1;
  //xalert("Year Amp: "+yearAmp,0,-1);
  //xalert("Quarter: "+quarter,0,-1);
  if (quarter === 0) {
      const quarterStartMonths = [5, 8, 11, 2]; // May, August, November, February
      const quarterEndMonths = [7, 10, 1, 4]; // July, October, January, April

      const quarterStartMonth = quarterStartMonths[0];
      const quarterEndMonth = quarterEndMonths[3];

      const startDate = new Date(`20${yearAmp}-${quarterStartMonth}-01`);
      const endDate = new Date(`20${yearAmp + 1}-${quarterEndMonth}-${getDaysInMonth(quarterEndMonth, yearAmp + 1)}`);
      endDate.setHours(23, 59, 59);
      //console.log("Quarter to Range",startDate, endDate);
      
      return {
          startDate,
          endDate
      };
  }
  const quarterStartMonths = [5, 8, 11, 2]; // May, August, November, February
  const quarterEndMonths = [7, 10, 1, 4]; // July, October, December, March
  if (quarter < 1 || quarter > 4) {
      throw new Error('Invalid quarter');
  }

  if (yearAmp < 0 || yearAmp > 99) {
      throw new Error('Invalid year');
  }
  let startYear = parseInt(yearAmp);
  let endYear = parseInt(yearAmp);
  if (quarter === 4) {
      startYear += 1;
      endYear += 1;
  }
  if (quarter === 3) {
      endYear += 1;
  }


  const quarterStartMonth = quarterStartMonths[quarter - 1];
  const quarterEndMonth = quarterEndMonths[quarter - 1];

  let startDate = new Date(`20${startYear.toString()}-${quarterStartMonth}-01`);
  let endDate = new Date(`20${endYear.toString()}-${quarterEndMonth}-${getDaysInMonth(quarterEndMonth, endYear.toString())}`);
  startDate.setHours(0, 0, 0);
  endDate.setHours(23, 59, 59);
  if(iOS()){
    console.warn("iOS detected attempting to fix date");
    console.warn("Before",startDate,endDate);
    startDate.setFullYear(parseInt('20'+startYear.toString()),quarterStartMonth-1,1);
    endDate.setFullYear(parseInt('20'+endYear.toString()),quarterEndMonth-1,getDaysInMonth(quarterEndMonth, endYear.toString()));
    console.warn("After",startDate,endDate);
    //xalert("iOS Detected",2,-1);
    //xalert(startDate,2,-1);
    //xalert(endDate,2,-1);
  }
  //console.log("Quarter to Range",startDate, endDate);
  return {
      startDate,
      endDate
  };
}

function getDaysInMonth(month, year) {
  return new Date(year, month, 0).getDate();
}


function myUserRequest(callback, force) {
  if (force === true) {
    sessionStorage.removeItem("myUser");
  }
  var myUser = sessionStorage.getItem("myUser");
  if (myUser !== null) {
    if (callback === null) {
      return;
    }
    callback(null, JSON.parse(myUser));
    return;
  }

  var xhr = new XMLHttpRequest();
  xhr.open("GET", url + "/biomedapi/myuser", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  var token = readToken();
  if (token === null) {
    callback("Token not found", null);
    return;
  }
  xhr.setRequestHeader("Authorization", "Bearer " + token);
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4) {
      if (xhr.status === 200) {
        var response = JSON.parse(xhr.responseText);
        // Save user object in session storage
        sessionStorage.setItem("myUser", JSON.stringify(response));
        if (callback === null) {
          return;
        }
        callback(null, response);
      } else {
        if (callback === null) {
          return;
        }
        callback(new Error(xhr.responseText), xhr.status);
      }
    }
  };
  xhr.send();
}

function decodeJwtPayload(token) {
  // 1. Split out the payload (second segment)
  const base64Url = token.split('.')[1];
  // 2. Convert from base64url to base64
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  // 3. atob() gives us the raw JSON string
  const jsonString = decodeURIComponent(
    atob(base64)
      .split('')
      .map(c => {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      })
      .join('')
  );
  // 4. Parse and return
  return JSON.parse(jsonString);
}

function readToken() {
  var token = null;
  if (sessionStorage.getItem("jwtToken")) {
    token = sessionStorage.getItem("jwtToken");
  }else{
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      if (cookie.startsWith("jwtToken=")) {
        token = cookie.substring("jwtToken=".length, cookie.length);
        break;
      }
    }
  }
  
  if (token === null) {
    window.location.href = "./login.html";
    return null;
  }

  const payload = decodeJwtPayload(token);
  console.log(payload);                  // see all claims
  const expSeconds = payload.exp;        // typically a UNIX timestamp (seconds)
  const expiresAt   = new Date(expSeconds * 1000);
  console.log('Expires at:', expiresAt);

  // Check if it’s already expired:
  if (Date.now() >= expSeconds * 1000) {
    console.log('Token has expired!');
    removeToken();
  } else {
    console.log(`Token still valid for ${(expSeconds * 1000 - Date.now()) / 1000} seconds`);
    return token;
  }

  return null;
}

function removeToken() {
    //console.log("Removing token");
    document.cookie = "jwtToken=; expires=Thu, 01 Jan 1970 00:00:00 UTC;path=*;";
    sessionStorage.removeItem("myUser");
    sessionStorage.removeItem("users");
    sessionStorage.removeItem("pipelines");
    sessionStorage.removeItem("groups");
    clearCache();
    window.location.href = "./login.html";
    //console.log(readToken());
}

function getEvents(callback,query) {
    var token = readToken();
    var xhr = new XMLHttpRequest();
    if(query === undefined || query === null){
        xhr.open('GET', url+'/biomedapi/events', true);
    }
    else{
        xhr.open('POST', url+'/biomedapi/events', true);
    }
    //xhr.open('GET', url+'/biomedapi/events', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Authorization', 'Bearer ' + token);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                var events = JSON.parse(xhr.responseText);
                //console.log(events);
                callback(null, events);
            } else {
                callback('Request failed with status ' + xhr.status+" error:"+xhr.responseText+"\nRequest:"+JSON.stringify(query), null);
            }
        }
    };
    if(query !== undefined && query !== null){
        xhr.send(JSON.stringify(query));
    }
    else{
        xhr.send();
    }
}

function xalert(text, style, time) {
  document.body.scrollTop = 0; // For Safari
  document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
  var alertBar = document.getElementById("alert-bar");
  alertBar.innerHTML = ""; // add // for debuging
  var styleClass = "";
  var styleText = "";

  switch (style) {
    case 0:
      styleClass = "success";
      styleText = "<strong>Successful</strong>";
      break;
    case 1:
      styleClass = "danger";
      styleText = "<strong>Error</strong>";
      break;
    case 2:
      styleClass = "warning";
      styleText = "<strong>Warning</strong>";
      break;
    case 3:
      styleClass = "info";
      styleText = "<strong>Info</strong>";
      break;
    default:
      styleClass = "info";
      styleText = "<strong>Info</strong>";
      break;
  }

  var alertElement = document.createElement("div");
  alertElement.classList.add(
    "alert",
    "alert-" + styleClass,
    "my-3",
    "mx-2",
    "text-wrap",
    "text-break"
  );
  alertElement.setAttribute("role", "alert");
  alertElement.innerHTML = styleText + "-" + text;

  alertBar.appendChild(alertElement);

  if (time !== -1 && time !== null) {
    setTimeout(function () {
      alertElement.remove();
    }, time);
  }
}
getUserById = function (callback, id) {
  intid = parseInt(id);
  if (isNaN(intid)) {
    callback(new Error("Invalid ID: ID should be an integer"), null);
    return;
  }

  // Get all users from session storage (including disabled) for lookup by ID
  var cachedUsers = sessionStorage.getItem("users");
  if (cachedUsers !== null) {
    var allUsers = JSON.parse(cachedUsers);
    const user = allUsers.find(user => user.Id === intid);
    callback(null, user);
    return;
  }

  // If no cache, fetch and store, then find
  getUsers((error, users) => {
    if (error) {
      console.error('Failed to fetch users:', error);
      callback(error, null);
      return;
    }
    // Re-read from session to get all users including disabled
    var allUsersRaw = sessionStorage.getItem("users");
    if (allUsersRaw) {
      var allUsers = JSON.parse(allUsersRaw);
      const user = allUsers.find(user => user.Id === intid);
      callback(null, user);
    } else {
      callback(null, null);
    }
  }, false);
}

function getUsers(callback, force, includeDisabled) {
  if (force === true) {
    sessionStorage.removeItem("users");
  }
  var users = sessionStorage.getItem("users");
  if (users !== null) {
    var parsedUsers = JSON.parse(users);
    // Filter out disabled users unless includeDisabled is true
    var filteredUsers = includeDisabled ? parsedUsers : parsedUsers.filter(function(u) { return u.Enabled !== false; });
    // Sort by FirstName
    filteredUsers.sort(function(a, b) {
      var nameA = (a.FirstName || '').toLowerCase();
      var nameB = (b.FirstName || '').toLowerCase();
      return nameA.localeCompare(nameB);
    });
    callback(null, filteredUsers);
    return;
  }
  var xhr = new XMLHttpRequest();
  xhr.open("GET", url + "/biomedapi/users", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());
  xhr.onload = function () {
    if (xhr.status === 200) {
      var users = JSON.parse(xhr.responseText);
      sessionStorage.setItem("users", JSON.stringify(users));
      // Filter out disabled users unless includeDisabled is true
      var filteredUsers = includeDisabled ? users : users.filter(function(u) { return u.Enabled !== false; });
      // Sort by FirstName
      filteredUsers.sort(function(a, b) {
        var nameA = (a.FirstName || '').toLowerCase();
        var nameB = (b.FirstName || '').toLowerCase();
        return nameA.localeCompare(nameB);
      });
      callback(null, filteredUsers);
    } else {
      callback(new Error(xhr.responseText), null);
    }
  };
  xhr.onerror = function () {
    callback(new Error("Request failed"), null);
  };
  xhr.send();
  
}

function getPipelines(callback, force) {
  if (force === true) {
    sessionStorage.removeItem("pipelines");
  }
  var pipelines = sessionStorage.getItem("pipelines");
  if (pipelines !== null) {
    callback(null, JSON.parse(pipelines));
    return;
  }
  var xhr = new XMLHttpRequest();
  xhr.open("GET", url + "/biomedapi/v2/crm/pipelines", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());
  xhr.onload = function () {
    if (xhr.status === 200) {
      var pipelines = JSON.parse(xhr.responseText);
      pipelines.sort((a, b) => a.Order - b.Order);
      sessionStorage.setItem("pipelines", JSON.stringify(pipelines));
      callback(null, pipelines);
    } else {
      callback(new Error(xhr.responseText), null);
    }
  };
  xhr.onerror = function () {
    callback(new Error("Request failed"), null);
  };
  xhr.send();
}

function isValidGuid(input) {
  var guidRegex =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return guidRegex.test(input);
}

function iOS() {
  //xalert(navigator.userAgent,3,-1);
  var iOS = /(iPad|iPhone|iPod|OS X)/g.test(navigator.userAgent);
  return iOS;
}


function timeFormater(input) {
  const options = {
    month: "numeric",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "numeric",
    second: "numeric",
    hour12: true,
  };
  //'en-US', options
  // Create DateRange record
  var temp = new Date(input).toLocaleString("en-US", options);
  //console.log(temp);
  /*if(iOS()){
    console.warn("iOS detected attempting to fix date");
    console.warn("Before",temp);
    temp = temp.replace(/-/g, "/");
    console.warn("After",temp);
  }*/
  return temp;
}
function timeIsoString(input) {
  const date = new Date(input);
  return date.toISOString();
}


function timeFriendly(input) {
  const options = {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  };

  var temp = new Date(input).toLocaleString("en-US", options);
  return temp;
}

function timeFriendlyString(input) {
  const date = new Date(input);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  const ampm = hours >= 12 ? "PM" : "AM";

  const formattedDate = `${month}-${day}-${year}`;
  const formattedTime = `${hours}:${minutes}:${seconds} ${ampm}`;

  return `${formattedDate} ${formattedTime}`;
}

function getLeads(callback,query = null,deep = false) {
  const token = readToken();

  const xhr = new XMLHttpRequest();
  if(query === null){
    xhr.open("POST", url + "/biomedapi/v2/crm/leads", true);
    query = {};
  }
  else{
    xhr.open("POST", url + "/biomedapi/v2/crm/leads", true);
  }
  if (deep === true) {
    query = { "DeepDetails": true };
  }
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", `Bearer ${token}`);
  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        // Request successful
        //console.log(xhr.responseText);
        const leads = JSON.parse(xhr.responseText);

        callback(null, leads);
      } else {
        // Request failed
        xalert("Error " + xhr.status + " " + xhr.responseText+"\nRequest:"+JSON.stringify(query), 1, -1);
        callback(xhr.status, null);
      }
    }
  };
  if(query !== null){
    xhr.send(JSON.stringify(query));
  }
  else{
    xhr.send();
  }
}

function timeFuck(input) {
  date = new Date(input);

  // Extract the components in local time
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  // Format the datetime-local value
  const localDateTimeString = `${year}-${month}-${day}T${hours}:${minutes}`;

  return localDateTimeString;
}

async function getColor(inputNumber) {
  if (typeof inputNumber !== 'number' || isNaN(inputNumber)) {
    inputNumber = 0;
  }
  if (sessionStorage.getItem("colors")) {
    var colors = JSON.parse(sessionStorage.getItem("colors"));
    // Rest of the code that uses the colors
  } else {
    const response = await fetch("colors.json");
    var colors = await response.json();
    sessionStorage.setItem("colors", JSON.stringify(colors));
    // Rest of the code that uses the colors
  }
  // Define the color categories in the order they should be returned
  const colorCategories = [
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "pink",
    "brown",
    "black",
    "gray",
    "white",
  ];

  // Calculate the color category and index within that category

  const colorCategory = inputNumber % colorCategories.length;
  const colorIndex = Math.floor(inputNumber / colorCategories.length);

  // Get the color and its hex code
  const color = colors[colorCategories[colorCategory]][colorIndex];

  const hexCode = color.code;

  // Calculate the brightness of the color to determine the text color
  const r = parseInt(hexCode.slice(1, 3), 16);
  const g = parseInt(hexCode.slice(3, 5), 16);
  const b = parseInt(hexCode.slice(5, 7), 16);
  const brightness = Math.round((r * 299 + g * 587 + b * 114) / 1000);
  const textColor = brightness > 125 ? "black" : "white";
  //console.log({ color: color, textColor: textColor });
  // Return the color and the text color
  return { color: color, textColor: textColor};
}

function getGroups(callback, force) {
  if (force === true) {
    sessionStorage.removeItem("groups");
  }
  var groups = sessionStorage.getItem("groups");
  if (groups !== null) {
    callback(null, JSON.parse(groups));
    return;
  }
  var xhr = new XMLHttpRequest();
  xhr.open("GET", url + "/biomedapi/groups", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());
  xhr.onload = function () {
    if (xhr.status === 200) {
      var groups = JSON.parse(xhr.responseText);
      callback(null, groups);
      sessionStorage.setItem("groups", JSON.stringify(groups));
    } else {
      callback(new Error(xhr.responseText), null);
    }
  };
  xhr.onerror = function () {
    callback(new Error("Request failed"), null);
  };
  xhr.send();
}
async function promiseGroups(force = false) {
  return new Promise((resolve, reject) => {
    getGroups((error, groups) => {
      if (error) {
        console.error('Failed to fetch groups:', error);
        reject(error);
        return;
      }
      resolve(groups);
    }, force);
  });
}

function getGroupMembers(groupId, callback) {
  var xhr = new XMLHttpRequest();
  xhr.open("GET", url + "/biomedapi/groups/" + groupId, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());
  xhr.onload = function () {
    if (xhr.status === 200) {
      var members = JSON.parse(xhr.responseText);
      //console.log(members);
      callback(null, members);
    } else {
      callback(new Error(xhr.responseText), null);
    }
  };
  xhr.onerror = function () {
    callback(new Error("Request failed"), null);
  };
  xhr.send();
}
function promiseGroupMembers(groupId) {
  return new Promise((resolve, reject) => {
    getGroupMembers(groupId, (error, members) => {
      if (error) {
        console.error('Failed to fetch group members:', error);
        reject(error);
        return;
      }
      resolve(members);
    });
  });
}


let timeoutId;

function startShaking(button, redirect) {
  button.classList.add("shake");
  timeoutId = setTimeout(() => {
    redirect();
  }, 1000);
}

function stopShaking(button) {
    clearTimeout(timeoutId);
    button.classList.remove('shake');
}


function getContacts(callback, force) {
  if (force === true) {
    sessionStorage.removeItem("contacts");
    Object.keys(sessionStorage).forEach(key => {
      if (key.startsWith("contact:")) {
        sessionStorage.removeItem(key);
      }
    });
  }
  var contacts = sessionStorage.getItem("contacts");

  if (contacts !== null) {
    var parsedContacts = JSON.parse(contacts);
    // Sort by Name
    parsedContacts.sort(function(a, b) {
      var nameA = (a.Name || '').toLowerCase();
      var nameB = (b.Name || '').toLowerCase();
      return nameA.localeCompare(nameB);
    });
    callback(null, parsedContacts);

  } else {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url + "/biomedapi/contacts", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          var contacts = JSON.parse(xhr.responseText);
          sessionStorage.setItem("contacts", JSON.stringify(contacts));
          // Sort by Name
          contacts.sort(function(a, b) {
            var nameA = (a.Name || '').toLowerCase();
            var nameB = (b.Name || '').toLowerCase();
            return nameA.localeCompare(nameB);
          });
          callback(null, contacts);
        } else {
          callback(new Error("Failed to get contacts"), null);
        }
      }
    };
    xhr.send();
  }
}

function getContactById(id, callback) {
  var contact = sessionStorage.getItem("contact:"+id);
  if (contact !== null) {
    callback(null, JSON.parse(contact));
  } else {
        var xhr = new XMLHttpRequest();
        xhr.open("GET", url + "/biomedapi/contacts/" + id, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.setRequestHeader("Authorization", "Bearer " + readToken());
        xhr.onload = function () {
          if (xhr.readyState === xhr.DONE) {
            if (xhr.status === 200) {
              var contact = JSON.parse(xhr.responseText);
              sessionStorage.setItem("contact:"+id, JSON.stringify(contact));
              callback(null, contact);
            } else {
              callback("Error: " + xhr.status);
            }
          }
        };
        xhr.onerror = function () {
          callback("Request failed");
        };
        xhr.send();
      }
}

function getIDFromSelection(selection) {
  return Array.from(
    selection.selectedOptions
  ).map((option) => parseInt(option.value))
}

function clearCache () {
  sessionStorage.clear();
}


function getBillings(callback,force) {
  if(force === true){
    sessionStorage.removeItem("billing");
  }
  var xhr = new XMLHttpRequest();
  xhr.open("GET", url + "/biomedapi/billinginformations", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());
  xhr.onload = function () {
    if (xhr.status === 200) {
      var billing = JSON.parse(xhr.responseText);
      sessionStorage.setItem("billing", JSON.stringify(billing));
      callback(null, billing);
    } else {
      callback(new Error(xhr.responseText), null);
    }
  };
  xhr.onerror = function () {
    callback(new Error("Request failed"), null);
  };
  xhr.send();
}

function getProducts(callback, force) {
  if (force === true) {
    sessionStorage.removeItem("product");
  }
  var product = sessionStorage.getItem("product");
  if (product !== null) {
    callback(null, JSON.parse(product));
  } else {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url + "/biomedapi/products", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onload = function () {
      if (xhr.status === 200) {
        var product = JSON.parse(xhr.responseText);
        sessionStorage.setItem("product", JSON.stringify(product));
        callback(null, product);
      } else {
        callback(new Error(xhr.responseText), null);
      }
    };
    xhr.onerror = function () {
      callback(new Error("Request failed"), null);
    };
    xhr.send();
  }
}

function getProductById(id, callback) {
  var product = sessionStorage.getItem("product:" + id);
  if (product !== null) {
    callback(null, JSON.parse(product));
  } else {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url + "/biomedapi/products/" + id, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onload = function () {
      if (xhr.readyState === xhr.DONE) {
        if (xhr.status === 200) {
          sessionStorage.setItem("product:" + id, xhr.responseText);
          callback(null, JSON.parse(xhr.responseText));
        } else {
          callback("Error: " + xhr.status);
        }
      }
    };
    xhr.onerror = function () {
      callback("Request failed");
    };
    xhr.send();
  }
}

function getSaleAreas(callback, force) {
  if (force === true) {
    sessionStorage.removeItem("saleArea");
  }
  var saleArea = sessionStorage.getItem("saleArea");
  if (saleArea !== null) {
    callback(null, JSON.parse(saleArea));
  } else {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url + "/biomedapi/saleareas", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onload = function () {
      if (xhr.status === 200) {
        var saleArea = JSON.parse(xhr.responseText);
        sessionStorage.setItem("saleArea", JSON.stringify(saleArea));
        callback(null, saleArea);
      } else {
        callback(new Error(xhr.responseText), null);
      }
    };
    xhr.onerror = function () {
      callback(new Error("Request failed"), null);
    };
    xhr.send();
  }
}
function getSaleAreaById(id) {
  return new Promise((resolve, reject) => {
    var saleArea = sessionStorage.getItem("saleArea:" + id);
    if (saleArea !== null) {
      resolve(JSON.parse(saleArea));
    } else {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", url + "/biomedapi/saleareas/" + id, true);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.setRequestHeader("Authorization", "Bearer " + readToken());
      xhr.onload = function () {
        if (xhr.readyState === xhr.DONE) {
          if (xhr.status === 200) {
            sessionStorage.setItem("saleArea:" + id, xhr.responseText);
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject("Error: " + xhr.status);
          }
        }
      };
      xhr.onerror = function () {
        reject("Request failed");
      };
      xhr.send();
    }
  });
}

function getProjects(callback, force) {
  if (force === true) {
    sessionStorage.removeItem("projects");
  }
  var projects = sessionStorage.getItem("projects");
  if (projects !== null) {
    callback(null, JSON.parse(projects));
  } else {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url + "/biomedapi/v2/project", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onload = function () {
      if (xhr.status === 200) {
        var projects = JSON.parse(xhr.responseText);
        sessionStorage.setItem("projects", JSON.stringify(projects));
        callback(null, projects);
      } else {
        console.error("getProjects error:", xhr.status, xhr.responseText);
        callback(new Error("Status " + xhr.status + ": " + xhr.responseText), null);
      }
    };
    xhr.onerror = function () {
      console.error("getProjects network error");
      callback(new Error("Network request failed"), null);
    };
    xhr.send();
  }
}

function getProjectById(id, callback) {
  var project = sessionStorage.getItem("project:" + id);
  if (project !== null) {
    callback(null, JSON.parse(project));
  } else {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url + "/biomedapi/v2/project/" + id, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onload = function () {
      if (xhr.readyState === xhr.DONE) {
        if (xhr.status === 200) {
          sessionStorage.setItem("project:" + id, xhr.responseText);
          callback(null, JSON.parse(xhr.responseText));
        } else {
          callback("Error: " + xhr.status);
        }
      }
    };
    xhr.onerror = function () {
      callback("Request failed");
    };
    xhr.send();
  }
}

function headerSetup(){
  const header = document.querySelector("header");
  if (!header) {
    console.error("Header element not found.");
    return;
  }
  //console.log("Setting up header");
  //console.log(header);
  header.innerHTML = `
    <div class="px-1 py-0 biomed-bg-dark border-bottom">
  <div class="containerfluid">
    <div class="d-flex align-items-center justify-content-evenly flex-wrap flex-xxl-nowrap">
      <!-- Logo on the left -->
      <a href="/" class="p-0 m-0 text-decoration-none">
        <img src="https://www.biomedthai.com/images/logo.png" style="max-height:80px;" alt="biomed diagnostic">
      </a>
      <!-- Navigation on the right (or center, adjust as needed) -->
      <ul class="nav my-0 text-small">
        <li>
          <a href="index.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-user"></i>
            User
          </a>
        </li>
        <li>
          <a href="crm.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-crm-computer"></i>
            CRM
          </a>
        </li>
        <li>
          <a href="event.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-calendar-day"></i>
            Event
          </a>
        </li>
        <li>
          <a href="project.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-diagram-project"></i>
            Project
          </a>
        </li>
        <li>
          <a href="contact.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-review"></i>
            Contact
          </a>
        </li>
        <li>
          <a href="helpdesk.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-wrench-alt"></i>
            Helpdesk
          </a>
        </li>
        <li>
          <a href="#" class="nav-link biomed-disabled-nav disabled rounded">
            <i class="fi fi-rr-file-invoice"></i>
            Invoice & Order
          </a>
        </li>
        <li>
          <a href="inventory.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-box-alt"></i>
            Inventory
          </a>
        </li>
        <li>
          <a href="#" class="nav-link biomed-disabled-nav disabled rounded">
            <i class="fi fi-rr-shipping-fast"></i>
            Delivery
          </a>
        </li>
        <li>
          <a href="visualization.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-analyse-alt"></i>
            Data Visualization
          </a>
        </li>
        <li>
          <a href="d3.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-network-analytic"></i>
            D3 Network
          </a>
        </li>
        <li>
          <a href="management.html" class="nav-link biomed-hover rounded">
            <i class="fi fi-rr-user-gear"></i>
            Management
          </a>
        </li>
      </ul>
    </div>
  </div>
</div>

  `;
}
// Workspace header is mounted by biomed-navbar.js.


function clearsession(){
  clearCache();
  setTimeout(() => { location.reload(); }, 500);
}


function getTargets(callback,query = null){
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url + "/biomedapi/targets", true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", "Bearer " + readToken());
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4) {
      if (xhr.status === 200) {
        var targets = JSON.parse(xhr.responseText);
        callback(null, targets);
      } else {
        var error = new Error(xhr.responseText);
        error.message = error.message + "\nRequest:"+JSON.stringify(query);
        callback(error, null);
      }
    }
  };
  if(query !== null){
    xhr.send(JSON.stringify(query));
  }
  else{
    xhr.send();
  }

}
function formatDateTime(date) {
  const options = { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' };
  const formattedDate = new Date(date).toLocaleDateString(undefined, options);
  return formattedDate;
}
function formatDateOnly(date) {
  const options = { day: '2-digit', month: 'long', year: 'numeric' };
  const formattedDate = new Date(date).toLocaleDateString(undefined, options);
  return formattedDate;
}
function formatTimeOnly(date) {
  const options = { hour: '2-digit', minute: '2-digit' };
  const formattedTime = new Date(date).toLocaleTimeString(undefined, options);
  return formattedTime;
}
function getRemainingDays(endDate, startDate = null, formatting = true) {
  const today = startDate === null? new Date(): new Date(startDate);
  const targetDate = new Date(endDate);
  const timeDiff = targetDate.getTime() - today.getTime();
  const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));
  return formatting? daysDiff >= 0 ? (daysDiff <= 30 ? '⚠️' : '') + daysDiff + " Days remaining" : 'Overdue ' + Math.abs(daysDiff) + ' Days': daysDiff;
}

function getQuarterAndYearByDate(date) {
  const month = date.getMonth();
  const year = month <=3 ? date.getFullYear(): date.getFullYear()+1;
  let quarter;
  if(month == 4||month == 5||month == 6){
    quarter = "Q1";
  }
  if(month == 7||month == 8||month == 9){
    quarter = "Q2";
  }
  if(month == 10||month == 11||month == 0){
    quarter = "Q3";
  } 
  if(month == 1||month == 2||month == 3){
    quarter = "Q4";
  }

  let output = {
    input: date,
    quarter: quarter,
    month: month,
    year: year
  }

  console.log('Date to Quarter',output);
  return output;
}

function AutoComma(number) {
  return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}


//section of helpdesk
function GetHelpdeskPipeline(callback, force) {
  if (force === true) {
    sessionStorage.removeItem("helpdeskPipeline");
  }
  var helpdeskPipeline = sessionStorage.getItem("helpdeskPipeline");
  if (helpdeskPipeline !== null) {
    callback(null, JSON.parse(helpdeskPipeline));
  } else {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url + "/biomedapi/v2/helpdesk/pipeline", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onload = function () {
      if (xhr.status === 200) {
        var helpdeskPipeline = JSON.parse(xhr.responseText);
        helpdeskPipeline.sort((a, b) => a.Order - b.Order);
        sessionStorage.setItem("helpdeskPipeline", JSON.stringify(helpdeskPipeline));
        callback(null, helpdeskPipeline);
      } else {
        callback(new Error(xhr.responseText), null);
      }
    };
    xhr.onerror = function () {
      callback(new Error("Request failed"), null);
    };
    xhr.send();
  }
}

function getTickets(callback, query = null) {
  const token = readToken();
  const xhr = new XMLHttpRequest();

  if (query === null) {
    xhr.open("GET", url + "/biomedapi/v2/helpdesk/tickets", true);
  } else {
    xhr.open("POST", url + "/biomedapi/v2/helpdesk/tickets", true);
  }

  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.setRequestHeader("Authorization", `Bearer ${token}`);
  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        const tickets = JSON.parse(xhr.responseText);
        callback(null, tickets);
      } else {
        callback(new Error(xhr.responseText), null);
      }
    }
  };

  if (query !== null) {
    xhr.send(JSON.stringify(query));
  } else {
    xhr.send();
  }
}

function priorityFormatting(value) {
  var priority = 0;
  var intvalue = parseInt(value);
  switch (intvalue) {
    case -1:
      priority = "Any Priority📄";
          break;
    case 0:
      priority = "No Priority💤";
      break;
    case 1:
      priority = "Low🧊";
      break;
    case 2:
      priority = "Medium⚒️";
      break;
    case 3:
      priority = "High⚡";
      break;
    case 4:
      priority = "Urgent🔥";
      break;
    case 5:
      priority = "Critical❤️‍🔥";
      break;
    default:
      priority = "Unknown❓";
      break;
  }
  return priority;
}

function uploadFile(callback) {
  const input = document.createElement('input');
  input.type = 'file';
  input.onchange = function(event) {
    const file = event.target.files[0];
    if (!file) {
      callback(new Error("No file selected"), null);
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    

    const xhr = new XMLHttpRequest();
    xhr.open('POST', url + '/biomedapi/misc/uploadfile', true);
    xhr.setRequestHeader('Authorization', 'Bearer ' + readToken());
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          //console.log(xhr.responseText);
          callback(null, xhr.responseText);
        } else {
          console.error(xhr.status,xhr.responseText);
          callback(new Error(xhr.responseText), null);
        }
      }
    };
    
    xhr.send(formData);
  };
  input.click();
}
/*
var initialValues = {};
function cachingObject(){

  initialValues = {}; // Reset previous values

  document.querySelectorAll('input, select, textarea').forEach(element => {
      const key = element.name || element.id;

      if (element.tagName === 'SELECT' && element.multiple) {
          // Store an array of selected values for multiple selects
          initialValues[key] = Array.from(element.selectedOptions).map(option => option.value);
      } else {
          initialValues[key] = element.value;
      }
  });

}

function compareChange() {
  let changes = [];

    document.querySelectorAll('input, select, textarea').forEach(element => {
        const key = element.name || element.id;
        let newValue;

        if (element.tagName === 'SELECT' && element.multiple) {
            newValue = Array.from(element.selectedOptions).map(option => option.value);
        } else {
            newValue = element.value;
        }

        // Check for changes (array comparison for multi-select)
        if (JSON.stringify(initialValues[key]) !== JSON.stringify(newValue)) {
            changes.push({
                field: key,
                oldValue: initialValues[key],
                newValue: newValue
            });
        }
    });

    //console.log('Changes:', changes);
    return changes; // Returns an array of changed fields

  
}*/
//Campare Change Version 2
var initialValues = {};

function cachingObject() {
    initialValues = {}; // Reset previous values


    const selects = document.querySelectorAll('.multi-select');
    
    
    selects.forEach(el => {
        initialValues[el.id] = Array.from(el.querySelectorAll('input'))
          .map(input => input.value)
          .filter(value => value.trim() !== ""); // Store non-empty selected values for multi-selects
        initialValues[el.id].Multiple = true; // Mark as multiple select
    });


    document.querySelectorAll('input, select, textarea').forEach(element => {
        const key = element.name || element.id;
        let value;

        if (element.tagName === 'SELECT' && element.multiple) {
            // Store selected values for multiple selects
            value = Array.from(element.selectedOptions).map(option => option.value);
        } else if (element.type === "checkbox") {
            value = element.checked; // Store boolean for checkboxes
        } else if (element.type === "radio") {
            if (element.checked) {
                value = element.id; // Store radio ID if checked
            } else {
                return; // Skip unchecked radios
            }
        } else {
            value = element.value.trim(); // Trim spaces
        }

        // Store only non-empty values
        if (value !== "" && value !== null && value !== undefined) {
            initialValues[key] = value;
        }
    });

    // Cache Pipeline Status (daisyUI Steps)
    if (typeof getSelectedPipelineId === 'function' && getSelectedPipelineId()) {
        initialValues['pipelineStatus'] = getSelectedPipelineId();
    }

    // Cache Responsibles (Users MultiSelect)
    if (typeof getSelectedUserIds === 'function') {
        var userIds = getSelectedUserIds().map(id => id.toString());
        // Include primary user if available
        if (typeof primaryUserId !== 'undefined' && primaryUserId) {
            userIds = [primaryUserId.toString()].concat(userIds);
        }
        initialValues['responsibles'] = userIds;
    }

    // Cache Main Contact (Helpdesk)
    if (typeof mainContactMS !== 'undefined' && mainContactMS && typeof mainContactMS.getValues === 'function') {
        initialValues['mainContact'] = mainContactMS.getValues();
    }

    // Cache Additional Contacts (Helpdesk)
    if (typeof additionalContactsMS !== 'undefined' && additionalContactsMS && typeof additionalContactsMS.getValues === 'function') {
        initialValues['additionalContacts'] = additionalContactsMS.getValues();
    }

    // Cache HelpDeskItems count (for change tracking)
    if (typeof currentHelpDeskItems !== 'undefined' && Array.isArray(currentHelpDeskItems)) {
        initialValues['helpDeskItemsCount'] = currentHelpDeskItems.length;
        initialValues['helpDeskItemsData'] = JSON.stringify(currentHelpDeskItems);
    }

    //console.log("Cached Values:", initialValues);
}

async function compareChange() {
    let changes = [];

    Object.keys(initialValues).forEach(key => {
      if (initialValues[key].Multiple) {
      const currentValues = Array.from(document.querySelectorAll(`#${key} input`))
        .map(input => input.value)
        .filter(value => value.trim() !== ""); // Skip empty values
      if (JSON.stringify(initialValues[key]) !== JSON.stringify(currentValues)) {
        const oldValue = [...initialValues[key]]; // Create a shallow copy of the original object
        delete oldValue.Multiple; // Remove the Multiple property from the copy
        changes.push({
        field: key,
        oldValue: oldValue,
        newValue: currentValues
        });
      }
      }
    });

    document.querySelectorAll('input, select, textarea').forEach(element => {
        const key = element.name || element.id;
        let newValue;
        
        // Skip read-only fields that shouldn't be tracked
        if (key === 'ticketCreator' || key === 'ticketCreatorId' || key === 'creation') {
            return;
        }
        
        if (element.tagName === 'SELECT' && (element.multiple || element.multiple === "multiple")) {
            newValue = Array.from(element.selectedOptions).map(option => option.value);
        } else if (element.type === "checkbox") {
        
            newValue = element.checked; // Store boolean for checkboxes
        } else if (element.type === "radio") {
            if (element.checked) {
                newValue = element.id; // Get radio ID if checked
            } else {
                return; // Skip unchecked radios
            }
        } else if (element.type === "hidden") {
          return; // Skip hidden inputs
        }
        else {
            newValue = element.value.trim();
        }

        if (newValue !== "" && newValue !== null && newValue !== undefined) {
            const oldValue = initialValues[key];

            if (element.type === "radio" && oldValue !== newValue) {
                // For radio buttons, mark old one as false and new one as true
                changes.push({ field: oldValue, newValue: false, oldValue: true });
                changes.push({ field: newValue, newValue: true, oldValue: false });
            } else if (JSON.stringify(oldValue) !== JSON.stringify(newValue)) {
                changes.push({
                    field: key,
                    oldValue: typeof(oldValue)==='boolean'? oldValue: oldValue || "N/A",
                    newValue: newValue
                });
            }
        }
    });

    // Compare Pipeline Status (daisyUI Steps)
    if (typeof getSelectedPipelineId === 'function') {
        const oldPipeline = initialValues['pipelineStatus'];
        const newPipeline = getSelectedPipelineId();
        if (oldPipeline && newPipeline && oldPipeline !== newPipeline) {
            changes.push({
                field: 'pipelineStatus',
                oldValue: oldPipeline,
                newValue: newPipeline
            });
        }
    }

    // Compare Responsibles (Users MultiSelect)
    if (typeof getSelectedUserIds === 'function') {
        const oldResponsibles = initialValues['responsibles'] || [];
        var newUserIds = getSelectedUserIds().map(id => id.toString());
        // Include primary user if available
        if (typeof primaryUserId !== 'undefined' && primaryUserId) {
            newUserIds = [primaryUserId.toString()].concat(newUserIds);
        }
        if (JSON.stringify(oldResponsibles) !== JSON.stringify(newUserIds)) {
            changes.push({
                field: 'responsibles',
                oldValue: oldResponsibles,
                newValue: newUserIds
            });
        }
    }

    // Compare Main Contact (Helpdesk)
    if (typeof mainContactMS !== 'undefined' && mainContactMS && typeof mainContactMS.getValues === 'function') {
        const oldMainContact = initialValues['mainContact'] || [];
        const newMainContact = mainContactMS.getValues();
        if (JSON.stringify(oldMainContact) !== JSON.stringify(newMainContact)) {
            changes.push({
                field: 'mainContact',
                oldValue: oldMainContact,
                newValue: newMainContact
            });
        }
    }

    // Compare Additional Contacts (Helpdesk)
    if (typeof additionalContactsMS !== 'undefined' && additionalContactsMS && typeof additionalContactsMS.getValues === 'function') {
        const oldAdditionalContacts = initialValues['additionalContacts'] || [];
        const newAdditionalContacts = additionalContactsMS.getValues();
        if (JSON.stringify(oldAdditionalContacts) !== JSON.stringify(newAdditionalContacts)) {
            changes.push({
                field: 'additionalContacts',
                oldValue: oldAdditionalContacts,
                newValue: newAdditionalContacts
            });
        }
    }

    // Compare HelpDeskItems
    if (typeof currentHelpDeskItems !== 'undefined' && Array.isArray(currentHelpDeskItems)) {
        const oldItemsCount = initialValues['helpDeskItemsCount'] || 0;
        const newItemsCount = currentHelpDeskItems.length;
        const oldItemsData = initialValues['helpDeskItemsData'] || '[]';
        const newItemsData = JSON.stringify(currentHelpDeskItems);
        
        if (oldItemsData !== newItemsData) {
            changes.push({
                field: 'helpDeskItems',
                oldValue: `${oldItemsCount} items`,
                newValue: `${newItemsCount} items`
            });
        }
    }

    //console.log('Changes:', changes);
    let newChanges = await changeParse(changes);
    return newChanges;
}

async function changeParse(changes) {
  let newChanges = [];
  for (const change of changes) {
    // Skip fields with empty names
    if (!change.field || change.field.trim() === '') {
      continue;
    }
    
    let readableChange = {};
    readableChange.field = change.field;
    readableChange.oldValue = change.oldValue;
    readableChange.newValue = change.newValue;
    
    // Handle mainContactsSelecter (single main contact)
    if (change.field === "mainContactsSelecter") {
      readableChange.field = "Main Contact";
      // Old value
      if (change.oldValue && change.oldValue !== "" && change.oldValue !== "N/A") {
        await new Promise((resolve) => {
          getContactById(change.oldValue, (error, contact) => {
            if (error || !contact) {
              readableChange.oldValue = "Contact(" + change.oldValue + ")";
            } else {
              readableChange.oldValue = contact.Name + "(" + change.oldValue + ")";
            }
            resolve();
          });
        });
      } else {
        readableChange.oldValue = "N/A";
      }
      // New value
      if (change.newValue && change.newValue !== "" && change.newValue !== "N/A") {
        await new Promise((resolve) => {
          getContactById(change.newValue, (error, contact) => {
            if (error || !contact) {
              readableChange.newValue = "Contact(" + change.newValue + ")";
            } else {
              readableChange.newValue = contact.Name + "(" + change.newValue + ")";
            }
            resolve();
          });
        });
      } else {
        readableChange.newValue = "N/A";
      }
    }
    
    if (change.field === "contactsSelecter"||change.field === "contactsDropdown") {
      readableChange.field = "Additional Contacts";
      readableChange.oldValue = [];
      for (const element of change.oldValue) {
        await new Promise((resolve, reject) => {
          getContactById(element, (error, contact) => {
            if (error) {
              console.error('Failed to fetch contact:', error);
              reject(error);
              return;
            }
            readableChange.oldValue.push(contact.Name + "(" + element + ")");
            resolve();
          });
        });
      }

      readableChange.newValue = [];
      for (const element of change.newValue) {
        await new Promise((resolve, reject) => {
          getContactById(element, (error, contact) => {
            if (error) {
              console.error('Failed to fetch contact:', error);
              reject(error);
              return;
            }
            readableChange.newValue.push(contact.Name + "(" + element + ")");
            resolve();
          });
        });
      }
    }
    if (change.field === "productsDropdown") {
      readableChange.oldValue = [];
      for (const element of change.oldValue) {
        await new Promise((resolve, reject) => {
          getProductById(element, (error, contact) => {
            if (error) {
              console.error('Failed to fetch contact:', error);
              reject(error);
              return;
            }
            readableChange.oldValue.push(contact.Name + "(" + element + ")");
            resolve();
          });
        });
      }

      readableChange.newValue = [];
      for (const element of change.newValue) {
        await new Promise((resolve, reject) => {
          getProductById(element, (error, contact) => {
            if (error) {
              console.error('Failed to fetch contact:', error);
              reject(error);
              return;
            }
            readableChange.newValue.push(contact.Name + "(" + element + ")");
            resolve();
          });
        });
      }
    }
    // Skip usersSelecter - use responsibles instead
    if (change.field === "usersSelecter" || change.field === "usersDropdown") {
      continue; // Skip this field, we use 'responsibles' field instead
    }
    if (change.field === "saleArea"){
      readableChange.oldValue = change.oldValue !== "N/A"&&change.oldValue !=="-1"? (await new Promise((resolve, reject) => {
        getSaleAreaById(change.oldValue).then(resolve).catch(reject);
      })).Name+"("+change.oldValue+")":"N/A";

      readableChange.newValue = change.newValue!=="N/A"&&change.newValue !=="-1"?(await new Promise((resolve, reject) => {
        getSaleAreaById(change.newValue).then(resolve).catch(reject);
      })).Name+"("+change.newValue+")":"N/A";
    }
    if (change.field === "product" || change.field === "modalProduct") {
      readableChange.oldValue = change.oldValue !== "N/A"&&change.oldValue !=="-1"? (await new Promise((resolve, reject) => {
        getProductById(change.oldValue, (error, product) => {
          if (error) {
            console.error('Failed to fetch product:', error);
            reject(error);
            return;
          }
          resolve(product);
        });
      })).Name+"("+change.oldValue+")":"N/A";
      readableChange.newValue = change.newValue!=="N/A"&&change.newValue !=="-1"? (await new Promise((resolve, reject) => {
        getProductById(change.newValue, (error, product) => {
          if (error) {
            console.error('Failed to fetch product:', error);
            reject(error);
            return;
          }
          resolve(product);
        });
      })).Name+"("+change.newValue+")":"N/A";
    }
    if (change.field.startsWith("pipeline")) {
      const label = document.querySelector(`label[for="${change.field}"]`);
      if (label) {
        readableChange.field = label.textContent.trim() + " (" + change.field.replace("pipeline", "").trim()+")";
      }
    }
    // Handle Pipeline Status (daisyUI Steps)
    if (change.field === "pipelineStatus") {
      readableChange.field = "Pipeline Status";
      // Get pipeline name from step element
      const oldStep = document.querySelector(`#pipelineSelection li[data-pipeline-id="${change.oldValue}"]`);
      const newStep = document.querySelector(`#pipelineSelection li[data-pipeline-id="${change.newValue}"]`);
      readableChange.oldValue = oldStep ? oldStep.textContent.trim() : change.oldValue;
      readableChange.newValue = newStep ? newStep.textContent.trim() : change.newValue;
    }

    // Handle Main Contact (Helpdesk)
    if (change.field === "mainContact") {
      readableChange.field = "Main Contact";
      readableChange.oldValue = [];
      readableChange.newValue = [];
      
      for (const contactId of (change.oldValue || [])) {
        await new Promise((resolve) => {
          getContactById(contactId, (error, contact) => {
            if (error || !contact) {
              readableChange.oldValue.push("Contact(" + contactId + ")");
            } else {
              readableChange.oldValue.push(contact.Name + "(" + contactId + ")");
            }
            resolve();
          });
        });
      }
      
      for (const contactId of (change.newValue || [])) {
        await new Promise((resolve) => {
          getContactById(contactId, (error, contact) => {
            if (error || !contact) {
              readableChange.newValue.push("Contact(" + contactId + ")");
            } else {
              readableChange.newValue.push(contact.Name + "(" + contactId + ")");
            }
            resolve();
          });
        });
      }
    }

    // Handle Additional Contacts (Helpdesk)
    if (change.field === "additionalContacts") {
      readableChange.field = "Additional Contacts";
      readableChange.oldValue = [];
      readableChange.newValue = [];
      
      for (const contactId of (change.oldValue || [])) {
        await new Promise((resolve) => {
          getContactById(contactId, (error, contact) => {
            if (error || !contact) {
              readableChange.oldValue.push("Contact(" + contactId + ")");
            } else {
              readableChange.oldValue.push(contact.Name + "(" + contactId + ")");
            }
            resolve();
          });
        });
      }
      
      for (const contactId of (change.newValue || [])) {
        await new Promise((resolve) => {
          getContactById(contactId, (error, contact) => {
            if (error || !contact) {
              readableChange.newValue.push("Contact(" + contactId + ")");
            } else {
              readableChange.newValue.push(contact.Name + "(" + contactId + ")");
            }
            resolve();
          });
        });
      }
    }

    // Handle Responsibles (Users MultiSelect)
    if (change.field === "responsibles") {
      readableChange.field = "Responsibles";
      // Convert user IDs to names
      readableChange.oldValue = [];
      readableChange.newValue = [];
      
      // Resolve old user IDs
      for (const userId of change.oldValue) {
        await new Promise((resolve) => {
          getUserById((error, user) => {
            if (error || !user) {
              readableChange.oldValue.push("User(" + userId + ")");
            } else {
              var fullName = (user.FirstName || '') + ' ' + (user.LastName || '');
              readableChange.oldValue.push(fullName.trim() + "(" + userId + ")");
            }
            resolve();
          }, userId);
        });
      }
      
      // Resolve new user IDs
      for (const userId of change.newValue) {
        await new Promise((resolve) => {
          getUserById((error, user) => {
            if (error || !user) {
              readableChange.newValue.push("User(" + userId + ")");
            } else {
              var fullName = (user.FirstName || '') + ' ' + (user.LastName || '');
              readableChange.newValue.push(fullName.trim() + "(" + userId + ")");
            }
            resolve();
          }, userId);
        });
      }
    }

    // Handle Assigned User
    if (change.field === "assignedUser") {
      readableChange.field = "Assigned Responsible";
      // Old value
      if (change.oldValue && change.oldValue !== "" && change.oldValue !== "N/A" && change.oldValue !== "-1") {
        await new Promise((resolve) => {
          getUserById((error, user) => {
            if (error || !user) {
              readableChange.oldValue = "User(" + change.oldValue + ")";
            } else {
              var fullName = (user.FirstName || '') + ' ' + (user.LastName || '');
              readableChange.oldValue = fullName.trim() + "(" + change.oldValue + ")";
            }
            resolve();
          }, change.oldValue);
        });
      } else {
        readableChange.oldValue = "Unassigned";
      }
      // New value
      if (change.newValue && change.newValue !== "" && change.newValue !== "N/A" && change.newValue !== "-1") {
        await new Promise((resolve) => {
          getUserById((error, user) => {
            if (error || !user) {
              readableChange.newValue = "User(" + change.newValue + ")";
            } else {
              var fullName = (user.FirstName || '') + ' ' + (user.LastName || '');
              readableChange.newValue = fullName.trim() + "(" + change.newValue + ")";
            }
            resolve();
          }, change.newValue);
        });
      } else {
        readableChange.newValue = "Unassigned";
      }
    }

    newChanges.push(readableChange);
  }
  return newChanges;
}



const charset = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // No confusing chars like O/0/I/1

function intToFourDigitString(num) {
    let base = charset.length;
    let str = "";
    
    for (let i = 0; i < 4; i++) {
        str = charset[num % base] + str;
        num = Math.floor(num / base);
    }

    return str;
}

function fourDigitStringToInt(str) {
    let base = charset.length;
    let num = 0;
    
    for (let i = 0; i < str.length; i++) {
        num = num * base + charset.indexOf(str[i]);
    }

    return num;
}

// Example usage:
//let encoded = intToFourDigitString(12345);
////console.log(encoded); // Example: "7BFD"

//let decoded = fourDigitStringToInt(encoded);
////console.log(decoded); // 12345

async function processTargets(targets) {
  if (!targets || targets.length === 0) {
      return targets;
  }
  const sortedTargets = targets.sort((a, b) => new Date(b.EndDate).getTime() - new Date(a.EndDate).getTime());
  sortedTargets.forEach((target, index) => {
      target.order = index + 1;
  });
  //console.log("Sorted Targets",sortedTargets);

  //query and target processing
  const totalQuery = {};
  for (const target of sortedTargets) {
      if (!totalQuery.SaleAreaIDs) {
          totalQuery.SaleAreaIDs = [];
      }
      if (!totalQuery.ProductIDs) {
          totalQuery.ProductIDs = [];
      }
      if (!totalQuery.SaleAreaIDs.includes(target.SaleAreaID)) {
          totalQuery.SaleAreaIDs.push(target.SaleAreaID);
      }
      if (!totalQuery.ProductIDs.includes(target.ProductID)) {
          totalQuery.ProductIDs.push(target.ProductID);
      }
      const product = await promiseProductById(target.ProductID);
      const saleArea = await promiseSaleAreaById(target.SaleAreaID);
      target.Product = product;
      target.SaleArea = saleArea;
      target.Leads = [];
      target.Color = await getColor(target.ProductID);
  }
  const minStartDate = sortedTargets.reduce((min, target) => new Date(target.StartDate) < min ? new Date(target.StartDate) : min, new Date(sortedTargets[0].StartDate));
  const maxEndDate = sortedTargets.reduce((max, target) => new Date(target.EndDate) > max ? new Date(target.EndDate) : max, new Date(sortedTargets[0].EndDate));

  //console.log("Min Start Date:", minStartDate);
  //console.log("Max End Date:", maxEndDate);
  totalQuery.ExpectedStart = timeFormater(minStartDate);
  totalQuery.ExpectedEnd = timeFormater(maxEndDate);
  totalQuery.DeepSearch = true;
  //console.log("Total Query",totalQuery);
  const totalLeads = await promiseLeads(totalQuery);
  //console.log("Total Leads",totalLeads);

  for (const lead of totalLeads) {
      const target = sortedTargets.find(target => 
          target.ProductID === lead.ProductId && 
          target.SaleAreaID === lead.SaleAreaId &&
          new Date(lead.Expected) >= new Date(target.StartDate) &&
          new Date(lead.Expected) <= new Date(target.EndDate)
      );
      if (target) {
          if (!target.Leads) {
              target.Leads = [];
          }
          target.Leads.push(lead);
      }
  }
  return sortedTargets;
}

//it's time to promise!
async function promiseMyUser(){
  return new Promise((resolve, reject) => {
    myUserRequest((error, user) => {
          if (error) {
              console.error('Failed to fetch user:', error);
              reject(error);
              return;
          }
          resolve(user);
      });
  });
}

async function promiseLeads(query = null){
  return new Promise((resolve, reject) => {
      getLeads((error, leads) => {
          if (error) {
              console.error('Failed to fetch leads:', error);
              reject(error);
              return;
          }
          resolve(leads);
      },query);
  });
}
async function promiseUsers(force = false) {
  return new Promise((resolve, reject) => {
    getUsers((error, users) => {
      if (error) {
        console.error('Failed to fetch users:', error);
        reject(error);
        return;
      }
      resolve(users);
    }, force);
  });
}

async function promiseUserById(id) {
  return new Promise((resolve, reject) => {
      getUserById((error, user) => {
          if (error) {
              console.error('Failed to fetch contact:', error);
              reject(error);
              return;
          }
          //readableChange.oldValue.push(user.FirstName + " " + user.LastName + "(" + id + ")");
          resolve(user);
      }, id);
  });
}
async function promiseSaleAreaById(id) {
  return new Promise((resolve, reject) => {
      getSaleAreaById(id).then(resolve).catch(reject);
  });
}

async function promiseProductById(id) {
  return new Promise((resolve, reject) => {
      getProductById(id,(error, product) => {
          if (error) {
              console.error('Failed to fetch product:', error);
              reject(error);
              return;
          }
          resolve(product);
      });
  });
}
async function promiseProducts(force = false) {
  return new Promise((resolve, reject) => {
    getProducts((error, products) => {
      if (error) {
        console.error('Failed to fetch products:', error);
        reject(error);
        return;
      }
      resolve(products);
    }, force);
  });
}

async function promiseContacts(force = false) {
  return new Promise((resolve, reject) => {
    getContacts((error, contacts) => {
      if (error) {
        console.error('Failed to fetch contacts:', error);
        reject(error);
        return;
      }
      resolve(contacts);
    }, force);
  });
}
async function promiseContactById(id) {
  return new Promise((resolve, reject) => {
      getContactById(id,(error, contact) => {
          if (error) {
              console.error('Failed to fetch contact:', error);
              reject(error);
              return;
          }
          resolve(contact);
      });
  });
}
let pipelinesCache = [];
async function promiseCRMPipelines(){ 
  return new Promise((resolve, reject) => {
      if(pipelinesCache.length > 0){
          resolve(pipelinesCache);
          return;
      }
  getPipelines((error, pipelines) => {
      if (error) {
          console.error('Failed to fetch pipelines:', error);
          reject(error);
          return;
      }
      //console.log("CRM Pipelines",pipelines);
      pipelinesCache = pipelines;
      resolve(pipelines);
  });
});
}

async function promiseCRMPipelineById(id) {
  try {
      let pipelines = await promiseCRMPipelines();
      const pipeline = pipelines.find(p => p.Id === id);
      if (!pipeline) {
          //throw new Error('Pipeline not found');
          return {Id:id,PipelineName:"Unknown"};
      }
      return pipeline;
  } catch (error) {
      console.error(error);
      throw error;
  }
}

async function promiseTargets(query = null){
  return new Promise((resolve, reject) => {
      getTargets((error, targets) => {
          if (error) {
              console.error('Failed to fetch targets:', error);
              reject(error);
              return;
          }
          resolve(targets);
      },query);
  });
}

async function promiseEvents(query = null) {
  return new Promise((resolve, reject) => {
    getEvents((error, events) => {
      if (error) {
        console.error('Failed to fetch events:', error);
        reject(error);
        return;
      }
      resolve(events);
    }, query);
  });
}

async function promiseEventById(id) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", `${url}/biomedapi/v2/event/${id}`, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          const event = JSON.parse(xhr.responseText);
          resolve(event);
        } else {
          reject(new Error(xhr.responseText));
        }
      }
    };
    xhr.onerror = function () {
      reject(new Error("Request failed"));
    };
    xhr.send();
  });
}

async function promiseColorById(id) {
  return new Promise(async (resolve, reject) => {
    try {
      const color = await getColor(id);
      resolve(color);
    } catch (error) {
      console.error('Failed to fetch color:', error);
      reject(error);
    }
  });
}

async function v2_promiseEvents(filter = {DeepSearch:true}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url + "/biomedapi/v2/event", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "Bearer " + readToken());
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          const events = JSON.parse(xhr.responseText);
          resolve(events);
        } else {
          reject(new Error(xhr.responseText));
        }
      }
    };
    xhr.onerror = function () {
      reject(new Error("Request failed"));
    };
    xhr.send(filter ? JSON.stringify(filter) : filter);
  });
}

function Label(color, text,objectMode = false) {

  const element = document.createElement("div");
  element.className = "m-1 p-1 rounded-5 c-shadow text-truncate";
  element.style.backgroundColor = "white";

  const colorSpan = document.createElement("span");
  colorSpan.className = "m-0 p-0 c-text-shadow";
  colorSpan.style.color = color;
  colorSpan.textContent = "⬤ ";

  const textSpan = document.createElement("span");
  textSpan.className = "m-0 p-0";
  textSpan.style.fontSize = "smaller";
  textSpan.textContent = text;

  element.appendChild(colorSpan);
  element.appendChild(textSpan);


  return (!objectMode)?`<div class="m-1 p-1 rounded-5 c-shadow text-truncate" style="background-color:white">
  <span class="m-0 p-0 c-text-shadow" style="color:${color}">⬤ </span>
  <span class="m-0 p-0" style="font-size:smaller;">${text}</span>
</div>`:element;
}

function showLoader() {
  // Check if loader already exists
  if (document.getElementById('loader')) {
    return; // Loader already exists, no need to create a new one
  }
  const loaderHTML = `
    <div class="position-fixed top-0 start-0 w-100 h-100" style="z-index: 99999; background-color: rgba(0, 0, 0, 0.5);" id="loader">
      <div class="d-flex justify-content-center align-items-center h-100">
        <div class="bg-white p-4 rounded-5">
          <div aria-label="Orange and tan hamster running in a metal wheel" role="img" class="wheel-and-hamster mx-auto">
            <div class="wheel"></div>
            <div class="hamster">
              <div class="hamster__body">
                <div class="hamster__head">
                  <div class="hamster__ear"></div>
                  <div class="hamster__eye"></div>
                  <div class="hamster__nose"></div>
                </div>
                <div class="hamster__limb hamster__limb--fr"></div>
                <div class="hamster__limb hamster__limb--fl"></div>
                <div class="hamster__limb hamster__limb--br"></div>
                <div class="hamster__limb hamster__limb--bl"></div>
                <div class="hamster__tail"></div>
              </div>
            </div>
            <div class="spoke"></div>
          </div>
          <p class="text-center mt-3" id="loadingText">Loading<span id="dots">.</span></p>
          
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', loaderHTML);
  const dotsElement = document.getElementById('dots');
  let dotCount = 1;
  dotsElement.LoadSpin =  setInterval(() => {
    dotCount = (dotCount % 3) + 1; // Cycle through 1 to 3
    dotsElement.textContent = '.'.repeat(dotCount);
  }, 500); // Update every 500ms

  // After 15 seconds, show error label, logout button, and errors box
  setTimeout(() => {
    const loader = document.getElementById('loader');
    if (!loader) return;
    const loaderContent = loader.querySelector('.bg-white');
    if (!loaderContent || loaderContent.querySelector('#loaderError')) return;
    const errorHTML = `
      <div id="loaderError" class="text-center mt-3">
        <p class="mb-2">Something went wrong?</p>
        <button class="btn c-con-primary" onclick="removeToken()">Logout</button>
        <button class="btn btn-secondary ms-2" onclick="alert('Please press F12 or Ctrl+Shift+I to open Developer Tools')">Developer Mode</button>
        <div class="mt-2 d-none">
          <textarea id="loaderErrors" class="form-control" rows="5" readonly></textarea>
        </div>
      </div>
    `;
    loaderContent.insertAdjacentHTML('beforeend', errorHTML);
    // populate console errors into textarea
    const errorList = window._loaderConsoleErrors || [];
    if (errorList.length > 0) {
      document.getElementById('loaderErrors').value = errorList.join('\n');
    }
  }, 15000);
}


function hideLoader() {
  // Check if loader exists
  if (!document.getElementById('loader')) {
    return; // Loader doesn't exist, no need to remove it
  }
  const loader = document.getElementById('loader');
  if (loader) {
    loader.remove();
  }
  const dotsElement = document.getElementById('dots');
  if (dotsElement && dotsElement.LoadSpin) {
    clearTimeout(dotsElement.LoadSpin);
    dotsElement.LoadSpin = null;
  }
}
;

(function() {
  // Capture console errors for loader error display
  window._loaderConsoleErrors = [];
  const origConsoleError = console.error;
  console.error = function(...args) {
    // capture error message and stack location
    const msg = args.map(arg => {
      try { return JSON.stringify(arg); } catch { return String(arg); }
    }).join(' ');
    const stackLine = (new Error()).stack.split("\n")[2] || '';
    window._loaderConsoleErrors.push(`${msg} at ${stackLine.trim()}`);
    origConsoleError.apply(console, args);
  };
  window.onerror = function(message, source, lineno, colno, error) {
    window._loaderConsoleErrors.push(`${message} at ${source}:${lineno}:${colno}`);
  };
  // Capture unhandled Promise rejections
  window.addEventListener('unhandledrejection', function(event) {
    const reason = event.reason instanceof Error ? event.reason.stack : String(event.reason);
    window._loaderConsoleErrors.push(`UnhandledRejection: ${reason}`);
  });
})();
// Shared session adapter: the API ignores this compatibility marker and checks its HttpOnly cookie.
readToken=function(){return window.CRMContext?'shared-session':null;};
removeToken=async function(){const r=await fetch('/api/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(r.ok){sessionStorage.removeItem('myUser');location.assign('/?portal=1')}};
sendLoginRequest=function(username,password,callback){location.assign('/?portal=1&next=%2Fcrm%2Findex.html');if(callback)callback(new Error('Use Staff Portal sign-in'));};
