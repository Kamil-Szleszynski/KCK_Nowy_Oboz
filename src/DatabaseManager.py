import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="Database.db"):
        self.db_name = db_name # Ustalenie nazwy pliku bazy danych
        self.init_database() # Automatyczne wywołanie tworzenia tabel

    def init_database(self):
        """Tworzy dwie powiązane tabele: dla całych serii i dla pojedynczych powtórzeń"""
        conn = sqlite3.connect(self.db_name) # Otwarcie połączenia z plikiem bazy danych
        cursor = conn.cursor() # Utworzenie obiektu kursora do wykonywania zapytań SQL

        #  Tabela seria (id, data-godzina, calkowita liczba wykonanych powtorzen, sredni wynik dla calej serii)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS series_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_reps INTEGER NOT NULL,
                average_score REAL NOT NULL
            )
        ''')

        # Tabela Pojedyncze powtórzenia wewnątrz serii (id, id serii, numer powtórzenia w danej serii, wynik procentowy danego powtorzenia)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reps_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER NOT NULL,
                rep_number INTEGER NOT NULL,
                score REAL NOT NULL,
                FOREIGN KEY (series_id) REFERENCES series_history(id) ON DELETE CASCADE
            )
        ''')
        # Zapisanie zmian w bazie danych i zamknięcie połączenia
        conn.commit()
        conn.close()
        print("[BAZA DANYCH] Zainicjalizowano relacyjną bazę danych (Serie + Powtórzenia).")

    def save_session(self, reps_scores_list):
        """Zapisuje całą sesję oraz każde powtórzenie z osobna do bazy"""
        total_reps = len(reps_scores_list)
        if total_reps == 0: # Ochrona przed zapisywaniem pustych sesji
            print("[BAZA DANYCH] Brak powtórzeń do zapisania.")
            return


        avg_score = round(sum(reps_scores_list) / total_reps, 2) # Obliczanie średniej serii
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            # Wstawiamy serię do tabeli głównej
            cursor.execute('''
                INSERT INTO series_history (timestamp, total_reps, average_score)
                VALUES (?, ?, ?)
            ''', (current_time, total_reps, avg_score))

            # Pobieramy ID właśnie stworzonej serii, żeby przypisać do niej powtórzenia
            series_id = cursor.lastrowid

            # W pętli wstawiamy każde powtórzenie z osobna
            for index, score in enumerate(reps_scores_list):
                rep_num = index + 1  # Indeksowanie od 1 dla czytelności w bazie danych
                cursor.execute('''
                    INSERT INTO reps_details (series_id, rep_number, score)
                    VALUES (?, ?, ?)
                ''', (series_id, rep_num, round(score, 2)))

            conn.commit()
            print(
                f"\n[BAZA DANYCH] Sukces! Zapisano Serię ID: {series_id} ({total_reps} powtórzeń, Średnia: {avg_score}%)")

        except Exception as e:
            # W razie jakiegokolwiek blędu cofamy całą transakcję.
            conn.rollback()
            print(f"[BAZA DANYCH] Błąd krytyczny podczas zapisu: {e}")
        finally:
            conn.close()

    def fetch_series_with_reps(self, series_id):
        """Pobiera szczegóły konkretnej serii wraz z wynikami wszystkich jej powtórzeń"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Pobieranie danych przefiltrowanych po ID serii i posortowanych chronologicznie według numeru powtórzenia
        cursor.execute('''
            SELECT rep_number, score 
            FROM reps_details 
            WHERE series_id = ? 
            ORDER BY rep_number ASC
        ''', (series_id,))

        reps = cursor.fetchall()# Zwraca listę krotek
        conn.close()
        return reps

    def fetch_all_series(self):
        """Pobiera listę wszystkich odbytych serii"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM series_history ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows