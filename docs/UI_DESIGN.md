# UI/UX Modernization & Design System Specifications

**Design Standard**: Modern Financial SaaS (Stripe / Mercury aesthetic)
**Theme Engine**: Material UI 7 + Custom Tokens (`frontend/src/theme/theme.js`)
**Chart Engine**: Zero-Dependency Interactive SVG Visualizations

---

## 1. Design System & Palette Tokens

The redesign eliminates generic college-project typography and primary blue buttons in favor of an institutional fintech palette:

| Token | Hex | Role |
| :--- | :--- | :--- |
| **Primary Navy** | `#0F172A` (Slate 900) | Primary actions, headings, typography |
| **AI Secondary** | `#6366F1` (Indigo 500) | AI badges, natural language prompts, extraction indicators |
| **Credit Emerald** | `#10B981` (Emerald 500) | Positive net balances ("you are owed"), successful payments |
| **Debt Rose** | `#EF4444` (Rose 500) | Negative balances ("you owe"), delete actions |
| **Warning Amber** | `#F59E0B` (Amber 500) | AI anomaly detection flags, review needed |
| **Canvas Slate** | `#F8FAFC` (Slate 50) | Main background, clean non-glare surface |
| **Card Surface** | `#FFFFFF` | Elevated cards, subtle border `#E2E8F0` |

---

## 2. Layout & Navigation Hierarchy

### Desktop (`>= 900px`)
- **Sticky 260px Sidebar**: Navigation links with active route indicators, quick balance summary, group shortcuts, and user profile pill with one-click logout.
- **Top Bar**: Clean header with quick-action triggers ("Scan Receipt", "Create Group").
- **Content Area**: Fluid responsive container with breadcrumb navigation.

### Mobile (`< 900px`)
- **Collapsible Drawer**: Slide-in navigation drawer triggered by menu hamburger button.
- **Touch-Friendly Controls**: Full-width action buttons and card lists.

---

## 3. Reusable UI Components

1. **`BalanceIndicator`**:
   - Explicit color coding: Green pill with `+₹X.XX` for creditors, Red pill with `-₹X.XX` for debtors, Gray pill for settled ($0.00$).
2. **`MetricCard`**:
   - Elevated card featuring icon badge, formatted large value, and secondary trend subtitle.
3. **`MonthlyBarChart` (SVG)**:
   - Zero-dependency scalable vector graphic displaying monthly spending trajectory with interactive hover tooltips.
4. **`CategoryDonutChart` (SVG)**:
   - Interactive SVG donut chart showing percentage share per category with synchronized legend.
5. **`StatusBadge`**:
   - Compact status pills for receipt processing (`PENDING`, `EXTRACTED`, `CONFIRMED`, `FAILED`).
6. **`EmptyState`**:
   - Contextual empty states with soft icons, descriptive text, and a primary CTA button.

---

## 4. Key Workflows

### A. Intelligent Receipt Verification Flow
1. User drags receipt image into scanner drop-zone.
2. Animated progress indicator updates as OpenCV and local Qwen process the image.
3. Extracted merchant, date, and line-item table render in editable text fields.
4. User can add/remove line items or edit quantities; subtotals update in real-time.
5. User confirms with one click, automatically posting the verified expense.

### B. Natural Language Split Flow
1. User enters natural phrasing in the AI prompt box.
2. Clicks **"Interpret & Fill"**.
3. Local LLM extracts payer, amount, split method, and member shares.
4. A preview card explains the reasoning and confidence score.
5. The form fields and member checkboxes auto-populate for final verification before submission.
