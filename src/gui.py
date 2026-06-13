import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class DeadliftApp(tk.Tk):
    """Główna klasa aplikacji zarządzająca oknem i przełączaniem widoków."""

    # Dodaliśmy parametr on_start_training
    def __init__(self, on_start_training=None):
        super().__init__()

        self.on_start_training = on_start_training

        self.title("Asystent Martwego Ciągu")
        self.geometry("900x600")
        self.minsize(800, 500)

        self.training_data = {
            "sets": 0,
            "height": 0.0,
            "weight": 0.0,
            "reps": 0
        }

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (MainMenu, TrainingSetup, TrainingHistory):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainMenu")

    def show_frame(self, page_name):
        """Podnosi wskazany ekran na wierzch."""
        frame = self.frames[page_name]
        frame.tkraise()


class MainMenu(tk.Frame):
    """Ekran początkowy z wyborem rozpoczęcia treningu lub historii."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Asystent Martwego Ciągu", font=("Helvetica", 24, "bold"))
        label.pack(pady=60)

        btn_start = tk.Button(self, text="Rozpocznij trening", font=("Helvetica", 14), width=20, height=2,
                              command=lambda: controller.show_frame("TrainingSetup"))
        btn_start.pack(pady=10)

        btn_history = tk.Button(self, text="Historia treningów", font=("Helvetica", 14), width=20, height=2,
                                command=lambda: controller.show_frame("TrainingHistory"))
        btn_history.pack(pady=10)


class TrainingSetup(tk.Frame):
    """Ekran konfiguracji parametrów treningu i gabarytów użytkownika."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Konfiguracja Treningu", font=("Helvetica", 20, "bold"))
        label.pack(pady=30)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=10)

        # Zmieniłem etykietę na "Ilość serii:", skoro niżej dodałeś "Powtórzenia"
        tk.Label(form_frame, text="Ilość serii:", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=10,
                                                                               sticky="e")
        self.entry_sets = tk.Entry(form_frame, font=("Helvetica", 12))
        self.entry_sets.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="Wzrost (cm):", font=("Helvetica", 12)).grid(row=1, column=0, padx=10, pady=10,
                                                                               sticky="e")
        self.entry_height = tk.Entry(form_frame, font=("Helvetica", 12))
        self.entry_height.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="Waga (kg):", font=("Helvetica", 12)).grid(row=2, column=0, padx=10, pady=10,
                                                                             sticky="e")
        self.entry_weight = tk.Entry(form_frame, font=("Helvetica", 12))
        self.entry_weight.grid(row=2, column=1, padx=10, pady=10)

        # Poprawiony wiersz (row=3) i domknięte parametry
        tk.Label(form_frame, text="Powtórzenia:", font=("Helvetica", 12)).grid(row=3, column=0, padx=10, pady=10,
                                                                               sticky="e")
        self.entry_reps = tk.Entry(form_frame, font=("Helvetica", 12))
        self.entry_reps.grid(row=3, column=1, padx=10, pady=10)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=30)

        btn_back = tk.Button(btn_frame, text="Wróć", font=("Helvetica", 12), width=15,
                             command=lambda: controller.show_frame("MainMenu"))
        btn_back.grid(row=0, column=0, padx=10)

        btn_confirm = tk.Button(btn_frame, text="Zatwierdź i start", font=("Helvetica", 12), width=15, bg="green",
                                fg="white",
                                command=self.save_and_start)
        btn_confirm.grid(row=0, column=1, padx=10)

    def save_and_start(self):
        """Waliduje dane i wysyła je do kontrolera (main.py)"""
        try:
            sets = int(self.entry_sets.get())
            height = float(self.entry_height.get())
            weight = float(self.entry_weight.get())
            reps = int(self.entry_reps.get())  # Poprawiona literówka i nawiasy

            # Czyścimy pola
            self.entry_sets.delete(0, tk.END)
            self.entry_height.delete(0, tk.END)
            self.entry_weight.delete(0, tk.END)
            self.entry_reps.delete(0, tk.END)

            # Przekazujemy wszystkie 4 wartości do main.py!
            if self.controller.on_start_training:
                self.controller.on_start_training(sets, height, weight, reps)

        except ValueError:
            messagebox.showerror("Błąd", "Wprowadź poprawne wartości liczbowe!")


class TrainingHistory(tk.Frame):
    """Ekran wyświetlający historię treningów."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Historia Treningów", font=("Helvetica", 20, "bold"))
        label.pack(pady=30)

        listbox = tk.Listbox(self, font=("Helvetica", 12), width=60, height=15)
        listbox.insert(1, "12.10.2023 - 4 serie - Poprawność: 85%")
        listbox.insert(2, "14.10.2023 - 5 serii - Poprawność: 90%")
        listbox.pack(pady=10)

        btn_back = tk.Button(self, text="Wróć do Menu", font=("Helvetica", 12), width=20,
                             command=lambda: controller.show_frame("MainMenu"))
        btn_back.pack(pady=20)