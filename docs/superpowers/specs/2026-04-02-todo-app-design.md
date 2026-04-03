# Todo Application Design Spec

## Overview

A single-user task management application built with Django and HTMX. Tasks are organised into user-defined lists (Work, Medical, Home, etc.) displayed as a customisable masonry dashboard. The app provides four views: Dashboard, Today, Calendar, and All Tasks. HTMX polling every 10 seconds provides cross-device reactivity without WebSockets. No authentication — external access is handled by Pangolin.

## Data Model

### TaskList

Represents a category of tasks (e.g. Work, Medical, Home).

| Field | Type | Notes |
|-------|------|-------|
| `id` | BigAutoField | PK |
| `name` | CharField(100) | e.g. "Work", "Medical" |
| `colour` | CharField(7) | Hex colour, e.g. "#4f46e5" |
| `icon` | CharField(50) | Optional emoji or icon name |
| `position` | PositiveIntegerField | Ordering on the dashboard |
| `column` | PositiveSmallIntegerField | Which column (0 or 1) on desktop; ignored on mobile |
| `created_at` | DateTimeField | auto_now_add |
| `updated_at` | DateTimeField | auto_now |

### Task

An individual task item within a list.

| Field | Type | Notes |
|-------|------|-------|
| `id` | BigAutoField | PK |
| `title` | CharField(255) | |
| `description` | TextField | Optional, supports markdown |
| `task_list` | FK → TaskList | on_delete=CASCADE |
| `parent_task` | FK → self | Nullable. For sub-tasks. on_delete=CASCADE |
| `start_date` | DateField | Nullable. When the task becomes visible. Null = immediately visible |
| `deadline` | DateField | Nullable. When the task is due. Null = no deadline |
| `completed` | BooleanField | Default False |
| `completed_at` | DateTimeField | Nullable. Set when completed |
| `follow_up_from` | FK → self | Nullable. Links to the predecessor task. on_delete=SET_NULL |
| `position` | PositiveIntegerField | Ordering within its list (among siblings if sub-task) |
| `created_at` | DateTimeField | auto_now_add |
| `updated_at` | DateTimeField | auto_now |

Constraints:
- A sub-task (`parent_task` set) must belong to the same `task_list` as its parent.
- `follow_up_from` can reference a task in any list — follow-up chains can cross lists.

### TaskAttachment

File attached to a task.

| Field | Type | Notes |
|-------|------|-------|
| `id` | BigAutoField | PK |
| `task` | FK → Task | on_delete=CASCADE |
| `file` | FileField | upload_to="attachments/%Y/%m/" |
| `filename` | CharField(255) | Original filename for display |
| `uploaded_at` | DateTimeField | auto_now_add |

### TaskLink

URL link attached to a task.

| Field | Type | Notes |
|-------|------|-------|
| `id` | BigAutoField | PK |
| `task` | FK → Task | on_delete=CASCADE |
| `url` | URLField | |
| `label` | CharField(255) | Optional. Defaults to URL if blank |
| `position` | PositiveIntegerField | Ordering |

## Views & URL Structure

### Navigation

Top navigation bar on desktop with four tabs. On mobile (<768px), this becomes a bottom tab bar.

### Routes

| URL | View | Description |
|-----|------|-------------|
| `/` | Dashboard | Masonry grid of all task list panels with active tasks |
| `/today/` | Today | Flat list of tasks due today or overdue, grouped by list |
| `/calendar/` | Calendar | FullCalendar month/week toggle with tasks on deadline dates |
| `/all/` | All Tasks | Every task including future and completed, with filters |

### Dashboard View

- Masonry layout using CSS Grid with 2 columns on desktop, 1 on mobile.
- Each task list is a panel. Panels are draggable (SortableJS) to reorder and move between columns.
- Panel layout (column assignment + position) is persisted to the TaskList model.
- Each panel shows active tasks: `start_date <= today` (or null) AND `completed = False`.
- Each panel has a "+" button to add a task inline.
- Each panel's content has `hx-trigger="every 10s"` to poll for updates.

### Today View

- Tasks grouped by task list (colour-coded headers).
- Shows tasks where: (`start_date` is null or `start_date <= today`) AND `deadline <= today` AND `completed = False`. This naturally includes overdue tasks (deadline < today) and tasks due today.
- Same card components as dashboard. No drag-and-drop — focused execution view.
- Polls every 10 seconds.

### Calendar View

- FullCalendar 6.x with month and week view toggle.
- Tasks appear as coloured pills on their deadline date, colour-matched to their task list.
- Click a day to see a popover listing that day's tasks with an "Add task" button.
- Click a task to expand it inline.
- Overdue tasks appear on today with a red outline.
- Polls every 10 seconds for data refresh.

### All Tasks View

- Complete list of all tasks (including future-dated and completed).
- Filterable by: task list, status (active/completed), date range.
- Sorted by deadline (nulls last), then position.

## Task Card Design

### Collapsed Card (default)

Displayed in list panels and the Today view.

- Left border coloured to match the task list.
- Checkbox (click to complete), title, deadline badge, indicators for sub-task count, file count, follow-up chain.
- Deadline badge is colour-coded: red for overdue or due today, amber for due within 3 days, grey for further out or no deadline.
- Clicking anywhere except the checkbox expands the card inline.

### Expanded Card (click to open)

Expands in place below the collapsed card. Contains:

- Title (editable inline)
- Start date and deadline (editable, date pickers)
- Description (editable, text area)
- Sub-tasks section: list of sub-tasks with their own checkboxes, "+ Add sub-task" button
- Files section: list of attachments with download links, "+ Attach file" button (file upload)
- Links section: list of URLs with labels, "+ Add link" button
- Follow-up chain: if this task is a follow-up, shows a link to the predecessor. Chain is navigable.
- Action buttons: "Schedule follow-up" (opens date picker + editable title, creates new task with `follow_up_from` link), "Delete" (with confirmation)

## Task Interactions (HTMX)

All interactions are HTMX partial page updates — no full page reloads.

| Action | Mechanism |
|--------|-----------|
| Add task | "+" button reveals inline form, POST creates task, HTMX swaps panel content |
| Edit task | Click to expand, edit fields inline, changes save on blur/enter via PATCH |
| Complete task | Checkbox click, HTMX PATCH toggles `completed`, card swaps to completed state (faded + strikethrough) |
| Delete task | Button in expanded card, confirmation dialog, DELETE removes, HTMX swaps out |
| Reorder tasks | SortableJS drag within list, POST new position order |
| Reorder panels | SortableJS drag on dashboard, POST new column + position |
| Add sub-task | Button in expanded card, inline form, POST creates with `parent_task` set |
| Schedule follow-up | Button opens inline date picker + title field, POST creates new task with `follow_up_from` |
| Attach file | File input in expanded card, POST multipart upload |
| Add link | URL + label fields in expanded card, POST creates link |
| Cross-device sync | `hx-trigger="every 10s"` on each panel/view refreshes content |

## Responsive Behaviour

- **Desktop (>768px):** 2-column masonry grid, top navigation bar, full card detail.
- **Mobile (<768px):** Single column stack, bottom tab bar (Dashboard / Today / Calendar / All). Cards and panels stack vertically. Drag-and-drop for panel reorder uses long-press (SortableJS mobile support). Calendar defaults to week view on mobile.

## Technology Stack

| Layer | Choice |
|-------|--------|
| Backend | Django 5.2 (existing project) |
| Database | PostgreSQL 17 (existing) |
| Cache | Valkey (existing) |
| Templates | Django templates + HTMX 2.x |
| Drag & drop | SortableJS |
| Calendar | FullCalendar 6.x |
| CSS | Hand-written, CSS Grid, CSS custom properties for theming. No framework. |
| File storage | Local filesystem, `MEDIA_ROOT/attachments/` |
| Polling | HTMX `hx-trigger="every 10s"` |
| Icons | Lucide (SVG, no font dependency) |
| Deployment | Docker/Traefik (existing), Pangolin handles auth + SSL |

## File Storage

Attachments stored under `MEDIA_ROOT/attachments/YYYY/MM/` using Django's FileField. `MEDIA_URL` configured to serve files. File size limit enforced in the upload view (sensible default: 20MB per file).

## Design Aesthetic

Clean and minimal (Things 3 / Todoist style):
- Lots of whitespace
- Subtle colours — task list colours used for left borders and calendar pills, not heavy fills
- Light grey backgrounds (#f8f9fa), white cards
- Small, understated typography for metadata (dates, counts)
- Smooth transitions on card expand/collapse
- No visual clutter — information density through progressive disclosure (collapsed → expanded)
