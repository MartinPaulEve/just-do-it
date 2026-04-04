## 1.4.0 (2026-04-04)

### Feat

- **tasks**: add Google Tasks import command and fix calendar UI

## 1.3.0 (2026-04-03)

### Feat

- **deploy**: add ECR build+push workflow and Dockerfile prod improvements
- **deploy**: add production docker-compose with Postgres and Valkey
- **deploy**: add WhiteNoise and update production settings for Pangolin

### Fix

- **deploy**: switch to ECR Public for unauthenticated pulls

## 1.2.0 (2026-04-03)

### Feat

- **ui**: add conditional field visibility for recurrence form
- **recurrence**: add edit and delete with scope for recurring tasks
- **display**: add repeat indicators, series info, and ensure_series_generated
- **recurrence**: add recurrence form and recurring task creation flow
- **commands**: add generate_recurring_tasks management command
- **recurrence**: add recurrence calculation and instance generation
- **models**: add RecurrenceSeries model and Task recurrence fields

## 1.1.0 (2026-04-03)

### Feat

- **all-tasks**: add all tasks view with list and status filters
- **calendar**: add calendar view with FullCalendar and JSON event feed
- **today**: add today view with tasks grouped by list
- **lists**: add task list create, edit, and delete views
- **reorder**: add panel and task drag-and-drop reorder endpoints
- **links**: add task link create, delete, and form views
- **attachments**: add file upload and delete for tasks
- **followup**: add follow-up task scheduling with date picker
- **subtasks**: add sub-task create, toggle, and form views
- **tasks**: add task CRUD views with HTMX partials
- **dashboard**: add dashboard view with task list panels
- **ui**: add base template, navigation, CSS, and JS foundation
- **templatetags**: add deadline_class and deadline_display filters
- **forms**: add TaskListForm, TaskForm, and TaskLinkForm
- **settings**: add media config, django-htmx, and template dirs
- **models**: add TaskList, Task, TaskAttachment, TaskLink models
- expose Django port directly for local dev debugging
- add tasks app scaffold with empty models and views
- add Docker Compose with Traefik, Postgres, and Valkey
- add Traefik configuration with HTTPS support
- add Dockerfile and container scripts
- add local and production settings overrides
- add split settings base configuration

### Fix

- **ci**: add contents write permission for version-release push
- **ci**: use SSH deploy key for version-release push
- **urls**: register debug toolbar URLs in local development

### Refactor

- switch to split settings under config.settings
