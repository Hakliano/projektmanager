import sqlite3

DB_NAME = "projektmanager.db"

def create_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = create_connection()
    cursor = conn.cursor()

    # Tabulka projektů
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            contact_email TEXT,
            tech_email TEXT,
            website TEXT,
            nickname TEXT,
            password TEXT,
            hourly_rate REAL,
            external_expenses REAL,
            discount_percent REAL,
            discount_amount REAL,
            comment TEXT
        )
    ''')

    # Tabulka záznamů o odpracovaných hodinách
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS worklogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            work_date TEXT,
            hours REAL,
            note TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Databáze a tabulky 'projects' a 'worklogs' byly úspěšně vytvořeny (nebo již existují).")
