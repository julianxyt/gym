import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys
import csv
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SAMPLE_SPREADSHEET_ID = '1Sj0V5vqf2LNmoHRGCjU3vcVuPBDR-z_pG8BCaHBrxgs'
SAMPLE_RANGE_NAME = 'GymReps'

class GymApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gym Workout Tracker")
        self.root.geometry("800x600")

        self.label = ttk.Label(self.root, text="Gym Workout Tracker", font=("Arial", 20))
        self.label.pack(pady=20)

        self.setup_input_fields()

    def setup_input_fields(self):
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=10)

        # Date
        ttk.Label(input_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
        self.date_entry = ttk.Entry(input_frame)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)

        # Exercise
        ttk.Label(input_frame, text="Exercise:").grid(row=1, column=0, padx=5, pady=5)
        self.exercise_var = tk.StringVar()
        self.exercise_combobox = ttk.Combobox(input_frame, textvariable=self.exercise_var, state="readonly")
        self.exercise_combobox['values'] = (
            "Squat", "Bench Press", "Deadlift", "Overhead Press",
            "Pull-up", "Barbell Row", "Leg Press", "Dumbbell Curl",
            "Tricep Extension", "Lat Pulldown"
        )
        self.exercise_combobox.grid(row=1, column=1, padx=5, pady=5)

        # Weight
        ttk.Label(input_frame, text="Weight:").grid(row=2, column=0, padx=5, pady=5)
        self.weight_entry = ttk.Entry(input_frame)
        self.weight_entry.grid(row=2, column=1, padx=5, pady=5)

        # Sets
        ttk.Label(input_frame, text="Sets:").grid(row=3, column=0, padx=5, pady=5)
        self.sets_entry = ttk.Entry(input_frame)
        self.sets_entry.grid(row=3, column=1, padx=5, pady=5)

        # Reps
        ttk.Label(input_frame, text="Reps:").grid(row=4, column=0, padx=5, pady=5)
        self.reps_entry = ttk.Entry(input_frame)
        self.reps_entry.grid(row=4, column=1, padx=5, pady=5)

        # Save Button
        self.save_button = ttk.Button(self.root, text="Save Workout", command=self.save_workout)
        self.save_button.pack(pady=10)

        # Sync Button
        self.sync_button = ttk.Button(self.root, text="Sync to Google Sheets", command=self.sync_to_sheets)
        self.sync_button.pack(pady=5)

        self.setup_treeview()

    def setup_treeview(self):
        # Treeview to display workouts
        columns = ("Date", "Exercise", "Weight", "Sets", "Reps")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        self.tree.pack(pady=20, fill="both", expand=True)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)

        self.load_workouts_to_tree()

    def load_workouts_to_tree(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        if os.path.isfile("workouts.csv"):
            with open("workouts.csv", newline="") as file:
                reader = csv.reader(file)
                try:
                    next(reader) # Skip header
                except StopIteration:
                    pass
                for row in reader:
                    self.tree.insert("", tk.END, values=row)

    def save_workout(self):
        date = self.date_entry.get()
        exercise = self.exercise_var.get()
        weight = self.weight_entry.get()
        sets = self.sets_entry.get()
        reps = self.reps_entry.get()

        if not all([date, exercise, weight, sets, reps]):
            messagebox.showwarning("Missing Input", "Please fill out all fields.")
            return

        file_exists = os.path.isfile("workouts.csv")

        try:
            with open("workouts.csv", mode="a", newline="") as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["Date", "Exercise", "Weight", "Sets", "Reps"])
                writer.writerow([date, exercise, weight, sets, reps])

            if not getattr(self, "headless_test", False):
                messagebox.showinfo("Success", "Workout saved successfully!")

            self.load_workouts_to_tree()

            # Clear inputs
            self.date_entry.delete(0, tk.END)
            self.exercise_combobox.set('')
            self.weight_entry.delete(0, tk.END)
            self.sets_entry.delete(0, tk.END)
            self.reps_entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"Could not save workout: {e}")

    def sync_to_sheets(self):
        if not os.path.exists("workouts.csv"):
            messagebox.showinfo("Info", "No workouts.csv found to sync.")
            return

        creds = None
        if os.path.exists('gymenv/token.json'):
            creds = Credentials.from_authorized_user_file('gymenv/token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    messagebox.showerror("Error", f"Could not refresh token: {e}")
                    return
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'gymenv/credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open credentials: {e}")
                    return
            with open('gymenv/token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('sheets', 'v4', credentials=creds)

            with open("workouts.csv", "r") as file:
                reader = csv.reader(file)
                values = list(reader)

            if len(values) <= 1:
                messagebox.showinfo("Info", "No data to sync in workouts.csv.")
                return

            body = {
                'values': values[1:] # Skip header
            }

            result = service.spreadsheets().values().append(
                spreadsheetId=SAMPLE_SPREADSHEET_ID,
                range=SAMPLE_RANGE_NAME,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()

            if not getattr(self, "headless_test", False):
                messagebox.showinfo("Success", f"Synced {result.get('updates').get('updatedRows')} rows to Google Sheets.")

        except HttpError as err:
            messagebox.showerror("Google Sheets API Error", str(err))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

def main():
    root = tk.Tk()
    app = GymApp(root)

    # For testing, exit quickly
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        root.after(100, root.destroy)

    root.mainloop()

if __name__ == "__main__":
    main()