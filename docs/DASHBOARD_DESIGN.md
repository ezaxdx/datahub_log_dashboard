---
name: Executive Precision
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3fd'
  on-secondary-container: '#57657b'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#271901'
  on-tertiary-container: '#98805d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d5e3fd'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2f'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#fcdeb5'
  tertiary-fixed-dim: '#dec29a'
  on-tertiary-fixed: '#271901'
  on-tertiary-fixed-variant: '#574425'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-lg:
    fontFamily: Manrope
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
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
  container-max-width: 1440px
  sidebar-width: 260px
  gutter: 24px
  margin-page: 32px
  stack-gap: 16px
  section-gap: 48px
---

## Brand & Style
The design system is engineered for high-level business intelligence and operational oversight. It targets decision-makers who require rapid data synthesis without cognitive overload. The brand personality is authoritative yet secondary to the data itself—acting as a silent, reliable partner in the decision-making process.

The visual style is **Corporate / Modern** with a strong emphasis on **Minimalism**. It utilizes a "content-first" architecture where functional elements are distinguished by purposeful whitespace rather than decorative flourishes. The aesthetic evokes a sense of calm efficiency, using a restrained palette to ensure that critical alerts and data trends remain the focal point.

## Colors
The color strategy prioritizes legibility and functional signaling. The background architecture uses a tiered system of soft whites and cool grays to define different functional zones without creating harsh visual breaks.

- **Primary:** Deep Navy (#0F172A) is used for headers, primary navigation, and high-level typography to establish grounded authority.
- **Surface:** The main canvas is set in a neutral off-white, with sidebar and utility areas shifting to subtle light grays.
- **Semantic:** Success, warning, and danger colors are desaturated to integrate cleanly with the professional palette, ensuring alerts are noticeable but not jarring.

## Typography
This design system employs a dual-font strategy to balance character with utility. **Manrope** is utilized for headings and key data points to provide a refined, modern executive feel. **Inter** is used for all body copy and UI controls due to its exceptional readability at small scales and neutral, systematic appearance.

Hierarchy is established through weight and scale. Labels use an uppercase treatment with increased letter spacing to clearly differentiate metadata from primary content. Data visualizations should favor tabular figures (monospaced numbers) to ensure alignment in dashboards.

## Layout & Spacing
The layout follows a **Fluid Grid** model within a maximum container width of 1440px. A 12-column grid system is used for the main content area, allowing for flexible card layouts (spanning 3, 4, 6, or 12 columns).

Whitespace is treated as a first-class citizen. Large margins (32px) and generous section gaps (48px) prevent the dashboard from feeling cramped, even when displaying complex datasets. All internal element spacing follows an 8px base grid to maintain a disciplined and rhythmic vertical flow.

## Elevation & Depth
Depth is communicated through **Tonal Layers** and **Ambient Shadows**. Instead of heavy drop shadows, the design system uses "Low-Contrast Outlines" (1px borders in a slightly darker gray than the background) paired with extremely soft, diffused shadows (10-15% opacity) to lift cards off the background.

- **Level 0 (Background):** Solid off-white (#F8FAFC).
- **Level 1 (Cards/Sidebar):** Pure white surface with a 1px border (#E2E8F0) and a subtle 4px blur shadow.
- **Level 2 (Dropdowns/Modals):** Pure white surface with a more pronounced 12px blur shadow to indicate interactivity and focus.

## Shapes
The shape language is consistently **Rounded**, using an 8px (0.5rem) base radius for cards and major containers. This softens the corporate aesthetic, making the environment feel more approachable and modern while maintaining a structural, grid-aligned integrity. Buttons and input fields mirror this radius, while smaller UI elements like tags or chips may use a fully pill-shaped radius for distinct visual categorization.

## Components
- **Cards:** The core container. Features a white background, 8px corner radius, and a subtle light-gray border. Padding inside cards should be a minimum of 24px.
- **Buttons:** Primary buttons use the Deep Navy background with white text. Secondary buttons use a transparent background with a 1px Navy border.
- **Inputs:** Fields are defined by a light gray border that thickens and darkens slightly on focus. Placeholder text is a muted gray to emphasize entered data.
- **Data Tables:** Row-based layouts with no vertical borders. Use a subtle hover state (#F1F5F9) to help users track information across wide rows.
- **Status Chips:** Small, rounded indicators using a low-saturation background of the semantic colors (e.g., light mint for success) with higher-contrast text of the same hue.
- **Navigation:** The sidebar uses a clean vertical list with icons. The active state is indicated by a subtle background fill and a primary-colored vertical bar on the left edge.