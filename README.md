# ApplyFlow Contact Agent

ApplyFlow Contact Agent is a local-first Streamlit app for job seekers who apply manually through company career portals, then want to find a likely recruiter or hiring contact email and generate warm, role-specific outreach.

The core question it helps answer is:

> I applied to this job. Who can I email, what is their likely email address, how confident are we, and what should I send them?

## Problem It Solves

When you apply to many jobs each day, the slow part after applying is often finding the right person to contact and writing a message that does not feel generic. This app keeps that workflow practical:

- Enter one job at a time after applying.
- Resolve or manually confirm the company domain.
- Generate recruiter and hiring-manager search queries.
- Generate likely professional email candidates.
- Check syntax, domain existence, and MX records locally.
- Rank candidates with honest confidence labels.
- Generate copy-ready cold emails, follow-ups, LinkedIn DMs, and a ChatGPT refinement prompt.
- Save each job/contact/email/outreach record in local SQLite.
- Export the tracker as CSV.

## What It Does

- Creates recruiter, talent acquisition, and hiring-manager search queries.
- Generates common email patterns such as `first.last@domain.com` and `firstinitiallast@domain.com`.
- Generates fallback aliases such as `careers@domain.com`, `recruiting@domain.com`, and `talent@domain.com`.
- Validates email candidates with free local checks.
- Scores email confidence without claiming exact inbox verification.
- Parses uploaded PDF resumes with PyMuPDF or accepts pasted resume text.
- Uses simple job-description keyword heuristics.
- Generates deterministic reel-style outreach in plain text, Markdown, and HTML.
- Uses clean clickable profile links in Markdown and HTML output.
- Saves records locally in `data/applyflow.db`.

## What It Does Not Do

- It does not guarantee exact recruiter emails.
- It does not verify exact inbox ownership.
- It does not scrape LinkedIn.
- It does not send emails automatically.
- It does not require OpenAI, Hunter, Apollo, Snov.io, Zapier, Gmail API, or paid scraping services.
- It does not invent personal connections, referrals, conversations, metrics, or company facts.

## Limitations

V1 is intentionally local and free. MX records only show that a domain can receive email. They do not prove that a specific inbox exists. Domain resolution is conservative and avoids aggressive guessing, especially when a job URL comes from an ATS such as Greenhouse, Lever, Workday, Ashby, iCIMS, SmartRecruiters, Jobvite, Taleo, Oracle Cloud, SuccessFactors, BambooHR, or Workable.

The resume-job match score is a heuristic, not a hiring prediction.

## Setup

### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## How To Use

### Find Contact

1. Enter company name, job title, and job URL or company careers URL.
2. Enter the company domain if you know it.
3. Click **Resolve Domain**.
4. Click **Generate Contact Search Queries** and manually search the generated queries.
5. Paste a contact name, title, LinkedIn URL, and context if available.
6. Click **Generate Email Candidates**.
7. Review confidence labels and select the best candidate.
8. Click **Save Contact Search** if you want to save the contact discovery step.

### Generate Email

1. Confirm company, role, contact, and selected email.
2. Paste the job description.
3. Upload the exact resume PDF used for that application or paste the resume text.
4. Add optional company notes or a truthful hook.
5. Click **Generate Outreach**.
6. Review the main email, short email, follow-up, LinkedIn DM, and ChatGPT prompt.
7. Click **Save Generated Outreach**.

### Tracker

The tracker shows saved applications with:

- Created date
- Company
- Job title
- Job URL
- Company domain
- Contact name/title
- Selected email
- Confidence label and score
- Status
- Follow-up date
- Priority
- Notes

You can filter records, update status/priority, delete a row by ID, and export all records to CSV.

### Settings

Settings store default profile details locally:

- Full name
- Email
- Phone
- LinkedIn URL
- GitHub URL
- Portfolio URL
- Default signature/style note
- Default follow-up days
- Default priority

Default links are prefilled for Ayush Meshram, and generated emails always use the latest saved Settings values.

### Help / Rules

The Help tab explains app limitations, confidence warnings, link formatting, and ethical usage.

## Email Confidence

The app scores candidates using local evidence only:

- Syntax validity
- Domain existence
- MX records
- Contact title relevance
- Department alignment
- Contact context
- Common email patterns
- LinkedIn URL presence
- Generic alias penalties

Labels:

- `High confidence`: Good candidate to email manually.
- `Medium confidence`: Use carefully; consider verifying manually.
- `Low confidence`: Do not use unless you verify elsewhere.
- `Do not use`: Skip this email.

The app never calls a guessed email verified.

## Link Formatting

Plain text emails may show raw URLs because plain text cannot hide hyperlinks.

Markdown output uses clean labels:

```markdown
[LinkedIn](https://www.linkedin.com/in/ayush-meshram025/) | [GitHub](https://github.com/Ayush141910) | [Portfolio](https://portfolio-two-orcin-btti7o0q2p.vercel.app/)
```

HTML output uses anchor tags:

```html
<a href="https://www.linkedin.com/in/ayush-meshram025/">LinkedIn</a> |
<a href="https://github.com/Ayush141910">GitHub</a> |
<a href="https://portfolio-two-orcin-btti7o0q2p.vercel.app/">Portfolio</a>
```

For Gmail, the HTML version may need to be pasted through a rich-text capable editor or copied from a rendered preview to preserve clickable labels.

## Ethical Usage

Use this app only for targeted professional job outreach. Do not spam. Do not send misleading emails. Do not fake referrals, conversations, or relationships. Respect opt-outs. Do not repeatedly contact people who do not respond.

## Future Roadmap

### v2

- Browser extension to capture company/job page text
- Better company domain resolver
- Google Sheets export/sync

### v3

- Optional Hunter/Apollo/Snov integration
- Email verification API integration
- Gmail draft creation, not auto-send

### v4

- Local LLM integration with Ollama
- Better contact ranking
- Better resume-job matching
- Follow-up reminders
- Better company research module
