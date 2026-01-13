## UI/UX Design

### Design Philosophy

| Principle | Description |
|-----------|-------------|
| Professional & Serious | Financial compliance tool, not playful |
| Clean & Uncluttered | Generous spacing, breathing room |
| Sophisticated Neutrality | Muted tones, no vibrant colours |
| Desktop-First | Optimised for professional workstations |
| Light Mode Only | No dark theme (regulatory clarity focus) |

### Colour Palette

#### Primary Colours

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Primary (Ink Blue) | `#2D3E50` | 45, 62, 80 | Headers, buttons, key actions, icons |
| Primary Foreground | `#FFFFFF` | 255, 255, 255 | Text on primary colour elements |

#### Secondary/Accent

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Secondary (Warm Grey-Beige) | `#E6E2DA` | 230, 226, 218 | Secondary actions, subtle highlights |

#### Backgrounds

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Background | `#F9FAFB` | 249, 250, 251 | Main application background |
| Card/Panel | `#FFFFFF` | 255, 255, 255 | Cards, dialogs, elevated surfaces |
| Muted | `#F3F4F6` | 243, 244, 246 | Table row stripes, input backgrounds |
| Border | `#E5E7EB` | 229, 231, 235 | Borders, dividers |

### Qt Stylesheet

```css
/* Main Window */
QMainWindow {
    background-color: #F9FAFB;
}

/* Primary Buttons */
QPushButton[primary="true"] {
    background-color: #2D3E50;
    color: #FFFFFF;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
}

QPushButton[primary="true"]:hover {
    background-color: #3D4E60;
}

/* Secondary Buttons */
QPushButton {
    background-color: #E6E2DA;
    color: #2D3E50;
    border: 1px solid #D1CCC3;
    padding: 8px 16px;
    border-radius: 6px;
}

/* Danger Buttons */
QPushButton[danger="true"] {
    background-color: #B91C1C;
    color: #FFFFFF;
    border: none;
}

/* Input Fields */
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    padding: 6px 10px;
    border-radius: 6px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #2D3E50;
}

/* Table */
QTableView {
    background-color: #FFFFFF;
    alternate-background-color: #F3F4F6;
    border: 1px solid #E5E7EB;
    gridline-color: #E5E7EB;
}

QTableView::item:selected {
    background-color: #2D3E50;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #2D3E50;
    color: #FFFFFF;
    padding: 8px;
    border: none;
    font-weight: bold;
}

/* Cards/Panels */
QFrame[card="true"] {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
}

/* Labels */
QLabel[heading="true"] {
    color: #2D3E50;
    font-size: 16px;
    font-weight: bold;
}

/* Progress Bars */
QProgressBar {
    background-color: #F3F4F6;
    border: none;
    border-radius: 4px;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #2D3E50;
    border-radius: 4px;
}
```

---
