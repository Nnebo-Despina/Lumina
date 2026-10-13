## PROJECT DOCUMENTATION
# Lumina E-Library — Online Library Management System

> **Status: IN PROGRESS** · Last updated: 9 Oct 2026

# Introduction
Lumina E-Library is our Aptech eProject (Python-R, *Online Library Management System*). It replaces slow, paper-based record keeping with a website where:

- **Guests** can view book titles, categories, library timings and send an inquiry through *Contact Us*.
- **Registered members** (one-time registration) can search by title, category, author or publisher, read books online, watch video tutorials, download books where the library allows it, and change their password.
- **The administrator** (super user) manages categories, book types, books, videos, download permissions, reports and their own profile.
- **Extra features we chose to add (not in the original specification):** member blocking, a contact-inquiry inbox, and physical book lending (copies, issuing, returns, "My Loans"). These are built last so they cannot put the required features at risk.

Team of five: **Despina** (`accounts`, integration) · **Justina** (`catalogue`, downloads, reports) · **Munachi** (member experience, lending) · **Samuel** (categories, public pages, documentation) · **Sanctus** (inquiries, member admin, documentation).
Team member names: 
# Student1642290 - JUSTINA ATU IRUOMA
# Student1647251 - NNEBO DESPINA AFOMA OKONKWO
# Student1639236 - ONAH DEBEIWU CHRYSANCTUS
# Student1670081 - CYNTHIA MUNACHIMYI EZUGWU
# Student1627019 - SAMUEL CHIEMEIE OKONKWO

# Project Specifications
-- Frontend
- HTML5 / CSS3 with a very small amount of Vanilla JS
- reason: simple, fast pages that work even if JavaScript is switched off. The mobile menu, modals, FAQ and toggle switches are pure HTML/CSS; JavaScript only handles show/hide password, "passwords match", live list filters, delete confirmations and the print button
- colour scheme: aubergine purple (#3B2159), cream (#F3EAD6) and gold(#C89B3D)
- every file is commented section by section so the team can follow it

-- Backend
- Django Monolith
- reason: Django provides authentication, forms, the ORM and the admin site out of the box, and gives built-in protection against CSRF, XSS and SQL injection (most effective when using Django forms and the ORM)

-- Database
- **[TO CONFIRM]** — SQLite for development and/or MySQL (state the provider here if one is used)

-- Auth model
- Custom `User` model that logs in with **email** (no username), with a `role` (student / teacher / staff / other), a phone number and an `is_blocked` flag

# Major Steps
-- Create a virtual environment (keeps this project's packages separate from everything else)

-- step --
py -m venv .venv

-- Activate the virtual environment

-- step --
- powershell
.venv/Scripts/activate

- command prompt
.venv\Scripts\activate

- git bash
source .venv/Scripts/activate

-- Install requirements (Django, plus Pillow because we store book covers and thumbnails in `ImageField`s)

-- step --
py -m pip install django pillow

-- Create the Django project --

-- step --
project-name = lumina
django-admin startproject ${project-name} .

-- Create the Django applications --

-- step --
python manage.py startapp ${app-name}

-- register each app in `INSTALLED_APPS` in settings.py --
-- create urls in each app and include them in the project urls --

-- Required settings (set these BEFORE the first migration) --
- `AUTH_USER_MODEL = "accounts.User"`
- `TEMPLATES["DIRS"] = [BASE_DIR / "templates"]`
- `MEDIA_URL = "/media/"` and `MEDIA_ROOT = BASE_DIR / "media"`
- `STATIC_URL = "/static/"` 

-- Create and apply migrations --

-- step --
python manage.py check
python manage.py makemigrations accounts catalogue library inquiries loans
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

-- Team Git rules --
- each person works on their own branch and opens pull requests; nothing goes straight to `main`
- commit migration files; after pulling a teammate's work run `python manage.py migrate`
- models are frozen after the agreed date; changes go through Despina so migrations do not collide

# Core Applications
---
Application 1
---
- name: accounts
- owner: Despina
- features: registration, login, logout, forgot / reset password, change password, member profile, administrator login / profile, permission decorators
- description: our custom email-based `User` model and everything about signing in

---
Application 2
---
- name: catalogue
- owner: Justina (Newbie A for categories and book types)
- models: `Category`, `BookType`, `Book`, `Video`, `BookCopy`
- description: all books and videos, uploads (cover, PDF, video file), download permissions (per category and per book), search and filtering, reports and CSV export

---
Application 3
---
- name: library
- owner: Muna
- models: `ReadingProgress`, `DownloadLog`, `VideoView`
- description: the member experience: online reader with a saved page, member dashboard, download history and video activity

---
Application 4
---
- name: inquiries
- owner: Sanctus
- models: `Inquiry`
- description: the *Contact Us* form and the administrator's inbox for answering messages

---
Application 5
---
- name: loans (extra feature)
- owner: Despina
- models: `BookIssue` (uses `BookCopy` from `catalogue`)
- description: physical lending. The admin issues a copy to a member, sets a due date and marks it returned; members only see their own loans

# Data Model (summary)
| Model | App | Key relationships |
|---|---|---|
| User | accounts | custom user; email login; `role`, `is_blocked` |
| Category | catalogue | has `allow_download` (category-level download switch) |
| BookType | catalogue | e.g. Book / Video |
| Book | catalogue | FK → Category, FK → BookType, FK → User (`created_by`); `download_permission` = inherit / allow / deny |
| Video | catalogue | FK → Category |
| BookCopy | catalogue | FK → Book; unique `inventory_code`; status available / on_loan / maintenance / lost / retired |
| ReadingProgress | library | FK → User, FK → Book; unique per user + book; stores `last_page` |
| DownloadLog | library | FK → User, FK → Book |
| VideoView | library | FK → User, FK → Video; unique per user + video |
| BookIssue | loans | FK → User (borrower), FK → BookCopy, FK → User (`issued_by`); `due_date`, `returned_at`, `status` |
| Inquiry | inquiries | optional FK → User |

**Download rule:** a book can be downloaded when its own setting is *allow*; if it is *inherit* it follows its category's `allow_download`; *deny* always blocks. The user must be logged in and not blocked.

# Front-end ↔ Django template map
The static front end (32 pages) lives in `lumina-e-library/`. Each page will become a Django template that extends a shared base.

| Static page | Django template |
|---|---|
| index, about | `catalogue/index.html`, `catalogue/about.html` |
| books, book-detail, videos | `catalogue/books.html`, `book_detail.html`, `videos.html` |
| member-book-detail | `catalogue/member_book_detail.html` |
| account, read, my-loans | `library/account.html`, `library/read.html`, `loans/my_loans.html` |
| contact | `inquiries/contact.html` |
| login, register, forgot-password, reset-password, change-password, profile | `accounts/*.html` |
| admin-index, categories, book-types, books, book-form, videos, video-form, downloads, reports | admin dashboard / catalogue management templates |
| users, inquiries | admin member and inquiry templates |
| issues, issue-form | admin lending templates |

- Public pages extend `templates/base.html`; admin pages extend an admin base (sidebar, header, messages).
- Every admin view must check permissions on the server; hiding the link is not enough.
- **Caution:** Django's own admin also looks for `admin/base.html`. Do not name our folder `templates/admin/` while `django.contrib.admin` is installed, or use a different folder name such as `manage/`.

# Specification Coverage
| Requirement (from the eProject specification) | Front end | Back end |
|---|---|---|
| Guest: view titles, categories, library info and timings | [x] | [ ] |
| Guest: Contact Us inquiry | [x] | [ ] |
| Member: one-time registration and login | [x] | [ ] |
| Member: search by title / category / author / publisher | [x] | [ ] |
| Member: read online | [x] | [ ] |
| Member: watch videos by category | [x] | [ ] |
| Member: download books where permitted | [x] | [ ] |
| Member: change own password | [x] | [ ] |
| Admin: login, recover password, update profile, change password | [x] | [ ] |
| Admin: dashboard (books, users, categories) | [x] | [ ] |
| Admin: add / delete categories | [x] | [ ] |
| Admin: add / delete book types | [x] | [ ] |
| Admin: add / edit books | [x] | [ ] |
| Admin: add / edit videos | [x] | [ ] |
| Admin: download permission by category or book | [x] | [ ] |
| Admin: report of books under each category | [x] | [ ] |
| *Extra:* block / unblock members | [x] | [ ] |
| *Extra:* physical lending and My Loans | [x] | [ ] |

## Development Progress & Audit Log

### Phase 1: Front end (static templates)
- [x] Public site: home, about, browse / search books, book detail (guest and member), videos, contact
- [x] Authentication pages: login, register, forgot password, reset password, change password
- [x] Member pages: account dashboard, online reader, my loans, profile (standalone file)
- [x] Admin area: login, recovery, dashboard (`admin-index.html`), categories, book types, books and book form, videos and video form, download permissions, reports, members, inquiries, profile, book issues and issue form
- [x] Purple / gold / cream colour scheme, responsive layout, CSS-only mobile menu and modals
- [x] All 32 pages link-checked; filters, date check and modals tested in a browser

### Phase 2: Django setup and data layer
- [x] Django project and apps `accounts`, `catalogue`, `library` created
- [x] Custom `UserManager` written (email login)
- [x] `catalogue` models written: Category, BookType, Book, Video, BookCopy
- [x] `library` models written: DownloadLog, ReadingProgress, VideoView
- [x] `loans` models drafted: BookIssue
- [x] `admin.py` drafted for all apps
- [x] Fix model bugs found in review (see Challenges): `Video.video_file`, `Video.level` length, `ReadingProgress.__str__`
- [x] Create `inquiries` app and `Inquiry` model
- [x] Settings completed (`AUTH_USER_MODEL`, templates, static, media, database)
- [x] Migrations created and applied; superuser created

### Phase 3: Authentication (Despina)
- [ ] Register, login, logout
- [ ] Forgot password and reset password
- [ ] Change password and member profile
- [ ] Administrator login and permission decorators (`admin_required`, `member_required`)

### Phase 4: Templates integration
- [ ] `templates/base.html` for the public site and a shared admin base
- [ ] Convert static pages to Django templates with `{% extends %}`, `{% static %}` and `{% url %}`
- [ ] Django messages and form validation errors shown on every form

### Phase 5: Admin management (Justina, Sanctus, Samuel)
- [ ] Category and book-type CRUD
- [ ] Book and video add / edit with uploads
- [ ] Download permissions page and secure download view
- [ ] Dashboard live statistics
- [ ] Reports with CSV export
- [ ] Member list: filter, block, unblock, delete
- [ ] Inquiry inbox and replies

### Phase 6: Member experience (Munachi)
- [ ] Search and filter with pagination
- [ ] Book detail, online reader and saved reading position
- [ ] Member dashboard and video browsing

### Phase 7: Lending
- [ ] Admin: issue a book and mark returned
- [ ] Member: My Loans (own records only)
- [ ] Availability shown on book pages

### Phase 8: Testing, documentation and submission
- [ ] ER diagram and GUI standards document (Sanctus)
- [ ] Unit-testing checklist and final-submission checklist (Samuel)
- [ ] Database script / backup and administrator login details
- [ ] Final integration test: guest → register → login → search → read → download → logout; and the full admin flow
- [ ] Final ZIP submitted

**Status**: In Progress. The front end is complete. The back end is at the model and admin stage. Next:  build authentication (Phase 3) so the other developers can start their views.

---

# Challenges
1. **Model bugs found in code review (resolved):** `Video.video_file` is a `URLField` with `upload_to`, which Django does not allow and which must be a `FileField`. `Video.level` has `max_length=10` but `INTERMEDIATE` is 12 characters. `ReadingProgress.__str__` uses `last_chapter` and `user.username`, which do not exist.
2. **Template folder name clash (will be resolved):** `templates/admin/` can collide with Django's built-in admin templates.
3. **Database choice and hosting (will be resolved):** **[TO CONFIRM]**

---

# Status Report Submission
During the project tenure we submit **two status reports at equal intervals** (every 10th day).

Each report contains:
- Overall progress of the project development
- Tasks completed and current status
- Challenges, if any
- Supporting files: source code, database scripts, screenshots and other documents that prove the progress
- All files in **one folder**, zipped, and submitted through the *Query / Status* section

### Folder layout for each submission
```
StatusReport_1/            (StatusReport_2/ for the second one)
├── README.md       <- copy of the report text below
├── source-code/           <- project folder (no .venv, no __pycache__)
├── screenshots/           <- pages that work, admin screens, forms
└── documents/             <- ER diagram, GUI standards, checklists
```

### Status Report 1
- **Date:** 10th October, 2026
- **Overall progress:** the complete front end (32 pages: public site, authentication, member area, admin area, lending) is finished and tested. Django project structure and the data models for `catalogue`, `library` and `loans` are written; `admin.py` is drafted for every app.
- **Tasks completed:** Phase 1 in full; Phase 2 up to the written models and admin registration.
- **Current status:** finishing settings and running the first migrations; authentication is the next task.
- **Challenges:** see the list above.
- **Supporting files:** front-end folder, the models and `admin.py` files, screenshots of the main public and admin pages, and the `documents/` folder as it becomes available.

### Status Report 2 (will be filled in when due)
- **Date:**
- **Overall progress:**
- **Tasks completed:**
- **Current status:**
- **Challenges:**
- **Supporting files:**

### Before zipping each report
- [ ] Project runs with `python manage.py runserver` and the pages shown in the screenshots really work
- [ ] No `.venv`, `__pycache__`, `.env` or other secrets (database passwords) inside the ZIP
- [ ] Migration files and the database script are included
- [ ] Screenshots are clear and named (for example `login.png`, `admin-books.png`)
- [ ] The report text matches what is actually finished (tick boxes honestly)