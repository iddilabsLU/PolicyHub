# UI/UX Design Specifications

Design specifications for PolicyHub's user interface.

## Design Philosophy

| Principle | Description |
|-----------|-------------|
| Professional & Serious | Financial compliance tool, not playful |
| Clean & Uncluttered | Generous spacing, breathing room |
| Sophisticated Neutrality | Muted tones, no vibrant colours |
| Desktop-First | Optimized for 1920x1080 workstations |
| Light Mode Only | No dark theme (regulatory clarity focus) |

## Color Palette

### Primary Colors

| Name | Hex | Usage |
|------|-----|-------|
| Primary (Ink Blue) | `#2D3E50` | Headers, primary buttons, sidebar |
| Primary Hover | `#3D5166` | Button hover states |
| Primary Foreground | `#FFFFFF` | Text on primary elements |

### Secondary/Accent

| Name | Hex | Usage |
|------|-----|-------|
| Secondary (Warm Grey-Beige) | `#E6E2DA` | Secondary buttons, borders |
| Secondary Hover | `#DDD8CF` | Secondary button hover |
| Secondary Border | `#D1CCC3` | Border for secondary buttons |

### Backgrounds

| Name | Hex | Usage |
|------|-----|-------|
| Background | `#F9FAFB` | Main window background |
| Card/Panel | `#FFFFFF` | Cards, dialogs, elevated surfaces |
| Muted | `#F3F4F6` | Table row stripes, input backgrounds |
| Border | `#E5E7EB` | Borders, dividers |
| Input Border | `#D1D5DB` | Input field borders |

### Text Colors

| Name | Hex | Usage |
|------|-----|-------|
| Text Primary | `#1F2937` | Main body text, headings |
| Text Secondary | `#6B7280` | Labels, helper text, timestamps |
| Text Muted | `#9CA3AF` | Placeholder text, disabled text |

### Status Indicators

| Status | Color | Background | Usage |
|--------|-------|------------|-------|
| Danger | `#B91C1C` | `#FEE2E2` | Overdue, errors |
| Warning | `#B45309` | `#FEF3C7` | Due soon (< 30 days) |
| Caution | `#A16207` | `#FEF9C3` | Upcoming (< 90 days) |
| Success | `#15803D` | `#DCFCE7` | On track, success |

### Document Type Accents

| Type | Color | Usage |
|------|-------|-------|
| Policy | `#6366F1` | Dashboard statistics |
| Procedure | `#8B5CF6` | Dashboard statistics |
| Manual | `#EC4899` | Dashboard statistics |
| HR/Others | `#14B8A6` | Dashboard statistics |

## Typography

Font: **Segoe UI** (Windows system font)

| Element | Size | Weight |
|---------|------|--------|
| Window Title | 16px | Semibold |
| Section Heading | 14px | Semibold |
| Body Text | 13px | Regular |
| Small/Caption | 11px | Regular |
| Button Text | 13px | Medium |
| Table Header | 12px | Semibold |
| Table Cell | 12px | Regular |

## Spacing

| Element | Value |
|---------|-------|
| Window Padding | 20px |
| Section Spacing | 24px |
| Card Padding | 16px |
| Button Padding (X/Y) | 10px / 8px |
| Input Height | 36px |
| Button Height | 36px |
| Table Row Height | 32px |
| Sidebar Width | 200px |
| Corner Radius | 6px |
| Corner Radius (Large) | 8px |

## Component Styling

All styling is implemented in `app/theme.py`. Use the provided helper functions:

```python
from app.theme import (
    configure_button_style,    # Apply button styling
    configure_input_style,     # Apply input field styling
    configure_card_style,      # Apply card/panel styling
    configure_dropdown_style,  # Apply dropdown styling
    configure_label_style,     # Apply label styling
    configure_table_style,     # Apply table styling
)
```

### Button Styles

- **Primary:** Ink Blue background, white text
- **Secondary:** Warm Grey-Beige background with border
- **Danger:** Red background, white text

### Card Style

White background with subtle border, rounded corners (8px).

### Table Style

- Light grey header with bold text
- White body with light border grid
- Blue selection highlight
