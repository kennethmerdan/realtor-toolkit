import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = "realtor_toolkit.db"

class DataManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        c = conn.cursor()

        c.executescript("""
        CREATE TABLE IF NOT EXISTS realtors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            location TEXT,
            website TEXT,
            google_business_id TEXT,
            facebook_page_id TEXT,
            instagram_handle TEXT,
            tiktok_handle TEXT,
            ghl_contact_id TEXT,
            subscription_tier TEXT DEFAULT 'free',
            stripe_customer_id TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            realtor_id INTEGER,
            type TEXT,
            title TEXT,
            body TEXT,
            platform TEXT,
            status TEXT DEFAULT 'draft',
            scheduled_at TEXT,
            published_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (realtor_id) REFERENCES realtors(id)
        );

        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            realtor_id INTEGER,
            content_id INTEGER,
            platform TEXT,
            scheduled_at TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (realtor_id) REFERENCES realtors(id)
        );

        CREATE TABLE IF NOT EXISTS audit_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            realtor_id INTEGER,
            report_json TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (realtor_id) REFERENCES realtors(id)
        );

        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            realtor_id INTEGER,
            subject TEXT,
            body TEXT,
            status TEXT,
            sent_at TEXT,
            FOREIGN KEY (realtor_id) REFERENCES realtors(id)
        );

        CREATE TABLE IF NOT EXISTS sms_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            realtor_id INTEGER,
            message TEXT,
            status TEXT,
            sent_at TEXT,
            FOREIGN KEY (realtor_id) REFERENCES realtors(id)
        );

        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            realtor_id INTEGER,
            lead_name TEXT,
            lead_email TEXT,
            lead_phone TEXT,
            property_address TEXT,
            loan_type TEXT,
            loan_amount REAL DEFAULT 0,
            commission REAL DEFAULT 0,
            status TEXT DEFAULT 'new',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (realtor_id) REFERENCES realtors(id)
        );

        CREATE TABLE IF NOT EXISTS onboarding_checklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            realtor_id INTEGER,
            step TEXT,
            description TEXT,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (realtor_id) REFERENCES realtors(id)
        );

        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER,
            event_type TEXT,
            platform TEXT,
            value INTEGER DEFAULT 0,
            recorded_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (content_id) REFERENCES content(id)
        );

        CREATE TABLE IF NOT EXISTS video_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            realtor_id INTEGER,
            title TEXT,
            file_path TEXT,
            platform TEXT,
            status TEXT DEFAULT 'pending',
            upload_url TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (realtor_id) REFERENCES realtors(id)
        );
        """)
        conn.commit()
        conn.close()

    # ── Realtors ──────────────────────────────────────────────────────────────
    def add_realtor(self, name, email=None, phone=None, location=None, **kwargs):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT INTO realtors (name, email, phone, location, website,
                google_business_id, facebook_page_id, instagram_handle, tiktok_handle)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, email, phone, location,
            kwargs.get('website'), kwargs.get('google_business_id'),
            kwargs.get('facebook_page_id'), kwargs.get('instagram_handle'),
            kwargs.get('tiktok_handle')
        ))
        rid = c.lastrowid
        conn.commit()
        conn.close()
        return rid

    def get_all_realtors(self):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM realtors ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_realtor(self, realtor_id):
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM realtors WHERE id = ?", (realtor_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def update_realtor(self, realtor_id, **kwargs):
        if not kwargs:
            return
        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [realtor_id]
        conn = self._get_conn()
        conn.execute(f"UPDATE realtors SET {fields}, updated_at = datetime('now') WHERE id = ?", values)
        conn.commit()
        conn.close()

    def delete_realtor(self, realtor_id):
        conn = self._get_conn()
        conn.execute("DELETE FROM realtors WHERE id = ?", (realtor_id,))
        conn.commit()
        conn.close()

    # ── Content ───────────────────────────────────────────────────────────────
    def save_content(self, realtor_id, type_, title, body, platform=None, status='draft'):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT INTO content (realtor_id, type, title, body, platform, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (realtor_id, type_, title, body, platform, status))
        cid = c.lastrowid
        conn.commit()
        conn.close()
        return cid

    def get_content(self, realtor_id=None, status=None, days=None):
        conn = self._get_conn()
        query = "SELECT c.*, r.name as realtor_name FROM content c JOIN realtors r ON c.realtor_id = r.id WHERE 1=1"
        params = []
        if realtor_id:
            query += " AND c.realtor_id = ?"
            params.append(realtor_id)
        if status:
            query += " AND c.status = ?"
            params.append(status)
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND c.created_at >= ?"
            params.append(cutoff)
        query += " ORDER BY c.created_at DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_content_status(self, content_id, status, published_at=None):
        conn = self._get_conn()
        conn.execute("UPDATE content SET status = ?, published_at = ? WHERE id = ?",
                     (status, published_at or datetime.now().isoformat(), content_id))
        conn.commit()
        conn.close()

    # ── Scheduled Posts ───────────────────────────────────────────────────────
    def schedule_post(self, realtor_id, content_id, platform, scheduled_at):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT INTO scheduled_posts (realtor_id, content_id, platform, scheduled_at)
            VALUES (?, ?, ?, ?)
        """, (realtor_id, content_id, platform, scheduled_at))
        pid = c.lastrowid
        conn.commit()
        conn.close()
        return pid

    def get_scheduled_posts(self, realtor_id=None, status='pending'):
        conn = self._get_conn()
        query = """
            SELECT sp.*, c.title, c.body, r.name as realtor_name
            FROM scheduled_posts sp
            JOIN content c ON sp.content_id = c.id
            JOIN realtors r ON sp.realtor_id = r.id
            WHERE sp.status = ?
        """
        params = [status]
        if realtor_id:
            query += " AND sp.realtor_id = ?"
            params.append(realtor_id)
        query += " ORDER BY sp.scheduled_at"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_scheduled_post_status(self, post_id, status):
        conn = self._get_conn()
        conn.execute("UPDATE scheduled_posts SET status = ? WHERE id = ?", (status, post_id))
        conn.commit()
        conn.close()

    # ── Email Logs ─────────────────────────────────────────────────────────────
    def log_email(self, realtor_id, subject, body, status):
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO email_logs (realtor_id, subject, body, status, sent_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (realtor_id, subject, body, status))
        conn.commit()
        conn.close()

    def get_email_logs(self, realtor_id=None, days=30):
        conn = self._get_conn()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        query = "SELECT * FROM email_logs WHERE sent_at >= ?"
        params = [cutoff]
        if realtor_id:
            query += " AND realtor_id = ?"
            params.append(realtor_id)
        rows = conn.execute(query + " ORDER BY sent_at DESC", params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Audit Reports ──────────────────────────────────────────────────────────
    def save_audit(self, realtor_id, report):
        conn = self._get_conn()
        conn.execute("INSERT INTO audit_reports (realtor_id, report_json) VALUES (?, ?)",
                     (realtor_id, json.dumps(report)))
        conn.commit()
        conn.close()

    def get_latest_audit(self, realtor_id):
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM audit_reports WHERE realtor_id = ? ORDER BY created_at DESC LIMIT 1",
            (realtor_id,)
        ).fetchone()
        conn.close()
        if row:
            d = dict(row)
            d['report'] = json.loads(d['report_json'])
            return d
        return None

    # ── Referrals ─────────────────────────────────────────────────────────────
    def add_referral(self, realtor_id, lead_name, lead_email=None, lead_phone=None,
                     loan_amount=0, loan_type='conventional', notes=None):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT INTO referrals (realtor_id, lead_name, lead_email, lead_phone,
                loan_amount, loan_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (realtor_id, lead_name, lead_email, lead_phone, loan_amount, loan_type, notes))
        rid = c.lastrowid
        conn.commit()
        conn.close()
        return rid

    def get_referrals(self, realtor_id=None, status=None, days=None):
        conn = self._get_conn()
        query = """
            SELECT r.*, re.name as realtor_name
            FROM referrals r JOIN realtors re ON r.realtor_id = re.id WHERE 1=1
        """
        params = []
        if realtor_id:
            query += " AND r.realtor_id = ?"
            params.append(realtor_id)
        if status:
            query += " AND r.status = ?"
            params.append(status)
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += " AND r.created_at >= ?"
            params.append(cutoff)
        rows = conn.execute(query + " ORDER BY r.created_at DESC", params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_referral_status(self, referral_id, status, **kwargs):
        conn = self._get_conn()
        fields = "status = ?, updated_at = datetime('now')"
        params = [status]
        for k, v in kwargs.items():
            fields += f", {k} = ?"
            params.append(v)
        params.append(referral_id)
        conn.execute(f"UPDATE referrals SET {fields} WHERE id = ?", params)
        conn.commit()
        conn.close()

    # ── Onboarding ────────────────────────────────────────────────────────────
    def create_onboarding_checklist(self, realtor_id):
        steps = [
            ("welcome_email", "Send welcome email"),
            ("portal_setup", "Set up realtor portal account"),
            ("audit_run", "Run initial online presence audit"),
            ("content_setup", "Generate first content batch"),
            ("sms_setup", "Configure SMS notifications"),
            ("ghl_sync", "Sync to Go High Level CRM"),
        ]
        conn = self._get_conn()
        # Clear existing
        conn.execute("DELETE FROM onboarding_checklist WHERE realtor_id = ?", (realtor_id,))
        for step, desc in steps:
            conn.execute("""
                INSERT INTO onboarding_checklist (realtor_id, step, description)
                VALUES (?, ?, ?)
            """, (realtor_id, step, desc))
        conn.commit()
        conn.close()

    def get_onboarding_status(self, realtor_id):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM onboarding_checklist WHERE realtor_id = ? ORDER BY id",
            (realtor_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def complete_onboarding_step(self, realtor_id, step):
        conn = self._get_conn()
        conn.execute("""
            UPDATE onboarding_checklist
            SET completed = 1, completed_at = datetime('now')
            WHERE realtor_id = ? AND step = ?
        """, (realtor_id, step))
        conn.commit()
        conn.close()

    def get_onboarding_completion(self, realtor_id):
        steps = self.get_onboarding_status(realtor_id)
        if not steps:
            return 0
        completed = sum(1 for s in steps if s['completed'])
        return (completed / len(steps)) * 100
