import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class DeadliftApp(tk.Tk):
	"""Główna klasa aplikacji zarządzająca oknem i przełączaniem widoków."""

	def __init__(self):
		super().__init__()

		self.title("Asystent Martwego Ciągu")
		self.geometry("900x600")
		self.minsize(800, 500)

		self.training_data = {
			"sets": 0,
			"height": 0.0,
			"weight": 0.0
		}

		container = tk.Frame(self)
		container.pack(side="top", fill="both", expand=True)
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)

		self.frames = {}

		for F in (MainMenu, TrainingSetup, TrainingView, TrainingHistory):
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
		"""Waliduje dane, zapisuje je i przechodzi do widoku z kamerami."""
		try:
			sets = int(self.entry_sets.get())
			height = float(self.entry_height.get())
			weight = float(self.entry_weight.get())
			self.controller.training_data["sets"] = sets
			self.controller.training_data["height"] = height
			self.controller.training_data["weight"] = weight


			self.entry_sets.delete(0, tk.END)
			self.entry_height.delete(0, tk.END)
			self.entry_weight.delete(0, tk.END)

			self.controller.show_frame("TrainingView")
		except ValueError:
			messagebox.showerror("Błąd", "Wprowadź poprawne wartości liczbowe!")


class TrainingView(tk.Frame):
	"""Główny ekran treningu zawierający dwa widoki z kamer."""

	def __init__(self, parent, controller):
		super().__init__(parent)
		self.controller = controller


		top_frame = tk.Frame(self)
		top_frame.pack(side="top", fill="x", pady=10)

		lbl_title = tk.Label(top_frame, text="Trening Trwa - Martwy Ciąg", font=("Helvetica", 18, "bold"))
		lbl_title.pack()

		cams_frame = tk.Frame(self)
		cams_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)
		cams_frame.grid_columnconfigure(0, weight=1)
		cams_frame.grid_columnconfigure(1, weight=1)
		cams_frame.grid_rowconfigure(0, weight=1)


		self.cam1_label = tk.Label(cams_frame, text="Kamera 1 (Bok)\n[Oczekuje na sygnał video...]",
		                           bg="#2c3e50", fg="white", font=("Helvetica", 14))
		self.cam1_label.grid(row=0, column=0, sticky="nsew", padx=10)

		self.cam2_label = tk.Label(cams_frame, text="Kamera 2 (Przód)\n[Oczekuje na sygnał video...]",
		                           bg="#2c3e50", fg="white", font=("Helvetica", 14))
		self.cam2_label.grid(row=0, column=1, sticky="nsew", padx=10)


		bottom_frame = tk.Frame(self)
		bottom_frame.pack(side="bottom", fill="x", pady=20)

		btn_end = tk.Button(bottom_frame, text="Zakończ trening", font=("Helvetica", 14), bg="red", fg="white",
		                    width=20,
		                    command=lambda: controller.show_frame("MainMenu"))
		btn_end.pack()


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


if __name__ == "__main__":
	app = DeadliftApp()
	app.mainloop()