# PolicyHub - Policy & Procedure Lifecycle Manager

## Product Requirements Document (PRD)
**Version:** 3.0  
**Last Updated:** January 2025  
**Target Users:** Luxembourg PSFs, Fund Administrators, Compliance & Operations Teams  
**License:** Open Source  
**Deployment:** Native Windows Desktop Application (.exe) with Shared Folder Multi-User Support

---

## 1. Problem Statement

### The Compliance Reality in Luxembourg PSFs

Every regulated entity must maintain a suite of internal policies and operational procedures. The CSSF expects these to be:
- **Current** — reviewed at least annually or after material changes
- **Version-controlled** — with clear audit trail of amendments
- **Linked** — policies should map to implementing procedures
- **Accessible** — staff must be able to find the relevant document

### How It Actually Works (The Pain)

| What CSSF Expects | What Actually Happens |
|-------------------|----------------------|
| Central document register | Excel file last updated 18 months ago |
| Review dates tracked | "I think Sarah owns that policy?" |
| Version history | v1_final_FINAL_v3_APPROVED.docx |
| Policy-procedure mapping | "It's somewhere on SharePoint" |
| Audit-ready evidence | Frantic scramble before CSSF visit |

### The Audit Scenario

> "Can you show me your document governance framework? When was your AML Policy last reviewed? Which procedures implement it? Who approved the current version?"

Most firms cannot answer this confidently without 30 minutes of searching.

---

## 2. Product Vision

**PolicyHub** is a native Windows desktop application that tracks the lifecycle of all policies and procedures in a regulated entity. It runs locally but connects to a shared network folder for team collaboration.

### Core Principles

| Principle | Implementation |
|-----------|----------------|
| **Data Sovereignty** | All data stays on your infrastructure (local + shared folder). No cloud. |
| **Native Desktop Experience** | Real Windows application, not browser-based. Fast startup, native dialogs. |
| **Single Source of Truth** | One register for both policies and procedures |
| **Audit-Ready** | Generate compliance reports in one click |
| **Multi-User** | Team access via shared folder with role-based permissions |
| **Document Storage** | Store actual policy documents alongside metadata |

### What PolicyHub Is

- ✅ A **register** that tracks what documents exist, who owns them, and when they're due for review
- ✅ A **document repository** where approved policies/procedures are stored centrally
- ✅ A **multi-user tool** with Admin, Editor, and Viewer roles
- ✅ An **audit trail** of all changes and reviews
- ✅ A **native Windows application** that feels professional and responsive

### What PolicyHub Is NOT

- ❌ A document editing or collaboration tool (editing happens in Word/PDF externally)
- ❌ A workflow/approval system (approvals happen outside the tool)
- ❌ A web application or cloud service

---

## 3. Deployment Architecture

### 3.1 Overview

PolicyHub uses a **shared folder architecture** where:
- The application (.exe) is installed locally on each user's machine
- All data (database, attachments, exports) lives on a shared network folder
- Users authenticate against credentials stored in the shared database

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SHARED NETWORK FOLDER                       │
│                      (e.g., \\server\PolicyHub\)                    │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │    data/    │  │attachments/ │  │  exports/   │                 │
│  │policyhub.db │  │   [files]   │  │  [reports]  │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
         ▲                  ▲                  ▲
         │                  │                  │
    ┌────┴────┐        ┌────┴────┐        ┌────┴────┐
    │ User A  │        │ User B  │        │ User C  │
    │ (Admin) │        │(Editor) │        │(Viewer) │
    │  Local  │        │  Local  │        │  Local  │
    │   .exe  │        │   .exe  │        │   .exe  │
    └─────────┘        └─────────┘        └─────────┘
```

### 3.2 Shared Folder Structure

```
\\server\PolicyHub\                    ← Root shared folder
├── data/
│   └── policyhub.db                   ← SQLite database
├── attachments/                       ← Document storage
│   ├── POL-AML-001/
│   │   ├── POL-AML-001_v3.2.pdf
│   │   └── POL-AML-001_v3.1.pdf
│   ├── PROC-KYC-001/
│   │   └── PROC-KYC-001_v2.0.docx
│   └── ...
└── exports/                           ← Generated reports
    └── [timestamped report files]
```

### 3.3 Local Installation Structure

```
C:\Users\[User]\AppData\Local\PolicyHub\
├── config.json                        ← Shared folder path, remembered username
└── logs/
    └── policyhub.log                  ← Local activity log
```

The .exe itself can be placed anywhere (Desktop, Program Files, etc.).

### 3.4 Windows Folder Permissions (IT Setup)

| Folder | Admin | Editor | Viewer |
|--------|-------|--------|--------|
| `\data\` | Read/Write | Read/Write | Read |
| `\attachments\` | Read/Write | Read/Write | Read |
| `\exports\` | Read/Write | Read/Write | Read/Write |

**Note:** Application-level permissions are enforced by PolicyHub. Windows folder permissions provide a secondary layer of protection.

---

## 4. User Roles & Permissions

### 4.1 Role Definitions

| Role | Description | Typical User |
|------|-------------|--------------|
| **Admin** | Full control including user management | Compliance Officer, IT Admin |
| **Editor** | Can add/edit documents and attachments | Risk Manager, Operations Lead |
| **Viewer** | Read-only access, can download/export | Staff, Auditors (temporary) |

### 4.2 Permission Matrix

| Action | Admin | Editor | Viewer |
|--------|:-----:|:------:|:------:|
| View document register | ✓ | ✓ | ✓ |
| View document details | ✓ | ✓ | ✓ |
| Download attachments | ✓ | ✓ | ✓ |
| Export register to Excel | ✓ | ✓ | ✓ |
| Generate PDF reports | ✓ | ✓ | ✓ |
| Add new documents | ✓ | ✓ | ✗ |
| Edit documents | ✓ | ✓ | ✗ |
| Upload attachments | ✓ | ✓ | ✗ |
| Delete attachments | ✓ | ✓ | ✗ |
| Mark as reviewed | ✓ | ✓ | ✗ |
| Manage document links | ✓ | ✓ | ✗ |
| Delete documents | ✓ | ✗ | ✗ |
| Manage users | ✓ | ✗ | ✗ |
| Change app settings | ✓ | ✗ | ✗ |
| Manage categories | ✓ | ✗ | ✗ |
| View full audit log | ✓ | ✗ | ✗ |

---

## 5. Setup & Onboarding Workflow

### 5.1 First Launch Detection

When PolicyHub starts, it checks for `config.json` in the local app data folder:
- **If not found:** Show Setup Wizard
- **If found but shared path invalid:** Show "Connect to Folder" screen
- **If found and valid:** Check if database exists
  - **No database:** Show Admin Creation screen (first-time setup)
  - **Database exists:** Show Login screen

### 5.2 Setup Wizard (First Launch)

```
┌─────────────────────────────────────────────────────────────────────┐
│  PolicyHub Setup                                            [—][×] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                         ┌─────────────────┐                         │
│                         │    PolicyHub    │                         │
│                         │      Setup      │                         │
│                         └─────────────────┘                         │
│                                                                     │
│     Welcome! Let's connect PolicyHub to your shared folder.         │
│                                                                     │
│     ─────────────────────────────────────────────────────────────   │
│                                                                     │
│     Shared Folder Path:                                             │
│     ┌─────────────────────────────────────────────────┐ ┌────────┐ │
│     │ \\server\PolicyHub                              │ │ Browse │ │
│     └─────────────────────────────────────────────────┘ └────────┘ │
│                                                                     │
│     This should be a network folder accessible to all users.        │
│     Ask your administrator if you don't know the path.              │
│                                                                     │
│     ─────────────────────────────────────────────────────────────   │
│                                                                     │
│                                              ┌─────────────────┐    │
│                                              │     Connect     │    │
│                                              └─────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Admin Account Creation (First Setup Only)

Shown when database doesn't exist (very first user = Admin):

```
┌─────────────────────────────────────────────────────────────────────┐
│  PolicyHub Setup                                            [—][×] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│     Create Administrator Account                                    │
│                                                                     │
│     You're the first user. Create an admin account to get started. │
│                                                                     │
│     ─────────────────────────────────────────────────────────────   │
│                                                                     │
│     Username:                                                       │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ admin                                                       │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                                                     │
│     Full Name:                                                      │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ John Smith                                                  │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                                                     │
│     Email (optional):                                               │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ j.smith@company.lu                                          │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                                                     │
│     Password:                                                       │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ ••••••••••••                                                │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                                                     │
│     Confirm Password:                                               │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ ••••••••••••                                                │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                                                     │
│     Minimum 8 characters                                            │
│                                                                     │
│     ─────────────────────────────────────────────────────────────   │
│                                                                     │
│                                              ┌─────────────────┐    │
│                                              │ Create & Login  │    │
│                                              └─────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.4 Login Screen

```
┌─────────────────────────────────────────────────────────────────────┐
│  PolicyHub                                                  [—][×] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                                                                     │
│                         ┌─────────────────┐                         │
│                         │    PolicyHub    │                         │
│                         │       ┌───┐     │                         │
│                         │       │ 📋│     │                         │
│                         │       └───┘     │                         │
│                         └─────────────────┘                         │
│                                                                     │
│                    Policy & Procedure Manager                       │
│                                                                     │
│                                                                     │
│                    Username:                                        │
│                    ┌───────────────────────────────┐                │
│                    │                               │                │
│                    └───────────────────────────────┘                │
│                                                                     │
│                    Password:                                        │
│                    ┌───────────────────────────────┐                │
│                    │                               │                │
│                    └───────────────────────────────┘                │
│                                                                     │
│                    ☐ Remember my username                           │
│                                                                     │
│                         ┌─────────────────┐                         │
│                         │      Login      │                         │
│                         └─────────────────┘                         │
│                                                                     │
│     ─────────────────────────────────────────────────────────────   │
│     Connected to: \\server\PolicyHub              [Change...]       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. UI/UX Design Philosophy

### 6.1 Design Principles

| Principle | Description |
|-----------|-------------|
| **Professional & Serious** | Financial compliance tool, not playful. No decorative elements. |
| **Clean & Uncluttered** | Whitespace-driven, breathing room between elements. |
| **Sophisticated Neutrality** | Muted tones, no vibrant or saturated colors. |
| **Desktop-First** | Designed for professional workstations (1920x1080 target). |
| **Light-Mode Only** | No dark theme. Regulatory clarity requires high contrast on white. |
| **Native Feel** | Uses native Windows file dialogs, standard window controls. |

### 6.2 Color Palette

#### Primary Colors (Professional & Trustworthy)

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Ink Blue** (Primary) | `#2D3E50` | 45, 62, 80 | Headers, primary buttons, sidebar, icons |
| **Ink Blue Hover** | `#3D5166` | 61, 81, 102 | Button hover states |
| **Primary Foreground** | `#FFFFFF` | 255, 255, 255 | Text on primary color |

#### Secondary/Accent (Warm Neutrals)

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Warm Grey-Beige** (Secondary) | `#E6E2DA` | 230, 226, 218 | Secondary buttons, borders, dividers |
| **Warm Grey-Beige Hover** | `#DDD8CF` | 221, 216, 207 | Secondary button hover |
| **Secondary Foreground** | `#2D3E50` | 45, 62, 80 | Text on secondary color |

#### Backgrounds (Clean & Light)

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Background** | `#F9FAFB` | 249, 250, 251 | Main window background |
| **Card** | `#FFFFFF` | 255, 255, 255 | Cards, panels, modals |
| **Muted** | `#F3F4F6` | 243, 244, 246 | Table row stripes, input backgrounds |
| **Border** | `#E5E7EB` | 229, 231, 235 | Borders, dividers |

#### Text Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Text Primary** | `#1F2937` | 31, 41, 55 | Main body text, headings |
| **Text Secondary** | `#6B7280` | 107, 114, 128 | Labels, helper text, timestamps |
| **Text Muted** | `#9CA3AF` | 156, 163, 175 | Placeholder text, disabled text |

#### Status Indicators (Muted Versions)

| Status | Hex | RGB | Usage |
|--------|-----|-----|-------|
| **Danger/Overdue** | `#B91C1C` | 185, 28, 28 | Overdue badges, error states |
| **Danger Background** | `#FEE2E2` | 254, 226, 226 | Overdue row highlight |
| **Warning** | `#B45309` | 180, 83, 9 | Due soon (< 30 days) |
| **Warning Background** | `#FEF3C7` | 254, 243, 199 | Warning row highlight |
| **Caution** | `#A16207` | 161, 98, 7 | Upcoming (< 90 days) |
| **Success** | `#15803D` | 21, 128, 61 | On track, success states |
| **Success Background** | `#DCFCE7` | 220, 252, 231 | Success row highlight |

### 6.3 Typography

CustomTkinter uses system fonts by default. We'll use:

| Element | Font Family | Weight | Size |
|---------|-------------|--------|------|
| **Window Title** | Segoe UI | Semibold | 16px |
| **Section Heading** | Segoe UI | Semibold | 14px |
| **Body Text** | Segoe UI | Regular | 13px |
| **Small/Caption** | Segoe UI | Regular | 11px |
| **Button Text** | Segoe UI | Medium | 13px |
| **Table Header** | Segoe UI | Semibold | 12px |
| **Table Cell** | Segoe UI | Regular | 12px |

### 6.4 Spacing & Layout

| Element | Value |
|---------|-------|
| **Window padding** | 20px |
| **Section spacing** | 24px |
| **Card padding** | 16px |
| **Button padding** | 10px horizontal, 8px vertical |
| **Input height** | 36px |
| **Button height** | 36px |
| **Table row height** | 32px |
| **Sidebar width** | 200px |
| **Minimum window size** | 1024 × 700 px |
| **Default window size** | 1280 × 800 px |

### 6.5 Component Specifications

#### Buttons

**Primary Button:**
- Background: `#2D3E50`
- Text: `#FFFFFF`
- Corner radius: 6px
- Hover: `#3D5166`

**Secondary Button:**
- Background: `#E6E2DA`
- Text: `#2D3E50`
- Border: 1px `#D1CCC3`
- Corner radius: 6px
- Hover: `#DDD8CF`

**Danger Button (Delete actions):**
- Background: `#B91C1C`
- Text: `#FFFFFF`
- Corner radius: 6px

#### Input Fields

- Background: `#FFFFFF`
- Border: 1px `#D1D5DB`
- Corner radius: 6px
- Focus border: `#2D3E50`
- Height: 36px
- Padding: 8px 12px

#### Cards/Panels

- Background: `#FFFFFF`
- Border: 1px `#E5E7EB`
- Corner radius: 8px
- Shadow: subtle (1px blur)

#### Tables (tksheet)

- Header background: `#F3F4F6`
- Header text: `#2D3E50`, semibold
- Row background (odd): `#FFFFFF`
- Row background (even): `#F9FAFB`
- Row hover: `#F3F4F6`
- Selected row: `#E6E2DA`
- Border: 1px `#E5E7EB`

---

## 7. Document Taxonomy

### 7.1 Document Types

| Type | Code | Description | Examples |
|------|------|-------------|----------|
| **Policy** | `POLICY` | Board-level document stating principles | AML/CFT Policy, Data Protection Policy |
| **Procedure** | `PROCEDURE` | Operational document explaining how to execute a process | KYC Onboarding Procedure, NAV Calculation Procedure |
| **Manual** | `MANUAL` | Comprehensive guide covering multiple procedures | Accounting Manual, Transfer Agent Manual |
| **Register** | `REGISTER` | Standalone tracking document | Outsourcing Register, Conflict of Interest Register |

### 7.2 Document Categories (Default)

| Code | Name | Sort Order |
|------|------|------------|
| `AML` | Anti-Money Laundering & CFT | 1 |
| `GOV` | Corporate Governance | 2 |
| `OPS` | Operations | 3 |
| `ACC` | Accounting & Valuation | 4 |
| `IT` | Information Technology & Security | 5 |
| `HR` | Human Resources | 6 |
| `DP` | Data Protection / GDPR | 7 |
| `BCP` | Business Continuity | 8 |
| `RISK` | Risk Management | 9 |
| `REG` | Regulatory & Compliance | 10 |
| `OTHER` | Other | 99 |

Categories are configurable by Admin.

### 7.3 Document Statuses

| Status | Code | Description |
|--------|------|-------------|
| **Draft** | `DRAFT` | Document in preparation, not yet effective |
| **Active** | `ACTIVE` | Current, approved document |
| **Under Review** | `UNDER_REVIEW` | Being reviewed for updates |
| **Superseded** | `SUPERSEDED` | Replaced by a newer version |
| **Archived** | `ARCHIVED` | No longer applicable, kept for records |

### 7.4 Review Frequencies

| Frequency | Code | Days |
|-----------|------|------|
| **Annual** | `ANNUAL` | 365 |
| **Semi-Annual** | `SEMI_ANNUAL` | 182 |
| **Quarterly** | `QUARTERLY` | 91 |
| **Ad Hoc** | `AD_HOC` | Manual (no auto-calculation) |

### 7.5 Link Types

| Type | Code | Description |
|------|------|-------------|
| **Implements** | `IMPLEMENTS` | Procedure implements a Policy |
| **References** | `REFERENCES` | Document references another |
| **Supersedes** | `SUPERSEDES` | Document replaces an older one |

---

## 8. Data Model

### 8.1 Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    users     │       │  documents   │       │  categories  │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ user_id (PK) │       │ doc_id (PK)  │       │ code (PK)    │
│ username     │       │ doc_type     │       │ name         │
│ password_hash│       │ doc_ref      │       │ is_active    │
│ full_name    │       │ title        │       │ sort_order   │
│ email        │       │ category ────┼───────│              │
│ role         │       │ ...          │       └──────────────┘
│ is_active    │       │ created_by ──┼───┐
│ created_at   │       │ updated_by ──┼───┤
│ created_by   │       └──────┬───────┘   │
└──────────────┘              │           │
       ▲                      │           │
       │                      │           │
       └──────────────────────┴───────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ attachments  │ │document_links│ │document_     │
     ├──────────────┤ ├──────────────┤ │   history    │
     │attachment_id │ │ link_id (PK) │ ├──────────────┤
     │ doc_id (FK)  │ │parent_doc_id │ │ history_id   │
     │ filename     │ │child_doc_id  │ │ doc_id (FK)  │
     │ file_path    │ │ link_type    │ │ action       │
     │ version_label│ │ created_at   │ │ field_changed│
     │ is_current   │ │ created_by   │ │ old_value    │
     │ uploaded_at  │ └──────────────┘ │ new_value    │
     │ uploaded_by  │                   │ changed_by   │
     └──────────────┘                   │ changed_at   │
                                        │ notes        │
                                        └──────────────┘
```

### 8.2 Table: `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | TEXT | PRIMARY KEY | UUID |
| `username` | TEXT | UNIQUE, NOT NULL | Login username |
| `password_hash` | TEXT | NOT NULL | Bcrypt hashed password |
| `full_name` | TEXT | NOT NULL | Display name |
| `email` | TEXT | | Email address |
| `role` | TEXT | NOT NULL | ADMIN, EDITOR, VIEWER |
| `is_active` | INTEGER | NOT NULL, DEFAULT 1 | 1=active, 0=inactive |
| `created_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `created_by` | TEXT | | FK to users (null for first admin) |
| `last_login` | TEXT | | ISO 8601 timestamp |

**Index:** `idx_users_username` on `username`

### 8.3 Table: `documents`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `doc_id` | TEXT | PRIMARY KEY | UUID |
| `doc_type` | TEXT | NOT NULL | POLICY, PROCEDURE, MANUAL, REGISTER |
| `doc_ref` | TEXT | UNIQUE, NOT NULL | Reference code (e.g., POL-AML-001) |
| `title` | TEXT | NOT NULL | Document title |
| `description` | TEXT | | Brief description |
| `category` | TEXT | NOT NULL | FK to categories |
| `owner` | TEXT | NOT NULL | Responsible person/role |
| `approver` | TEXT | | Final approver |
| `status` | TEXT | NOT NULL | DRAFT, ACTIVE, UNDER_REVIEW, SUPERSEDED, ARCHIVED |
| `version` | TEXT | NOT NULL | Version number (e.g., "2.1") |
| `effective_date` | TEXT | NOT NULL | ISO 8601 date |
| `last_review_date` | TEXT | NOT NULL | ISO 8601 date |
| `next_review_date` | TEXT | NOT NULL | ISO 8601 date |
| `review_frequency` | TEXT | NOT NULL | ANNUAL, SEMI_ANNUAL, QUARTERLY, AD_HOC |
| `notes` | TEXT | | Free text notes |
| `created_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `created_by` | TEXT | NOT NULL | FK to users |
| `updated_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `updated_by` | TEXT | NOT NULL | FK to users |

**Indexes:**
- `idx_documents_doc_ref` on `doc_ref`
- `idx_documents_category` on `category`
- `idx_documents_status` on `status`
- `idx_documents_next_review` on `next_review_date`

### 8.4 Table: `attachments`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `attachment_id` | TEXT | PRIMARY KEY | UUID |
| `doc_id` | TEXT | NOT NULL, FK | FK to documents |
| `filename` | TEXT | NOT NULL | Original filename |
| `file_path` | TEXT | NOT NULL | Relative path in attachments folder |
| `file_size` | INTEGER | NOT NULL | Size in bytes |
| `mime_type` | TEXT | | MIME type |
| `version_label` | TEXT | NOT NULL | Version this represents |
| `is_current` | INTEGER | NOT NULL, DEFAULT 1 | 1=current, 0=previous |
| `uploaded_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `uploaded_by` | TEXT | NOT NULL | FK to users |

**Index:** `idx_attachments_doc_id` on `doc_id`

### 8.5 Table: `document_links`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `link_id` | TEXT | PRIMARY KEY | UUID |
| `parent_doc_id` | TEXT | NOT NULL, FK | FK to documents (Policy) |
| `child_doc_id` | TEXT | NOT NULL, FK | FK to documents (Procedure) |
| `link_type` | TEXT | NOT NULL | IMPLEMENTS, REFERENCES, SUPERSEDES |
| `created_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `created_by` | TEXT | NOT NULL | FK to users |

**Unique constraint:** `(parent_doc_id, child_doc_id, link_type)`

### 8.6 Table: `document_history`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `history_id` | TEXT | PRIMARY KEY | UUID |
| `doc_id` | TEXT | NOT NULL, FK | FK to documents |
| `action` | TEXT | NOT NULL | CREATED, UPDATED, STATUS_CHANGED, REVIEWED, ATTACHMENT_ADDED, ATTACHMENT_REMOVED |
| `field_changed` | TEXT | | Which field (null for CREATED) |
| `old_value` | TEXT | | Previous value |
| `new_value` | TEXT | | New value |
| `changed_by` | TEXT | NOT NULL | FK to users |
| `changed_at` | TEXT | NOT NULL | ISO 8601 timestamp |
| `notes` | TEXT | | Change notes |

**Index:** `idx_history_doc_id` on `doc_id`

### 8.7 Table: `categories`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `code` | TEXT | PRIMARY KEY | Category code |
| `name` | TEXT | NOT NULL | Display name |
| `is_active` | INTEGER | NOT NULL, DEFAULT 1 | 1=active, 0=hidden |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 99 | Display order |

### 8.8 Table: `settings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `key` | TEXT | PRIMARY KEY | Setting name |
| `value` | TEXT | | Setting value |
| `updated_at` | TEXT | | ISO 8601 timestamp |
| `updated_by` | TEXT | | FK to users |

**Default Settings:**
```
company_name = ""
warning_threshold_days = "30"
upcoming_threshold_days = "90"
date_format = "DD/MM/YYYY"
default_review_frequency = "ANNUAL"
```

---

## 9. Application Structure

### 9.1 Window Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  PolicyHub                                                  [—][□][×]│
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────────────────────────────────────────────────┐ │
│ │         │ │                                                     │ │
│ │         │ │                                                     │ │
│ │ SIDEBAR │ │                                                     │ │
│ │         │ │                    MAIN CONTENT                     │ │
│ │  200px  │ │                                                     │ │
│ │         │ │                                                     │ │
│ │         │ │                                                     │ │
│ │         │ │                                                     │ │
│ │         │ │                                                     │ │
│ └─────────┘ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Sidebar Navigation

```
┌─────────────────────┐
│                     │
│     PolicyHub       │
│                     │
├─────────────────────┤
│                     │
│  ▣ Dashboard        │  ← Currently selected
│                     │
│  ☐ Register         │
│                     │
│  ☐ Reports          │
│                     │
│  ☐ Settings         │  ← Admin only
│                     │
├─────────────────────┤
│                     │
│  John Smith         │
│  Admin              │
│                     │
│  [Logout]           │
│                     │
└─────────────────────┘
```

### 9.3 Dashboard View

```
┌─────────────────────────────────────────────────────────────────────┐
│  Dashboard                                          [+ Add Document] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐ │
│  │  REVIEW STATUS               │  │  DOCUMENTS BY TYPE           │ │
│  │  ────────────────────────────│  │  ────────────────────────────│ │
│  │                              │  │                              │ │
│  │  ● Overdue            3     │  │  Policies          24        │ │
│  │  ● Due < 30 days      5     │  │  Procedures        47        │ │
│  │  ● Due < 90 days     12     │  │  Manuals            8        │ │
│  │  ○ On Track          45     │  │  Registers          6        │ │
│  │                              │  │                              │ │
│  └──────────────────────────────┘  └──────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────────┐
│  │  ATTENTION REQUIRED                                             │
│  │  ──────────────────────────────────────────────────────────────│
│  │                                                                 │
│  │  REF            TITLE                     DUE DATE    OWNER     │
│  │  ─────────────────────────────────────────────────────────────  │
│  │  POL-AML-001    AML/CFT Policy            15/12/2024  J.Smith   │
│  │  PROC-KYC-003   Enhanced Due Diligence    20/12/2024  M.Jones   │
│  │  MAN-ACC-001    Accounting Manual         28/12/2024  P.Brown   │
│  │                                                                 │
│  └──────────────────────────────────────────────────────────────────┘
│                                                                     │
│  [View Full Register]                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

*Note: "Add Document" button hidden for Viewer role.*

### 9.4 Register View

```
┌─────────────────────────────────────────────────────────────────────┐
│  Document Register                                  [+ Add Document] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Type:     [All           ▼]   Category: [All           ▼]      ││
│  │ Status:   [All           ▼]   Review:   [All           ▼]      ││
│  │                                                                 ││
│  │ Search:   [                                    ]   [Clear]      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Showing 65 documents                     [Export Excel] [Export PDF]│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  ▲ REF         TITLE                 CATEGORY  OWNER   REVIEW  ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │    MAN-ACC-001 Accounting Manual     ACC       T.Davis ● 01/01 ││
│  │    POL-AML-001 AML/CFT Policy        AML       J.Smith ● 10/01 ││
│  │    POL-BCP-001 Business Continuity   BCP       M.Brown ○ 10/06 ││
│  │    POL-DP-001  Data Protection       DP        J.Doe   ○ 01/03 ││
│  │    PROC-KYC-001 Customer Onboarding  AML       S.Wilson ○ 01/02 ││
│  │    PROC-KYC-002 Ongoing Monitoring   AML       S.Wilson ○ 15/03 ││
│  │    PROC-NAV-001 NAV Calculation      ACC       T.Davis ○ 01/09 ││
│  │                                                                 ││
│  │                                                                 ││
│  │                                                                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Page: [< 1 2 3 ... 7 >]                        Showing 1-10 of 65  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Review Status Indicators:**
- `●` Red = Overdue
- `●` Amber = Due within 30 days
- `●` Yellow = Due within 90 days
- `○` Green = On track

**Double-click row** → Opens Document Detail View

### 9.5 Document Detail View

```
┌─────────────────────────────────────────────────────────────────────┐
│  [← Back]                                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  POL-AML-001                                                        │
│  Anti-Money Laundering and Counter-Terrorist Financing Policy       │
│                                                                     │
│  ┌──────────┐  Next Review: 10/01/2025              ○ On Track     │
│  │  ACTIVE  │                                                       │
│  └──────────┘                                                       │
│                                                                     │
│  ┌─────────────────────────────────┬───────────────────────────────┐│
│  │ DOCUMENT DETAILS                │ ATTACHMENTS                   ││
│  ├─────────────────────────────────┼───────────────────────────────┤│
│  │                                 │                               ││
│  │ Type:         Policy            │ ┌───────────────────────────┐ ││
│  │ Category:     AML               │ │ 📄 POL-AML-001_v3.2.pdf   │ ││
│  │ Owner:        John Smith        │ │    Current · 245 KB       │ ││
│  │ Approver:     Board             │ │    [Download]             │ ││
│  │ Version:      3.2               │ └───────────────────────────┘ ││
│  │ Effective:    15/01/2024        │                               ││
│  │ Last Review:  10/01/2024        │ ┌───────────────────────────┐ ││
│  │ Frequency:    Annual            │ │ 📄 POL-AML-001_v3.1.pdf   │ ││
│  │                                 │ │    Previous · 230 KB      │ ││
│  │                                 │ │    [Download]             │ ││
│  │                                 │ └───────────────────────────┘ ││
│  │                                 │                               ││
│  │                                 │ [+ Upload New Version]        ││
│  └─────────────────────────────────┴───────────────────────────────┘│
│                                                                     │
│  IMPLEMENTING PROCEDURES                              [Manage Links] │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ PROC-KYC-001  │ Customer Onboarding Procedure      │ ACTIVE     ││
│  │ PROC-KYC-002  │ Ongoing Monitoring Procedure       │ ACTIVE     ││
│  │ PROC-SAR-001  │ Suspicious Activity Reporting      │ ACTIVE     ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  NOTES                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Updated to reflect CSSF Circular 24/XXX requirements.           ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  CHANGE HISTORY (Last 5)                                [View All]  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 10/01/2024  REVIEWED   j.smith  Annual review completed         ││
│  │ 10/01/2024  UPDATED    j.smith  version: 3.1 → 3.2              ││
│  │ 12/01/2023  REVIEWED   j.smith  Annual review completed         ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  [Edit]   [Mark as Reviewed]   [Delete]                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Role visibility:**
- All users: View details, Download attachments
- Editor/Admin: Edit, Mark as Reviewed, Upload, Manage Links
- Admin only: Delete

### 9.6 Add/Edit Document Dialog

Opens as a modal dialog window:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Add New Document                                           [×]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Document Type:                                                     │
│  ○ Policy   ○ Procedure   ○ Manual   ○ Register                    │
│                                                                     │
│  Reference Code:        [POL-                              ]        │
│  Title:                 [                                  ]        │
│  Description:           [                                  ]        │
│                         [                                  ]        │
│                                                                     │
│  Category:              [▼ Select...                       ]        │
│  Owner:                 [                                  ]        │
│  Approver:              [                                  ]        │
│                                                                     │
│  Status:                [▼ ACTIVE                          ]        │
│  Version:               [1.0        ]                               │
│                                                                     │
│  Effective Date:        [📅 15/01/2025    ]                         │
│  Last Review Date:      [📅 15/01/2025    ]                         │
│  Review Frequency:      [▼ Annual                          ]        │
│                         Next review: 15/01/2026                     │
│                                                                     │
│  Notes:                 [                                  ]        │
│                         [                                  ]        │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│                                   [Cancel]      [Save Document]     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.7 Upload Attachment Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│  Upload Attachment                                          [×]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Document: POL-AML-001 - Anti-Money Laundering Policy               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                 ││
│  │                      No file selected                           ││
│  │                                                                 ││
│  │                       [Browse...]                               ││
│  │                                                                 ││
│  │            Supported: PDF, DOC, DOCX, XLS, XLSX                 ││
│  │                     Maximum: 25 MB                              ││
│  │                                                                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Version Label:         [3.2        ]                               │
│                         (Should match document version)             │
│                                                                     │
│  ☑ Mark as current version                                          │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│                                   [Cancel]           [Upload]       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.8 Mark as Reviewed Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│  Mark as Reviewed                                           [×]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Document: POL-AML-001 - Anti-Money Laundering Policy               │
│                                                                     │
│  Current Version:     3.2                                           │
│  Last Review:         10/01/2024                                    │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│  Review Date:           [📅 15/01/2025    ]                         │
│                                                                     │
│  Version Change:                                                    │
│  ○ No change (review only)                                          │
│  ○ New version: [      ]                                            │
│                                                                     │
│  Review Notes:          [                                  ]        │
│                         [                                  ]        │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│                                   [Cancel]    [Confirm Review]      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.9 User Management View (Admin Only)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Settings > Users                                       [+ Add User] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ USERNAME     FULL NAME      EMAIL               ROLE    STATUS  ││
│  ├─────────────────────────────────────────────────────────────────┤│
│  │ admin        John Smith     j.smith@co.lu       Admin   Active  ││
│  │ m.jones      Mary Jones     m.jones@co.lu       Editor  Active  ││
│  │ p.brown      Peter Brown    p.brown@co.lu       Editor  Active  ││
│  │ viewer1      Audit User     audit@external.lu   Viewer  Active  ││
│  │ s.wilson     Sarah Wilson   s.wilson@co.lu      Viewer  Inactive││
│  │                                                                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Select a user to edit or deactivate.                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.10 Add/Edit User Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│  Add User                                                   [×]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Username:              [                                  ]        │
│  Full Name:             [                                  ]        │
│  Email:                 [                                  ]        │
│                                                                     │
│  Role:                  [▼ Select...                       ]        │
│                         • Admin - Full access + user management     │
│                         • Editor - Add/edit documents               │
│                         • Viewer - Read only                        │
│                                                                     │
│  Password:              [                                  ]        │
│  Confirm Password:      [                                  ]        │
│                         Minimum 8 characters                        │
│                                                                     │
│  ☑ Account is active                                                │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                     │
│                                   [Cancel]       [Create User]      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.11 Reports View

```
┌─────────────────────────────────────────────────────────────────────┐
│  Reports                                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SELECT REPORT                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                 ││
│  │  ○ Full Document Register                                       ││
│  │    Complete list of all policies and procedures                 ││
│  │                                                                 ││
│  │  ○ Overdue Reviews                                              ││
│  │    Documents past their review date                             ││
│  │                                                                 ││
│  │  ○ Upcoming Reviews                                             ││
│  │    Documents due for review soon                                ││
│  │                                                                 ││
│  │  ○ Policy-Procedure Mapping                                     ││
│  │    Shows which procedures implement each policy                 ││
│  │                                                                 ││
│  │  ○ Documents by Category                                        ││
│  │    Grouped by functional area                                   ││
│  │                                                                 ││
│  │  ○ Audit Trail (Admin only)                                     ││
│  │    All changes within a date range                              ││
│  │                                                                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  OPTIONS                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                 ││
│  │  Upcoming Reviews - Days:     [▼ 30                   ]         ││
│  │                                                                 ││
│  │  Audit Trail Date Range:                                        ││
│  │  From: [📅              ]    To: [📅              ]             ││
│  │                                                                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  OUTPUT FORMAT                                                      │
│  ○ PDF    ○ Excel                                                   │
│                                                                     │
│                                          [Generate Report]          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Technical Architecture

### 10.1 Technology Stack

| Component | Library/Tool | Version | Purpose |
|-----------|--------------|---------|---------|
| **Language** | Python | 3.11+ | Core application |
| **UI Framework** | CustomTkinter | 5.2+ | Modern themed Tkinter widgets |
| **Data Tables** | tksheet | 7.0+ | Spreadsheet-like table widget |
| **Date Picker** | tkcalendar | 1.6+ | Date selection widget |
| **Database** | sqlite3 | (builtin) | Data storage |
| **Password Hashing** | bcrypt | 4.0+ | Secure password storage |
| **PDF Generation** | ReportLab | 4.0+ | PDF report creation |
| **Excel Export** | openpyxl | 3.1+ | Excel file generation |
| **File Type Detection** | python-magic-bin | 0.4+ | MIME type detection (Windows) |
| **Packaging** | PyInstaller | 6.0+ | Create Windows .exe |

### 10.2 Project Structure

```
PolicyHub/
│
├── main.py                           # Application entry point
├── requirements.txt                  # Python dependencies
├── README.md                         # User documentation
├── build.spec                        # PyInstaller specification
│
├── app/
│   ├── __init__.py
│   ├── application.py                # Main application class
│   ├── constants.py                  # Application constants
│   └── theme.py                      # Color palette & styling
│
├── core/
│   ├── __init__.py
│   ├── config.py                     # Local config management
│   ├── session.py                    # User session management
│   ├── permissions.py                # Role-based permissions
│   └── database.py                   # Database connection manager
│
├── models/
│   ├── __init__.py
│   ├── user.py                       # User model
│   ├── document.py                   # Document model
│   ├── attachment.py                 # Attachment model
│   ├── link.py                       # Document link model
│   ├── history.py                    # History entry model
│   └── category.py                   # Category model
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py               # Authentication logic
│   ├── user_service.py               # User CRUD operations
│   ├── document_service.py           # Document CRUD operations
│   ├── attachment_service.py         # File upload/download
│   ├── link_service.py               # Document linking
│   ├── history_service.py            # Audit trail logging
│   ├── report_service.py             # Report generation
│   └── settings_service.py           # App settings
│
├── views/
│   ├── __init__.py
│   ├── base_view.py                  # Base view class
│   ├── setup_view.py                 # Initial setup wizard
│   ├── login_view.py                 # Login screen
│   ├── main_view.py                  # Main window with sidebar
│   ├── dashboard_view.py             # Dashboard
│   ├── register_view.py              # Document register
│   ├── document_detail_view.py       # Document details
│   ├── reports_view.py               # Reports
│   └── settings/
│       ├── __init__.py
│       ├── settings_view.py          # Settings container
│       ├── general_settings.py       # General settings
│       ├── users_view.py             # User management
│       └── categories_view.py        # Category management
│
├── dialogs/
│   ├── __init__.py
│   ├── base_dialog.py                # Base dialog class
│   ├── document_dialog.py            # Add/Edit document
│   ├── upload_dialog.py              # Upload attachment
│   ├── review_dialog.py              # Mark as reviewed
│   ├── link_dialog.py                # Manage links
│   ├── user_dialog.py                # Add/Edit user
│   └── confirm_dialog.py             # Confirmation dialogs
│
├── components/
│   ├── __init__.py
│   ├── sidebar.py                    # Sidebar navigation
│   ├── header.py                     # View headers
│   ├── status_badge.py               # Status indicator badges
│   ├── stat_card.py                  # Dashboard stat cards
│   ├── document_table.py             # Wrapped tksheet for docs
│   └── filter_bar.py                 # Filter controls
│
├── utils/
│   ├── __init__.py
│   ├── dates.py                      # Date formatting & calculations
│   ├── files.py                      # File path utilities
│   ├── validators.py                 # Input validation
│   └── threading_utils.py            # Background task helpers
│
└── assets/
    └── icons/
        └── app_icon.ico              # Application icon
```

### 10.3 Application Flow

```
┌─────────────┐
│   main.py   │
│   Entry     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Application.__init__()                        │
│  1. Load local config (or create default)                           │
│  2. Check if shared_folder_path is set                              │
└──────────────────────────────────────────────────────────────────────┘
       │
       ├─── No config ───▶ SetupView (browse for shared folder)
       │                          │
       │                          ▼
       │                   Save config, continue
       │                          │
       ▼                          │
┌─────────────────────────────────────────────────────────────────────┐
│  Check if database exists at shared_folder_path/data/policyhub.db   │
└──────────────────────────────────────────────────────────────────────┘
       │
       ├─── No database ───▶ Create DB schema
       │                     │
       │                     ▼
       │              AdminCreationView (first admin account)
       │                     │
       │                     ▼
       │              Save admin, continue to LoginView
       │                     │
       ▼                     │
┌─────────────────────────────────────────────────────────────────────┐
│                           LoginView                                  │
│  1. User enters credentials                                         │
│  2. Validate against database                                       │
│  3. Create session                                                  │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           MainView                                   │
│  ┌──────────────┐  ┌───────────────────────────────────────────────┐│
│  │   Sidebar    │  │              Content Frame                    ││
│  │              │  │                                               ││
│  │  Dashboard ──┼──┼──▶ DashboardView                              ││
│  │  Register  ──┼──┼──▶ RegisterView ──▶ DocumentDetailView        ││
│  │  Reports   ──┼──┼──▶ ReportsView                                ││
│  │  Settings  ──┼──┼──▶ SettingsView (Admin only)                  ││
│  │              │  │                                               ││
│  └──────────────┘  └───────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 10.4 Database Connection Management

SQLite over network shares requires careful handling:

```python
# core/database.py

import sqlite3
from pathlib import Path
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        - Uses timeout for busy database handling
        - Enables WAL mode for better concurrent access
        - Properly closes connection after use
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,  # Wait up to 30 seconds if locked
            isolation_level=None  # Autocommit mode
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
```

### 10.5 Session Management

```python
# core/session.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class UserSession:
    user_id: str
    username: str
    full_name: str
    role: str  # ADMIN, EDITOR, VIEWER
    
    def can_edit(self) -> bool:
        return self.role in ('ADMIN', 'EDITOR')
    
    def is_admin(self) -> bool:
        return self.role == 'ADMIN'

class SessionManager:
    _instance: Optional['SessionManager'] = None
    _session: Optional[UserSession] = None
    
    @classmethod
    def get_instance(cls) -> 'SessionManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def login(self, user: UserSession) -> None:
        self._session = user
    
    def logout(self) -> None:
        self._session = None
    
    @property
    def current_user(self) -> Optional[UserSession]:
        return self._session
    
    @property
    def is_authenticated(self) -> bool:
        return self._session is not None
```

### 10.6 Threading for Long Operations

File uploads, report generation, and exports should run in background threads:

```python
# utils/threading_utils.py

import threading
from typing import Callable, Any

def run_in_background(
    task: Callable,
    on_complete: Callable[[Any], None],
    on_error: Callable[[Exception], None]
) -> None:
    """
    Run a task in a background thread.
    Callbacks are scheduled on the main thread.
    """
    def worker():
        try:
            result = task()
            # Schedule callback on main thread
            # (implementation depends on how you handle this in CTk)
        except Exception as e:
            # Schedule error callback on main thread
            pass
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
```

---

## 11. Security Considerations

### 11.1 Password Storage

- Passwords hashed using bcrypt with automatic salt
- Never store or log plaintext passwords
- Minimum 8 characters enforced at UI level

```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())
```

### 11.2 Session Security

- Session stored in memory only (not persisted)
- "Remember username" stores username only, never password
- Logout clears all session state

### 11.3 Input Validation

- Validate all user inputs before database operations
- Sanitize file names when storing attachments
- Check file types by content, not just extension

### 11.4 Audit Trail Integrity

- History records cannot be deleted through the UI
- All changes logged with user ID and timestamp
- Admin can export full audit trail for review

---

## 12. Reporting

### 12.1 Available Reports

| Report | Description | Formats |
|--------|-------------|---------|
| **Full Document Register** | All documents with metadata | PDF, Excel |
| **Overdue Reviews** | Documents past review date | PDF |
| **Upcoming Reviews** | Due within X days | PDF |
| **Policy-Procedure Mapping** | Policies with linked procedures | PDF |
| **Documents by Category** | Grouped by functional area | PDF |
| **Audit Trail** | All changes in date range (Admin) | PDF, Excel |

### 12.2 PDF Report Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ABC FUND SERVICES S.A.                                             │
│                                                                     │
│  ═══════════════════════════════════════════════════════════════   │
│  DOCUMENT GOVERNANCE REPORT                                         │
│  Full Document Register                                             │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  Generated: 15/01/2025 14:32                                        │
│  Generated By: John Smith                                           │
│                                                                     │
│  ───────────────────────────────────────────────────────────────   │
│                                                                     │
│  [Table content]                                                    │
│                                                                     │
│  ───────────────────────────────────────────────────────────────   │
│  PolicyHub v1.0                                          Page 1/3   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 13. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Project structure setup
- [ ] Theme and constants configuration
- [ ] Local config management (config.json)
- [ ] Database schema and migrations
- [ ] Database connection manager with network share handling
- [ ] Session management
- [ ] Permission utilities

### Phase 2: Authentication (Week 2-3)
- [ ] SetupView (shared folder selection)
- [ ] AdminCreationView (first-run admin setup)
- [ ] LoginView with validation
- [ ] Password hashing with bcrypt
- [ ] "Remember username" functionality
- [ ] User service (CRUD operations)

### Phase 3: Main Application Shell (Week 3-4)
- [ ] MainView with sidebar navigation
- [ ] View switching mechanism
- [ ] Sidebar component with role-based menu items
- [ ] Base view class
- [ ] Logout functionality

### Phase 4: Document Management (Week 4-6)
- [ ] Document service (CRUD)
- [ ] Category service
- [ ] RegisterView with tksheet table
- [ ] Filter bar component
- [ ] Search functionality
- [ ] DocumentDetailView (read-only first)
- [ ] DocumentDialog (Add/Edit)
- [ ] History service (audit logging)

### Phase 5: Dashboard (Week 6-7)
- [ ] Review status calculation logic
- [ ] DashboardView with stat cards
- [ ] Attention Required list
- [ ] Status badge component
- [ ] Quick navigation to overdue items

### Phase 6: Attachments (Week 7-8)
- [ ] Attachment service
- [ ] File storage in shared folder
- [ ] UploadDialog with file browser
- [ ] Download functionality
- [ ] Version tracking
- [ ] File type validation

### Phase 7: Document Linking & Review (Week 8-9)
- [ ] Link service
- [ ] LinkDialog (manage relationships)
- [ ] Display linked documents in detail view
- [ ] ReviewDialog (mark as reviewed)
- [ ] Version update on review

### Phase 8: Reporting & Export (Week 9-10)
- [ ] ReportsView
- [ ] PDF generation with ReportLab
- [ ] Excel export with openpyxl
- [ ] Register export (from table)
- [ ] All report types implemented

### Phase 9: Settings & User Management (Week 10-11)
- [ ] SettingsView container
- [ ] GeneralSettings (company name, thresholds)
- [ ] UsersView (Admin only)
- [ ] UserDialog (Add/Edit users)
- [ ] CategoriesView (Admin only)

### Phase 10: Polish & Packaging (Week 11-12)
- [ ] Error handling and user feedback
- [ ] Loading indicators for long operations
- [ ] Edge case testing
- [ ] Network share reliability testing
- [ ] PyInstaller packaging
- [ ] Testing on clean Windows machine
- [ ] README and user guide

---

## 14. Acceptance Criteria

### Must Have (MVP)
- [ ] Admin can set up shared folder and create first account
- [ ] Users log in with username/password
- [ ] Role-based access (Admin/Editor/Viewer) enforced
- [ ] Add, edit, view documents with all metadata fields
- [ ] Visual indicators for overdue/due soon documents
- [ ] Upload and download document attachments
- [ ] Mark documents as reviewed (updates dates)
- [ ] Link policies to implementing procedures
- [ ] Export register to Excel
- [ ] Admin can add/edit/deactivate users
- [ ] Runs as standalone Windows .exe without Python installed

### Should Have
- [ ] Dashboard with summary statistics
- [ ] PDF report generation
- [ ] Multiple report types
- [ ] Full audit trail with export
- [ ] Category management
- [ ] Search across documents

### Nice to Have (Future)
- [ ] CSV import for bulk loading
- [ ] Database backup utility
- [ ] Password reset by admin
- [ ] Session timeout after inactivity

---

## 15. Packaging & Distribution

### 15.1 PyInstaller Command

```bash
pyinstaller --name PolicyHub \
            --onefile \
            --windowed \
            --icon=assets/icons/app_icon.ico \
            --add-data "assets;assets" \
            main.py
```

### 15.2 Build Specification (build.spec)

```python
# build.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=['bcrypt', 'tksheet', 'tkcalendar'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PolicyHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/icons/app_icon.ico',
)
```

### 15.3 Expected .exe Size

- Estimated: 25-40 MB
- Includes: Python runtime, all libraries, assets

### 15.4 Testing Checklist

Before release, test on a clean Windows machine (no Python installed):

- [ ] .exe launches without errors
- [ ] Setup wizard works with UNC paths (\\server\share)
- [ ] Login/logout functions correctly
- [ ] All CRUD operations work
- [ ] File upload/download works over network
- [ ] Reports generate correctly
- [ ] Multiple simultaneous users (test database locking)

---

## 16. Appendix

### A. Dependencies (requirements.txt)

```
customtkinter>=5.2.0
tksheet>=7.0.0
tkcalendar>=1.6.1
bcrypt>=4.0.0
reportlab>=4.0.0
openpyxl>=3.1.0
python-magic-bin>=0.4.14
pyinstaller>=6.0.0
```

### B. Sample Test Data

```sql
-- First admin (password: 'admin123')
INSERT INTO users (user_id, username, password_hash, full_name, role, is_active, created_at)
VALUES ('u-001', 'admin', '$2b$12$...', 'Admin User', 'ADMIN', 1, '2025-01-15T10:00:00');

-- Sample documents
INSERT INTO documents (doc_id, doc_type, doc_ref, title, category, owner, status, version,
    effective_date, last_review_date, next_review_date, review_frequency,
    created_at, created_by, updated_at, updated_by)
VALUES
('d-001', 'POLICY', 'POL-AML-001', 'Anti-Money Laundering Policy', 'AML', 'John Smith',
 'ACTIVE', '3.2', '2024-01-15', '2024-01-10', '2025-01-10', 'ANNUAL',
 '2024-01-10T09:00:00', 'u-001', '2024-01-10T09:00:00', 'u-001'),

('d-002', 'PROCEDURE', 'PROC-KYC-001', 'Customer Onboarding Procedure', 'AML', 'Sarah Wilson',
 'ACTIVE', '2.0', '2024-02-01', '2024-02-01', '2025-02-01', 'ANNUAL',
 '2024-02-01T09:00:00', 'u-001', '2024-02-01T09:00:00', 'u-001');

-- Link policy to procedure
INSERT INTO document_links (link_id, parent_doc_id, child_doc_id, link_type, created_at, created_by)
VALUES ('l-001', 'd-001', 'd-002', 'IMPLEMENTS', '2024-02-01T10:00:00', 'u-001');
```

### C. Glossary

| Term | Definition |
|------|------------|
| **CSSF** | Commission de Surveillance du Secteur Financier (Luxembourg regulator) |
| **PSF** | Professionnel du Secteur Financier (regulated financial professional) |
| **Policy** | High-level document approved by governance body stating principles |
| **Procedure** | Operational document detailing how to execute specific processes |
| **Manual** | Comprehensive guide covering multiple related procedures |
| **CustomTkinter** | Modern themed wrapper for Python's Tkinter GUI library |
| **tksheet** | Spreadsheet/table widget compatible with Tkinter |
| **WAL Mode** | SQLite Write-Ahead Logging for better concurrent access |

### D. Supported Attachment Types

| Extension | MIME Type | Max Size |
|-----------|-----------|----------|
| .pdf | application/pdf | 25 MB |
| .doc | application/msword | 25 MB |
| .docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document | 25 MB |
| .xls | application/vnd.ms-excel | 25 MB |
| .xlsx | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | 25 MB |
| .ppt | application/vnd.ms-powerpoint | 25 MB |
| .pptx | application/vnd.openxmlformats-officedocument.presentationml.presentation | 25 MB |
| .txt | text/plain | 25 MB |

---

## 17. Notes for Claude Code Implementation

### Key Implementation Guidance

1. **Start with `app/theme.py`** — Define all colors, fonts, and component configurations first. Reference these constants throughout.

2. **CustomTkinter patterns:**
   ```python
   import customtkinter as ctk
   
   ctk.set_appearance_mode("light")  # Light mode only
   ctk.set_default_color_theme("blue")  # Base theme, we override
   ```

3. **tksheet for tables** — It has excellent features but requires careful configuration. Set up a reusable wrapper in `components/document_table.py`.

4. **Frame-based navigation** — Create all view frames once, then show/hide them:
   ```python
   def show_view(self, view_name: str):
       for name, frame in self.views.items():
           if name == view_name:
               frame.pack(fill="both", expand=True)
           else:
               frame.pack_forget()
   ```

5. **Dialogs as Toplevel** — Use `ctk.CTkToplevel` for modal dialogs. Set `transient()` and `grab_set()` for proper modal behavior.

6. **Date handling** — Store all dates as ISO 8601 strings in SQLite. Parse/format only at the UI boundary.

7. **Network path handling** — Use `pathlib.Path` but be aware of UNC paths on Windows. Test with actual network shares.

8. **Error messages** — Use `CTkMessagebox` or create a custom toast/notification component for user feedback.

9. **Build iteratively** — Get login working end-to-end before building features. Verify .exe packaging early to catch issues.

10. **Test concurrent access** — Have two instances open pointing to the same shared folder. Verify no database corruption.

---

*End of PRD v3.0*
