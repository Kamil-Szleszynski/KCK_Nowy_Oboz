import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="Database.db"):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Tworzy dwie powiązane tabele: dla całych serii i dla pojedynczych powtórzeń"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        #  Tabela (Seria)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS series_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_reps INTEGER NOT NULL,
                average_score REAL NOT NULL
            )
        ''')

        # Tabela Pojedyncze powtórzenia wewnątrz serii
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reps_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER NOT NULL,
                rep_number INTEGER NOT NULL,
                score REAL NOT NULL,
                FOREIGN KEY (series_id) REFERENCES series_history(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()
        print("[BAZA DANYCH] Zainicjalizowano relacyjną bazę danych (Serie + Powtórzenia).")