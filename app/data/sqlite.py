import sqlite3

from app.core.config import settings


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.sqlite_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_sqlite() -> None:
    if settings.db_backend != "sqlite":
        return

    conn = _conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              full_name TEXT NOT NULL,
              email TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              role TEXT NOT NULL,
              active INTEGER NOT NULL DEFAULT 1
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_id INTEGER NOT NULL,
              payment_type TEXT NOT NULL,
              amount INTEGER NOT NULL,
              currency TEXT NOT NULL,
              payment_mode TEXT NOT NULL,
              payment_date TEXT NOT NULL,
              payment_status TEXT NOT NULL,
              receipt_original_filename TEXT,
              receipt_stored_path TEXT,
              created_by_user_id INTEGER,
              created_at TEXT NOT NULL,
              FOREIGN KEY(student_id) REFERENCES students(id)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS statuses (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL UNIQUE,
              active INTEGER NOT NULL DEFAULT 1,
              sort_order INTEGER NOT NULL DEFAULT 0
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              full_name TEXT NOT NULL,
              phone TEXT NOT NULL,
              email TEXT NOT NULL,
              country TEXT NOT NULL,
              study_level TEXT NOT NULL,
              program_choice TEXT NOT NULL,
              university TEXT NOT NULL,
              status_id INTEGER,
              agent_name TEXT NOT NULL,
              total_amount INTEGER NOT NULL DEFAULT 0,
              currency TEXT NOT NULL DEFAULT 'FCFA',
              notes TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(status_id) REFERENCES statuses(id)
            );
            """
        )

        # lightweight migrations for existing dev.db
        cur = conn.execute("PRAGMA table_info(students);")
        cols = {row[1] for row in cur.fetchall()}
        if "total_amount" not in cols:
            conn.execute("ALTER TABLE students ADD COLUMN total_amount INTEGER NOT NULL DEFAULT 0")
        if "currency" not in cols:
            conn.execute("ALTER TABLE students ADD COLUMN currency TEXT NOT NULL DEFAULT 'FCFA'")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS student_status_history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_id INTEGER NOT NULL,
              from_status_id INTEGER,
              to_status_id INTEGER,
              changed_by_user_id INTEGER,
              changed_at TEXT NOT NULL,
              FOREIGN KEY(student_id) REFERENCES students(id)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS student_documents (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_id INTEGER NOT NULL,
              doc_type TEXT NOT NULL,
              original_filename TEXT NOT NULL,
              stored_filename TEXT NOT NULL,
              stored_path TEXT NOT NULL,
              size_bytes INTEGER NOT NULL,
              uploaded_by_user_id INTEGER,
              uploaded_at TEXT NOT NULL,
              FOREIGN KEY(student_id) REFERENCES students(id)
            );
            """
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_students_status ON students(status_id);"
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_student_documents_student ON student_documents(student_id);"
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(student_id);"
        )

        conn.commit()
    finally:
        conn.close()


def conn():
    return _conn()
