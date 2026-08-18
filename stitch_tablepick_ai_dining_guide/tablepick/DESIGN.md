---
name: Tablepick
colors:
  surface: '#1e100d'
  surface-dim: '#1e100d'
  surface-bright: '#483531'
  surface-container-lowest: '#180a08'
  surface-container-low: '#271815'
  surface-container: '#2c1c19'
  surface-container-high: '#372623'
  surface-container-highest: '#43302d'
  on-surface: '#fadcd7'
  on-surface-variant: '#e4beb7'
  inverse-surface: '#fadcd7'
  inverse-on-surface: '#3e2c29'
  outline: '#ab8983'
  outline-variant: '#5b403b'
  surface-tint: '#ffb4a7'
  primary: '#ffb4a7'
  on-primary: '#670400'
  primary-container: '#ff553d'
  on-primary-container: '#5b0300'
  inverse-primary: '#b91e0d'
  secondary: '#e3c290'
  on-secondary: '#412d07'
  secondary-container: '#5c451e'
  on-secondary-container: '#d4b483'
  tertiary: '#8aceff'
  on-tertiary: '#00344e'
  tertiary-container: '#3499d3'
  on-tertiary-container: '#002d44'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad4'
  primary-fixed-dim: '#ffb4a7'
  on-primary-fixed: '#400200'
  on-primary-fixed-variant: '#920800'
  secondary-fixed: '#ffdeac'
  secondary-fixed-dim: '#e3c290'
  on-secondary-fixed: '#281900'
  on-secondary-fixed-variant: '#59431c'
  tertiary-fixed: '#c9e6ff'
  tertiary-fixed-dim: '#8aceff'
  on-tertiary-fixed: '#001e2f'
  on-tertiary-fixed-variant: '#004b6f'
  background: '#1e100d'
  on-background: '#fadcd7'
  surface-variant: '#43302d'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
  headline-md-mobile:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  title-lg:
    fontFamily: Newsreader
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 40px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style
The design system for this product is built on a "Functional Editorial" aesthetic. It targets discerning diners who value AI-driven precision as much as the craft of gastronomy. The brand personality is professional, honest, and high-quality, avoiding the frantic energy of typical food apps in favor of a curated, authoritative experience.

The visual style combines **Minimalism** with a **Structural** approach. It rejects depth-based metaphors like drop shadows and gradients, instead utilizing tonal shifts and hairline borders to create hierarchy. The interface should feel like a high-end digital publication—deliberate, legible, and premium.

## Colors
This design system uses a deeply recessed dark palette to allow food photography and restaurant names to command attention. 

- **Primary (Tomato #E23D28):** Reserved for high-action items, ratings, and rank badges. It signifies heat and appetite but is used sparingly to maintain a premium feel.
- **Secondary (Gold #D4B483):** Strictly utilized for AI-generated insights and quotes to differentiate machine intelligence from standard restaurant metadata.
- **Neutrals:** The background is a "Near-Black" charcoal. Hierarchy is built through tiered surfaces rather than elevation.
- **Accents:** Borders are strictly 1px hairlines at 8% white opacity, providing subtle structural definition without visual clutter.

## Typography
The typography system is a dual-font strategy that balances editorial charm with technical precision.

1. **The Serif (Newsreader):** Used for restaurant names, editorial titles, and AI quotes. It provides a literary, authoritative voice that elevates the dining recommendations.
2. **The Grotesque (Geist):** Used for all UI elements, labels, data points (prices, distances), and functional body text. Its sharp, monospaced-influenced terminals reinforce the product's AI/technical underpinning.

**Usage Note:** AI-generated explanations should be set in Newsreader Italic to further distinguish the "voice" of the recommendation.

## Layout & Spacing
The layout follows a rigorous 8px grid system. It prioritizes "Dense but Breathable" compositions, where data is packed efficiently but separated by significant negative space between logical sections.

- **Grid:** Use a 12-column fluid grid for desktop and a 4-column grid for mobile.
- **Margins:** 16px for mobile, scaling to 64px on large desktops to maintain a centered, editorial column feel.
- **Sectioning:** Use large 40px vertical gaps (spacing.lg) to separate major content blocks like "Recommendations" from "Recent History."
- **Reflow:** On mobile, restaurant cards stack vertically; on desktop, they shift to a 3-column masonry or grid layout to allow for larger imagery.

## Elevation & Depth
This design system rejects the use of drop shadows and blurs. Depth is achieved entirely through **Tonal Layering**:

1. **Level 0 (Base):** #0E1114 - Used for the main application canvas.
2. **Level 1 (Container):** #161B20 - Used for secondary panels, search bars, and inset areas.
3. **Level 2 (Raised):** #1C232A - Used for interactive cards and list items.

All boundaries are defined by a 1px hairline border (`rgba(255, 255, 255, 0.08)`). Interactive elements do not lift on hover; instead, they change border color to a slightly higher opacity (16%) or shift the background color slightly lighter.

## Shapes
The shape language is controlled and sophisticated. 
- **Standard UI (Inputs, Small Chips):** 0.5rem (8px) corner radius.
- **Cards & Primary Containers:** 1rem to 1.5rem (16px–24px) corner radius.
- **Icons:** Use 24px bounding boxes with a 1.5pt stroke weight. Avoid rounded terminals in icons; prefer sharp or slightly softened miters to match the Geist typeface.

## Components
### Buttons
- **Primary:** Solid #E23D28 with #F4F1EA text. No shadow. 8px radius.
- **Secondary:** Transparent background with the 1px hairline border. 
- **AI Action:** Gold #D4B483 text with a ghost-style border.

### Restaurant Cards
- Surfaces set to #1C232A.
- Image aspect ratio 16:9 or 4:3 with a subtle 0.5px inner stroke to prevent "bleeding" into the dark background.
- Ranking badges (e.g., #1) should be #E23D28 circles, positioned top-left.

### AI Quote Blocks
- Stylized with the Gold #D4B483.
- Left-border accent (2px width) in Gold.
- Typography: Newsreader Italic.

### Input Fields
- Background: #161B20.
- Border: 1px hairline.
- Focus state: Border color shifts to #E23D28; no outer glow.

### Chips/Tags
- Small, uppercase Geist text.
- 4px radius. 
- Background: #1C232A or transparent with a border. Used for cuisine types and price indicators ($$$).