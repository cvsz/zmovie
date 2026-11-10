# zMovie Admin Dashboard Architecture

## 1. System Architecture
The zMovie Admin Dashboard is built as a single-page application embedded within FastAPI (`/admin`), leveraging modern vanilla CSS and JavaScript, communicating securely with FastAPI backend API v2 endpoints (`/api/v2/...`).

## 2. Component Structure
- **App Shell**: AdminLTE dark sidebar, top navbar, breadcrumbs, content wrapper, and footer.
- **Modules**:
  - Dashboard Overview (KPIs, Charts, Recent Activity)
  - Production Studio & Projects
  - Render Queue & Workers
  - Publishing & Approval Center
  - System Health & Audit
