
import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

FILE = "students.csv"
FIELDS = ["Roll No", "Name", "Maths", "Python", "English",
          "Attendance", "Total", "Percentage", "Grade", "Status"]

BG = "#F3F6FC"
NAVY = "#142747"
BLUE = "#3478F6"
GREEN = "#159A78"
PURPLE = "#7959D9"
ORANGE = "#E98A3A"


def grade(p):
    if p >= 90:
        return "A+"
    if p >= 80:
        return "A"
    if p >= 70:
        return "B"
    if p >= 60:
        return "C"
    if p >= 40:
        return "D"
    return "F"


class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Performance Analytics")
        self.root.geometry("1250x800")
        self.root.minsize(1050, 680)
        self.root.configure(bg=BG)
        self.students = []
        self.editing_roll = None

        self.setup_style()
        self.load_data()
        self.build_ui()
        self.refresh()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white",
                        fieldbackground="white", rowheight=31,
                        font=("Segoe UI", 10), borderwidth=0)
        style.configure("Treeview.Heading", background="#E9EFF9",
                        foreground=NAVY, font=("Segoe UI", 10, "bold"),
                        padding=9, relief="flat")
        style.map("Treeview", background=[("selected", "#D8E7FF")],
                  foreground=[("selected", NAVY)])
        style.configure("TEntry", padding=7)

    def build_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Sidebar
        side = tk.Frame(self.root, bg=NAVY, width=190)
        side.grid(row=0, column=0, sticky="ns")
        side.grid_propagate(False)

        tk.Label(side, text="🎓  STUDENT\n      ANALYTICS",
                 bg=NAVY, fg="white", font=("Segoe UI", 15, "bold"),
                 justify="left", pady=27).pack(fill="x")

        for text in ["▦  Dashboard", "♟  Students",
                     "▥  Analytics", "▤  Reports"]:
            tk.Label(side, text=text, bg=NAVY, fg="#DCE7F8",
                     font=("Segoe UI", 11), anchor="w",
                     padx=20, pady=15).pack(fill="x")

        tk.Label(side, text="BETTER INSIGHTS\nFOR BRIGHTER FUTURES",
                 bg=NAVY, fg="#9DB6D9", font=("Segoe UI", 9, "italic"),
                 justify="left").pack(side="bottom", pady=25, padx=12)

        # Main content and scrollable area
        main = tk.Frame(self.root, bg=BG)
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=14)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(4, weight=1)

        header = tk.Frame(main, bg=BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        tk.Label(header, text="Student Performance Dashboard",
                 bg=BG, fg=NAVY, font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(header, text="Monitor academic progress and attendance",
                 bg=BG, fg="#697A96", font=("Segoe UI", 10)).pack(anchor="w", pady=3)

        # KPI cards
        self.cards_frame = tk.Frame(main, bg=BG)
        self.cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 13))
        for i in range(4):
            self.cards_frame.grid_columnconfigure(i, weight=1, uniform="cards")

        self.kpis = []
        card_info = [
            ("TOTAL STUDENTS", BLUE),
            ("CLASS AVERAGE", GREEN),
            ("PASS RATE", PURPLE),
            ("LOW ATTENDANCE", ORANGE)
        ]
        for i, (title, color) in enumerate(card_info):
            card = tk.Frame(self.cards_frame, bg="white",
                            highlightbackground="#DFE7F2", highlightthickness=1)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 7, 0),
                      ipady=10)
            tk.Frame(card, bg=color, height=4).pack(fill="x")
            tk.Label(card, text=title, bg="white", fg="#64748B",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=13, pady=(10, 3))
            value = tk.Label(card, text="0", bg="white", fg=NAVY,
                             font=("Segoe UI", 21, "bold"))
            value.pack(anchor="w", padx=13, pady=(0, 10))
            self.kpis.append(value)

        # Add student form
        form = tk.LabelFrame(main, text="  Student Details  ",
                             bg="white", fg=NAVY,
                             font=("Segoe UI", 10, "bold"),
                             padx=10, pady=7)
        form.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        for i in range(6):
            form.grid_columnconfigure(i, weight=1)

        self.entries = {}
        fields = [
            ("Roll No", "roll"), ("Student Name", "name"),
            ("Maths", "maths"), ("Python", "python"),
            ("English", "english"), ("Attendance %", "attendance")
        ]
        for i, (label, key) in enumerate(fields):
            box = tk.Frame(form, bg="white")
            box.grid(row=0, column=i, sticky="ew", padx=4)
            tk.Label(box, text=label, bg="white", fg="#52627A",
                     font=("Segoe UI", 9)).pack(anchor="w")
            entry = ttk.Entry(box)
            entry.pack(fill="x", pady=(4, 2))
            self.entries[key] = entry

        actions = tk.Frame(form, bg="white")
        actions.grid(row=1, column=0, columnspan=6, sticky="w", pady=(8, 0))
        self.add_btn = self.make_button(actions, "＋ Add Student",
                                        BLUE, self.add_student)
        self.add_btn.pack(side="left", padx=(0, 6))
        self.make_button(actions, "Clear", "#64748B",
                         self.clear_form).pack(side="left", padx=6)
        self.make_button(actions, "Delete Selected", "#D9534F",
                         self.delete_student).pack(side="left", padx=6)
        self.make_button(actions, "Edit Selected", PURPLE,
                         self.edit_student).pack(side="left", padx=6)

        # Analytics charts
        charts = tk.Frame(main, bg=BG)
        charts.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        charts.grid_columnconfigure(0, weight=1)
        charts.grid_columnconfigure(1, weight=1)

        self.fig = Figure(figsize=(8, 2.55), dpi=100, facecolor=BG)
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)
        self.fig.subplots_adjust(left=0.08, right=0.97,
                                 top=0.82, bottom=0.19, wspace=0.38)
        self.chart = FigureCanvasTkAgg(self.fig, master=charts)
        self.chart.get_tk_widget().grid(row=0, column=0, columnspan=2,
                                        sticky="ew")

        # Student records
        records = tk.Frame(main, bg="white",
                           highlightbackground="#DFE7F2", highlightthickness=1)
        records.grid(row=4, column=0, sticky="nsew")
        records.grid_columnconfigure(0, weight=1)
        records.grid_rowconfigure(1, weight=1)

        top = tk.Frame(records, bg="white")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        tk.Label(top, text="Student Records", bg="white", fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        self.search = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self.search, width=25)
        search_entry.pack(side="right", padx=5)
        search_entry.insert(0, "")
        self.search.trace_add("write", lambda *_: self.refresh_table())

        table_frame = tk.Frame(records, bg="white")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.table = ttk.Treeview(table_frame, columns=FIELDS,
                                  show="headings", selectmode="browse")
        widths = [65, 115, 65, 65, 65, 85, 65, 85, 55, 125]
        for field, width in zip(FIELDS, widths):
            self.table.heading(field, text=field)
            self.table.column(field, width=width, minwidth=50, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical",
                               command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        self.table.tag_configure("pass", foreground="#13805E")
        self.table.tag_configure("fail", foreground="#C24141")

        tk.Label(main, text="Student Performance Analysis System  |  Python + Tkinter + CSV + Matplotlib",
                 bg=BG, fg="#7B8AA2", font=("Segoe UI", 8)).grid(
                     row=5, column=0, pady=(8, 0))

    def make_button(self, parent, text, color, command):
        return tk.Button(parent, text=text, command=command,
                         bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat",
                         padx=12, pady=7, cursor="hand2",
                         font=("Segoe UI", 9, "bold"))

    def load_data(self):
        if not os.path.exists(FILE):
            return
        try:
            with open(FILE, "r", newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if all(field in row for field in FIELDS):
                        self.students.append(row)
        except (OSError, csv.Error) as e:
            messagebox.showerror("CSV Error", str(e))

    def save_data(self):
        with open(FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(self.students)

    def add_student(self):
        v = {key: entry.get().strip() for key, entry in self.entries.items()}
        if not v["roll"] or not v["name"]:
            messagebox.showerror("Missing Details", "Enter roll number and name.")
            return
        if any(s["Roll No"].lower() == v["roll"].lower()
               and s["Roll No"] != self.editing_roll for s in self.students):
            messagebox.showerror("Duplicate", "This roll number already exists.")
            return
        try:
            marks = [float(v[k]) for k in ("maths", "python", "english")]
            attendance = float(v["attendance"])
        except ValueError:
            messagebox.showerror("Invalid Input", "Enter numeric marks and attendance.")
            return
        if any(m < 0 or m > 100 for m in marks) or not 0 <= attendance <= 100:
            messagebox.showerror("Invalid Range", "Marks and attendance must be 0–100.")
            return

        total = sum(marks)
        pct = total / 3
        student = {
            "Roll No": v["roll"], "Name": v["name"],
            "Maths": str(marks[0]), "Python": str(marks[1]),
            "English": str(marks[2]), "Attendance": str(attendance),
            "Total": f"{total:.1f}", "Percentage": f"{pct:.2f}",
            "Grade": grade(pct),
            "Status": "Pass" if all(m >= 40 for m in marks) else "Needs Help"
        }

        if self.editing_roll:
            self.students = [s for s in self.students
                             if s["Roll No"] != self.editing_roll]
            self.editing_roll = None
            self.add_btn.config(text="＋ Add Student")
        self.students.append(student)
        try:
            self.save_data()
        except OSError as e:
            messagebox.showerror("Save Error", str(e))
            return
        self.clear_form()
        self.refresh()
        messagebox.showinfo("Saved", "Student record saved successfully.")

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.editing_roll = None
        self.add_btn.config(text="＋ Add Student")

    def edit_student(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Select Student", "Select a student record first.")
            return
        roll = self.table.item(selected[0], "values")[0]
        s = next((s for s in self.students if s["Roll No"] == roll), None)
        if not s:
            return
        for key, field in [("roll", "Roll No"), ("name", "Name"),
                           ("maths", "Maths"), ("python", "Python"),
                           ("english", "English"), ("attendance", "Attendance")]:
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, s[field])
        self.editing_roll = roll
        self.add_btn.config(text="Save Changes")

    def delete_student(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Select Student", "Select a student record first.")
            return
        roll = self.table.item(selected[0], "values")[0]
        if not messagebox.askyesno("Confirm Delete", f"Delete student {roll}?"):
            return
        self.students = [s for s in self.students if s["Roll No"] != roll]
        self.save_data()
        self.clear_form()
        self.refresh()

    def refresh_table(self):
        query = self.search.get().strip().lower()
        self.table.delete(*self.table.get_children())
        for s in self.students:
            if query and query not in s["Name"].lower() and query not in s["Roll No"].lower():
                continue
            tag = "pass" if s["Status"] == "Pass" else "fail"
            self.table.insert("", "end",
                              values=[s.get(f, "") for f in FIELDS],
                              tags=(tag,))

    def refresh(self):
        self.refresh_table()
        n = len(self.students)
        if not n:
            self.kpis[0].config(text="0")
            self.kpis[1].config(text="0.0%")
            self.kpis[2].config(text="0.0%")
            self.kpis[3].config(text="0")
        else:
            avg = sum(float(s["Percentage"]) for s in self.students) / n
            passed = sum(s["Status"] == "Pass" for s in self.students)
            low = sum(float(s["Attendance"]) < 75 for s in self.students)
            self.kpis[0].config(text=str(n))
            self.kpis[1].config(text=f"{avg:.1f}%")
            self.kpis[2].config(text=f"{passed / n * 100:.1f}%")
            self.kpis[3].config(text=str(low))

        self.update_charts()

    def update_charts(self):
        self.ax1.clear()
        self.ax2.clear()
        self.ax1.set_title("Subject-wise Average Marks", loc="left",
                           fontsize=10, fontweight="bold", color=NAVY)
        self.ax2.set_title("Grade Distribution", loc="left",
                           fontsize=10, fontweight="bold", color=NAVY)

        if self.students:
            subjects = ["Maths", "Python", "English"]
            averages = [
                sum(float(s[sub]) for s in self.students) / len(self.students)
                for sub in subjects
            ]
            bars = self.ax1.bar(subjects, averages,
                                color=["#22A699", "#5278D4", "#8865D8"],
                                width=0.55)
            self.ax1.set_ylim(0, 110)
            self.ax1.set_ylabel("Average marks", fontsize=8)
            self.ax1.tick_params(labelsize=8)
            self.ax1.spines[["top", "right"]].set_visible(False)
            self.ax1.grid(axis="y", alpha=0.2)
            self.ax1.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)

            counts = {}
            for s in self.students:
                counts[s["Grade"]] = counts.get(s["Grade"], 0) + 1
            labels = [g for g in ["A+", "A", "B", "C", "D", "F"] if counts.get(g)]
            sizes = [counts[g] for g in labels]
            self.ax2.pie(sizes, labels=labels, autopct="%1.0f%%",
                         startangle=90, textprops={"fontsize": 8},
                         colors=["#22A699", "#5278D4", "#8865D8",
                                 "#F0B44C", "#ED8C55", "#D95D5D"][:len(labels)])
        else:
            self.ax1.text(0.5, 0.5, "Add students to view analysis",
                          ha="center", va="center", transform=self.ax1.transAxes)
            self.ax2.text(0.5, 0.5, "Grade data will appear here",
                          ha="center", va="center", transform=self.ax2.transAxes)
        self.fig.tight_layout()
        self.chart.draw()
if __name__ == "__main__":
    root = tk.Tk()
    app = StudentApp(root)
    root.mainloop()