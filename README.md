# Orthopedic Clinic Appointment & Token Prototype

A mobile-friendly Flask + SQLite prototype for Prof. Adeel Ahmed Siddiqui's clinic workflow.

## Features
- Three clinics: Darul Sehat (DS), Jauhar (JH), FB Area (FB)
- First-come, first-served daily token generation
- New patient / follow-up and orthopedic / physiotherapy selection
- Staff dashboard with Booked, Arrived, Waiting, Seen, Cancelled states
- Walk-in registration
- Close/reopen bookings per clinic/date
- Admin sees all clinics; branch receptionists see their own clinic
- Local SQLite database; no external service required for prototype

## Run
1. Install Python 3.10+.
2. `pip install -r requirements.txt`
3. `python app.py`
4. Open `http://127.0.0.1:5000`

The database (`clinic.db`) is created on first run.

## Prototype logins — CHANGE BEFORE REAL USE
- Admin: `admin` / `2468`
- Jauhar: `jauhar` / `1357`
- FB Area: `fbarea` / `3579`
- Darul Sehat: `darulsehat` / `4680`

## Important before real patient deployment
- Replace PIN-only authentication with secure accounts/2FA.
- Set a strong secret key using an environment variable.
- Use HTTPS and a production database with encrypted backups.
- Add audit logs, privacy/consent language, retention policy, and role-based access controls.
- Do not expose the development server to the internet.
- WhatsApp integration should call the same booking/token logic through authenticated API endpoints; do not let the AI invent token numbers.
