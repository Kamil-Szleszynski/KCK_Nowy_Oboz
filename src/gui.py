# Import biblioteki tkinter do tworzenia interfejsu graficznego
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
# Import klasy odpowiedzialnej za operacje na bazie danych treningów
from DatabaseManager import DatabaseManager


# Główne okno aplikacji – dziedziczy po tk.Tk, więc jest korzeniem całego GUI
class DeadliftApp(tk.Tk):
    def __init__(self, on_start_training=None):
        """Inicjalizuje główne okno aplikacji i tworzy wszystkie ekrany (strony)."""
        super().__init__()

        # Callback wywoływany po zatwierdzeniu konfiguracji treningu (przekazywany z zewnątrz)
        self.on_start_training = on_start_training

        # Ustawienia okna: tytuł, rozmiar startowy i minimalny rozmiar
        self.title("Asystent Martwego Ciągu")
        self.geometry("900x600")
        self.minsize(800, 500)

        # Słownik przechowujący dane bieżącego treningu (domyślne wartości zerowe)
        self.training_data = {
            "sets": 0,
            "height": 0.0,
            "weight": 0.0,
            "reps": 0
        }

        # Kontener na wszystkie ekrany – wypełnia całe okno i rozciąga się przy zmianie rozmiaru
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Słownik przechowujący referencje do wszystkich ekranów (ramek) aplikacji
        self.frames = {}

        # Tworzenie trzech ekranów: menu główne, konfiguracja treningu i historia
        for F in (MainMenu, TrainingSetup, TrainingHistory):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            # Wszystkie ekrany układane w tym samym miejscu (nakładają się na siebie)
            frame.grid(row=0, column=0, sticky="nsew")

        # Na starcie pokazujemy ekran menu głównego
        self.show_frame("MainMenu")

    def show_frame(self, page_name):
        """Przełącza widoczny ekran na wskazaną stronę."""
        frame = self.frames[page_name]

        # Przed pokazaniem historii odświeżamy listę treningów z bazy danych
        if page_name == "TrainingHistory":
            frame.refresh_list()

        # Podnosi wybraną ramkę na wierzch – użytkownik widzi ten ekran
        frame.tkraise()


# Ekran menu głównego z przyciskami nawigacji
class MainMenu(tk.Frame):
    def __init__(self, parent, controller):
        """Buduje interfejs menu głównego z tytułem i dwoma przyciskami."""
        super().__init__(parent)
        self.controller = controller

        # Nagłówek aplikacji
        label = tk.Label(self, text="Asystent Martwego Ciągu", font=("Helvetica", 24, "bold"))
        label.pack(pady=60)

        # Przycisk przechodzący do ekranu konfiguracji treningu
        btn_start = tk.Button(self, text="Rozpocznij trening", font=("Helvetica", 14), width=20, height=2,
                              command=lambda: controller.show_frame("TrainingSetup"))
        btn_start.pack(pady=10)

        # Przycisk przechodzący do ekranu historii treningów
        btn_history = tk.Button(self, text="Historia treningów", font=("Helvetica", 14), width=20, height=2,
                                command=lambda: controller.show_frame("TrainingHistory"))
        btn_history.pack(pady=10)


# Ekran formularza do wprowadzenia parametrów treningu
class TrainingSetup(tk.Frame):
    def __init__(self, parent, controller):
        """Tworzy formularz z polami: serie, wzrost, waga, powtórzenia oraz przyciski akcji."""
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Konfiguracja Treningu", font=("Helvetica", 20, "bold"))
        label.pack(pady=30)

        # Ramka zawierająca pola formularza ułożone w siatce (grid)
        form_frame = tk.Frame(self)
        form_frame.pack(pady=10)

        # Pole: liczba serii do wykonania
        tk.Label(form_frame, text="Ilość serii:", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=10,
                                                                               sticky="e")
        self.entry_sets = tk.Entry(form_frame, font=("Helvetica", 12))
        self.entry_sets.grid(row=0, column=1, padx=10, pady=10)

        # Pole: wzrost użytkownika w centymetrach
        tk.Label(form_frame, text="Wzrost (cm):", font=("Helvetica", 12)).grid(row=1, column=0, padx=10, pady=10,
                                                                               sticky="e")
        self.entry_height = tk.Entry(form_frame, font=("Helvetica", 12))
        self.entry_height.grid(row=1, column=1, padx=10, pady=10)

        # Pole: masa ciężaru w kilogramach
        tk.Label(form_frame, text="Waga (kg):", font=("Helvetica", 12)).grid(row=2, column=0, padx=10, pady=10,
                                                                             sticky="e")
        self.entry_weight = tk.Entry(form_frame, font=("Helvetica", 12))
        self.entry_weight.grid(row=2, column=1, padx=10, pady=10)

        # Pole: liczba powtórzeń w każdej serii
        tk.Label(form_frame, text="Powtórzenia:", font=("Helvetica", 12)).grid(row=3, column=0, padx=10, pady=10,
                                                                               sticky="e")
        self.entry_reps = tk.Entry(form_frame, font=("Helvetica", 12))
        self.entry_reps.grid(row=3, column=1, padx=10, pady=10)

        # Ramka z przyciskami nawigacji i zatwierdzenia
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=30)

        # Powrót do menu głównego bez uruchamiania treningu
        btn_back = tk.Button(btn_frame, text="Wróć", font=("Helvetica", 12), width=15,
                             command=lambda: controller.show_frame("MainMenu"))
        btn_back.grid(row=0, column=0, padx=10)

        # Zatwierdzenie danych i uruchomienie treningu
        btn_confirm = tk.Button(btn_frame, text="Zatwierdź i start", font=("Helvetica", 12), width=15, bg="green",
                                fg="white", command=self.save_and_start)
        btn_confirm.grid(row=0, column=1, padx=10)

    def save_and_start(self):
        """Odczytuje i waliduje dane z formularza, czyści pola i uruchamia trening."""
        try:
            # Konwersja tekstu z pól na odpowiednie typy liczbowe
            sets = int(self.entry_sets.get())
            height = float(self.entry_height.get())
            weight = float(self.entry_weight.get())
            reps = int(self.entry_reps.get())

            # Czyszczenie pól po poprawnym odczycie danych
            self.entry_sets.delete(0, tk.END)
            self.entry_height.delete(0, tk.END)
            self.entry_weight.delete(0, tk.END)
            self.entry_reps.delete(0, tk.END)

            # Wywołanie funkcji zewnętrznej (np. uruchomienie modułu treningu) z podanymi parametrami
            if self.controller.on_start_training:
                self.controller.on_start_training(sets, height, weight, reps)

        except ValueError:
            # Wyświetlenie komunikatu błędu, gdy użytkownik wpisał nieprawidłowe wartości
            messagebox.showerror("Błąd", "Wprowadź poprawne wartości liczbowe!")


# Ekran wyświetlający historię zapisanych treningów z bazy danych
class TrainingHistory(tk.Frame):
    def __init__(self, parent, controller):
        """Tworzy listę historii treningów i przycisk powrotu do menu."""
        super().__init__(parent)
        self.controller = controller
        # Instancja menedżera bazy danych do pobierania zapisanych serii
        self.db = DatabaseManager()

        label = tk.Label(self, text="Historia Treningów", font=("Helvetica", 20, "bold"))
        label.pack(pady=30)

        # Lista (listbox) wyświetlająca wpisy o treningach
        self.listbox = tk.Listbox(self, font=("Helvetica", 12), width=70, height=15)
        self.listbox.pack(pady=10)

        btn_back = tk.Button(self, text="Wróć do Menu", font=("Helvetica", 12), width=20,
                             command=lambda: controller.show_frame("MainMenu"))
        btn_back.pack(pady=20)

    def refresh_list(self):
        """Czyści listbox i wypełnia go aktualnymi danymi prosto z bazy."""
        # Usunięcie wszystkich poprzednich wpisów z listy
        self.listbox.delete(0, tk.END)
        # Pobranie wszystkich serii treningowych z bazy danych
        rows = self.db.fetch_all_series()

        # Gdy baza jest pusta, wyświetlamy komunikat informacyjny
        if not rows:
            self.listbox.insert(tk.END, "Brak zapisanych treningów w bazie.")
            return

        # Dla każdego rekordu tworzymy czytelny wpis i dodajemy go do listy
        for row in rows:
            wpis = f"ID Serii: {row[0]} | Data: {row[1]} | Zrobione Powtórzenia: {row[2]} | Średnia: {row[3]}%"
            self.listbox.insert(tk.END, wpis)
