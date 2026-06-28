---
name: Cosmic Glass
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#cbc3d7'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#958ea0'
  outline-variant: '#494454'
  surface-tint: '#d0bcff'
  primary: '#d0bcff'
  on-primary: '#3c0091'
  primary-container: '#a078ff'
  on-primary-container: '#340080'
  inverse-primary: '#6d3bd7'
  secondary: '#4cd7f6'
  on-secondary: '#003640'
  secondary-container: '#03b5d3'
  on-secondary-container: '#00424e'
  tertiary: '#ffb2b7'
  on-tertiary: '#67001b'
  tertiary-container: '#ff516a'
  on-tertiary-container: '#5b0017'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e9ddff'
  primary-fixed-dim: '#d0bcff'
  on-primary-fixed: '#23005c'
  on-primary-fixed-variant: '#5516be'
  secondary-fixed: '#acedff'
  secondary-fixed-dim: '#4cd7f6'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#ffdadb'
  tertiary-fixed-dim: '#ffb2b7'
  on-tertiary-fixed: '#40000d'
  on-tertiary-fixed-variant: '#92002a'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Sora
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Sora
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Sora
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
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
  unit: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  sidebar-width: 260px
---

## Brand & Style
The design system is a "Cyber-Glass" aesthetic tailored for a high-performance AI desktop suite. It balances the depth of deep space with the technical precision of a futuristic laboratory. The brand personality is **Premium, Fast, and Intelligent**, aiming to evoke a sense of limitless possibility and effortless power.

The visual style is a hybrid of **Glassmorphism** and **Corporate Modernism**. It utilizes translucency and backdrop blurs to simulate physical glass panes floating in a dark, cosmic void. High-energy gradients (Electric Purple to Cyan) serve as the "digital soul" of the interface, highlighting active states and AI-driven insights with a subtle outer glow.

## Colors
The palette is rooted in an **Obsidian & Navy** foundation to reduce eye strain and provide maximum contrast for vibrant accents.

- **Primary:** Electric Purple (#8B5CF6), used for core branding and primary AI actions.
- **Secondary:** Cyan (#06B6D4), used for data visualization and success states.
- **Tertiary:** Hot Pink/Rose (#F43F5E), reserved for destructive actions or urgent notifications.
- **Neutral:** A range of deep slates and navies provide the "glass" substrate.

**Gradients & Blurs:**
Use the `action` gradient for primary buttons and progress indicators. Backgrounds should feature large, low-opacity "blobs" of primary and secondary colors (100px - 400px blur radius) to create the cosmic depth effect.

## Typography
Typography uses a dual-font strategy. **Sora** provides a high-tech, geometric feel for headings and branding, while **Inter** ensures maximum legibility for the density of AI-generated content and technical data.

Headlines should occasionally use a subtle text-shadow glow (`0 0 10px rgba(139, 92, 246, 0.3)`) when appearing over dark backgrounds to enhance the "Cyber" feel. Use `label-sm` for sidebar headers and non-interactive metadata.

## Layout & Spacing
The system uses a **Fluid Grid** model with a sidebar-centric navigation structure common in desktop workspaces.

- **Sidebar:** Fixed width of 260px, utilizing a full-height glass pane with a `backdrop-filter: blur(20px)`.
- **Main Canvas:** A 12-column fluid grid for content cards and tools. 
- **Gutters:** Standardized 24px spacing between cards to allow the background gradients to "breathe" through the gaps.
- **Vertical Rhythm:** Built on a 4px baseline unit. Most components use 12px or 16px internal padding.

## Elevation & Depth
Depth is conveyed through **Glassmorphism tiers** rather than traditional shadows.

1.  **Level 0 (Background):** Deep Navy (#0F172A) with blurred color blobs.
2.  **Level 1 (Main Surfaces):** Translucent Slate (rgba(30, 41, 59, 0.5)) with `backdrop-filter: blur(12px)` and a 1px solid border (rgba(255, 255, 255, 0.1)).
3.  **Level 2 (Hover/Active):** Increased opacity and a subtle "inner glow" using a 1px border with a gradient stroke.
4.  **Level 3 (Popovers/Modals):** High blur (40px) and a more pronounced drop shadow (`0 20px 50px rgba(0, 0, 0, 0.5)`) to pull the element forward.

## Shapes
This design system uses a **Rounded** shape language to feel approachable and modern. 

- Standard cards and buttons use `0.75rem` (12px).
- Input fields and smaller chips use `0.5rem` (8px).
- Decorative active-state indicators (like the sidebar selection bar) use fully rounded pill shapes.

## Components
- **Primary Buttons:** High-contrast `action` gradient backgrounds with white text. Apply a `box-shadow: 0 0 15px rgba(139, 92, 246, 0.4)` on hover.
- **Glass Cards:** Semi-transparent containers with a subtle 1px top-down light border to simulate a "rim light" effect.
- **Inputs:** Darker than the card background (rgba(0,0,0,0.2)) with a 1px border that glows when focused.
- **Sidebar Items:** Clear background by default. On active/hover, use a glass-morphic pill with a gradient accent bar on the left or right edge.
- **Glow Chips:** Used for status indicators (e.g., "Nvidia API"). These should feature a small pulsing dot and a background color that matches the status (Success = Cyan, Warning = Orange).
- **Scrollbars:** Ultra-thin (4px), dark slate tracks with primary purple thumbs, appearing only on hover.