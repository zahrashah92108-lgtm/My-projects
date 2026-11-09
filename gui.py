# ==============================================================
# Student Result Manager - GUI Version (gui.py)
# --------------------------------------------------------------
# A modern-looking window built with tkinter. It uses the data
# functions from main.py, so both versions share the same
# students.json file.
# Features: add, update, delete, search, topper, ranking,
# pass/fail status, show failed, import CSV and export CSV.
# ==============================================================

import csv                                        # to read and write CSV files
import tkinter as tk                              # main GUI library
from tkinter import ttk, messagebox, filedialog   # table, popups, file dialogs
from main import load_data, save_data, calculate_grade

# A student passes only if EVERY subject is at or above this mark.
# Change this number if your school uses different pass marks.
PASS_MARKS = 33

# Columns in a CSV file that are not subjects. They are ignored
# when importing, so a file made by "Export CSV" can be imported too.
IGNORED_COLUMNS = {"roll no", "name", "total", "percentage", "grade", "status"}

# --------------------------------------------------------------
# Colors and font (change these to restyle the whole program)
# --------------------------------------------------------------
FONT = "Segoe UI"
BG = "#f4f6fb"            # window background
HEADER_BG = "#1e3a5f"     # header and table heading color
CARD_BG = "#ffffff"       # white cards
TEXT = "#1f2937"          # main text
MUTED = "#6b7280"         # small grey text
GREEN = "#16a34a"
BLUE = "#2563eb"
RED = "#dc2626"
ORANGE = "#ea580c"
PURPLE = "#7c3aed"
TEAL = "#0d9488"

# Table row colors: (background, text)
ROW_ODD = ("#ffffff", TEXT)
ROW_EVEN = ("#f1f5f9", TEXT)
ROW_FAIL = ("#fee2e2", "#b91c1c")
ROW_SELECTED = ("#bfdbfe", TEXT)


# --------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------

# Convert text like "Math:85, English:78" into a dictionary
# {"Math": 85.0, "English": 78.0}. Raises ValueError if the
# text is in the wrong format or the marks are not valid.
def parse_subjects(text):
    subjects = {}
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError("Write subjects like this: Math:85, English:78")
        name, marks = part.split(":", 1)
        try:
            marks = float(marks)
        except ValueError:
            raise ValueError(f"Marks for '{name.strip()}' must be a number")
        if not 0 <= marks <= 100:
            raise ValueError("Marks must be between 0 and 100")
        subjects[name.strip()] = marks
    if not subjects:
        raise ValueError("Enter at least one subject")
    return subjects


# Create a complete student record (total, percentage, grade)
# from the name and the subjects dictionary
def build_record(name, subjects):
    total = sum(subjects.values())
    percentage = round(total / (len(subjects) * 100) * 100, 2)
    return {
        "name": name,
        "subjects": subjects,
        "total": total,
        "percentage": percentage,
        "grade": calculate_grade(percentage),
    }


# Convert a subjects dictionary back into text like "Math:85, English:78"
# (:g removes the extra ".0" from numbers like 85.0)
def subjects_to_text(subjects):
    return ", ".join(f"{k}:{v:g}" for k, v in subjects.items())


# Return "Pass" if all subjects are at or above PASS_MARKS,
# otherwise return "Fail". The status is calculated every time,
# so it is not stored in students.json.
def get_status(s):
    if all(m >= PASS_MARKS for m in s["subjects"].values()):
        return "Pass"
    return "Fail"


# --------------------------------------------------------------
# Main window and styles
# --------------------------------------------------------------

root = tk.Tk()
root.title("Student Result Manager")
root.configure(bg=BG)
root.minsize(1000, 620)

# Open the window in the middle of the screen
WIN_W, WIN_H = 1100, 680
pos_x = (root.winfo_screenwidth() - WIN_W) // 2
pos_y = max((root.winfo_screenheight() - WIN_H) // 2 - 30, 0)
root.geometry(f"{WIN_W}x{WIN_H}+{pos_x}+{pos_y}")

# "clam" is a theme that allows custom colors on buttons and tables
style = ttk.Style()
style.theme_use("clam")

# Table look
style.configure(
    "Table.Treeview",
    background="white",
    fieldbackground="white",
    foreground=TEXT,
    rowheight=32,
    font=(FONT, 10),
    borderwidth=0,
)
style.configure(
    "Table.Treeview.Heading",
    background=HEADER_BG,
    foreground="white",
    font=(FONT, 10, "bold"),
    relief="flat",
    padding=8,
)
style.map("Table.Treeview.Heading", background=[("active", "#2c5282")])

# Text box look
style.configure("TEntry", padding=6)


# Create one colored button style with a darker color on hover
def make_button_style(name, color, hover):
    style.configure(
        f"{name}.TButton",
        background=color,
        foreground="white",
        font=(FONT, 10, "bold"),
        padding=(14, 8),
        borderwidth=0,
        relief="flat",
        focuscolor=color,
    )
    style.map(
        f"{name}.TButton",
        background=[("active", hover), ("pressed", hover)],
        foreground=[("active", "white")],
    )


make_button_style("Green", GREEN, "#15803d")
make_button_style("Blue", BLUE, "#1d4ed8")
make_button_style("Red", RED, "#b91c1c")
make_button_style("Gray", "#6b7280", "#4b5563")
make_button_style("Orange", ORANGE, "#c2410c")
make_button_style("Purple", PURPLE, "#6d28d9")
make_button_style("Teal", TEAL, "#0f766e")

# These variables are linked to the three text boxes
roll_var = tk.StringVar()
name_var = tk.StringVar()
subjects_var = tk.StringVar()
status_var = tk.StringVar(value="Ready")

# Remembers the normal color tag of each row (roll -> tag name),
# so a row can go back to its color after it is unselected
row_tags = {}

# The number labels inside the four stat cards (filled in later)
stat_labels = {}


# --------------------------------------------------------------
# Functions that update the screen
# --------------------------------------------------------------

# Show a short message in the status bar at the bottom
def set_status(text):
    status_var.set(text)


# Update the four cards at the top using ALL students
def update_stats(data):
    total = len(data)
    failed = sum(1 for s in data.values() if get_status(s) == "Fail")
    top = max((s["percentage"] for s in data.values()), default=0)
    stat_labels["total"].config(text=str(total))
    stat_labels["passed"].config(text=str(total - failed))
    stat_labels["failed"].config(text=str(failed))
    stat_labels["top"].config(text=f"{top:g}%")


# Fill the table with students. If "rows" is given, only those
# students are shown (used by search, topper, ranking and failed).
# Otherwise all students are shown.
def refresh(rows=None):
    table.delete(*table.get_children())   # remove old rows
    row_tags.clear()
    data = load_data()
    items = rows if rows is not None else list(data.items())
    for index, (roll, s) in enumerate(items):
        status = get_status(s)
        # Failed rows are red, other rows alternate white / light blue
        if status == "Fail":
            tag = "fail"
        else:
            tag = "even" if index % 2 else "odd"
        row_tags[roll] = tag
        # iid=roll lets us find the row again by roll number
        table.insert(
            "",
            "end",
            iid=roll,
            values=(
                roll,
                s["name"],
                subjects_to_text(s["subjects"]),
                f"{s['total']:g}",
                f"{s['percentage']}%",
                s["grade"],
                status,
            ),
            tags=(tag,),
        )
    update_stats(data)
    set_status(f"Showing {len(items)} of {len(data)} student(s)")


# Empty all three text boxes and remove the row highlight
def clear_fields():
    roll_var.set("")
    name_var.set("")
    subjects_var.set("")
    table.selection_set(())


# When a row is clicked: highlight it and copy its values into
# the text boxes so the user can easily update or delete it
def on_select(event):
    selected = table.selection()
    # Selected row gets the blue color, the others get their own color
    for iid, base in row_tags.items():
        table.item(iid, tags=("selected",) if iid in selected else (base,))
    if not selected:
        return
    roll = selected[0]
    s = load_data().get(roll)
    if s:
        roll_var.set(roll)
        name_var.set(s["name"])
        subjects_var.set(subjects_to_text(s["subjects"]))


# --------------------------------------------------------------
# Button functions
# --------------------------------------------------------------

# Add a new student using the values in the text boxes
def add_student():
    roll = roll_var.get().strip()
    name = name_var.get().strip()
    if not roll or not name:
        messagebox.showerror("Error", "Roll No and Name are required")
        return
    data = load_data()
    if roll in data:
        messagebox.showerror("Error", "This roll number already exists")
        return
    try:
        subjects = parse_subjects(subjects_var.get())
    except ValueError as e:
        messagebox.showerror("Error", str(e))
        return
    data[roll] = build_record(name, subjects)
    save_data(data)
    clear_fields()
    refresh()
    messagebox.showinfo("Done", "Student added successfully!")


# Update an existing student (found by roll number) with the
# new name and subjects from the text boxes
def update_student():
    roll = roll_var.get().strip()
    data = load_data()
    if roll not in data:
        messagebox.showerror("Error", "Student not found")
        return
    # If the name box is empty, keep the old name
    name = name_var.get().strip() or data[roll]["name"]
    try:
        subjects = parse_subjects(subjects_var.get())
    except ValueError as e:
        messagebox.showerror("Error", str(e))
        return
    data[roll] = build_record(name, subjects)
    save_data(data)
    clear_fields()
    refresh()
    messagebox.showinfo("Done", "Student updated successfully!")


# Delete a student after asking for confirmation
def delete_student():
    roll = roll_var.get().strip()
    data = load_data()
    if roll not in data:
        messagebox.showerror("Error", "Student not found")
        return
    if messagebox.askyesno("Confirm", f"Delete {data[roll]['name']}?"):
        del data[roll]
        save_data(data)
        clear_fields()
        refresh()


# Show only the student whose roll number is in the Roll No box
def search_student():
    roll = roll_var.get().strip()
    data = load_data()
    if roll in data:
        refresh([(roll, data[roll])])
    else:
        messagebox.showerror("Error", "Student not found")


# Show the student with the highest percentage
def show_topper():
    data = load_data()
    if not data:
        messagebox.showinfo("Topper", "No students found yet")
        return
    roll, s = max(data.items(), key=lambda item: item[1]["percentage"])
    refresh([(roll, s)])
    messagebox.showinfo(
        "Topper",
        f"{s['name']} (Roll {roll})\n{s['percentage']}% - Grade {s['grade']}",
    )


# Show only the students who failed (at least one subject
# below PASS_MARKS)
def show_failed():
    data = load_data()
    failed = [(roll, s) for roll, s in data.items() if get_status(s) == "Fail"]
    if not failed:
        messagebox.showinfo("Failed Students", "No student has failed")
        return
    refresh(failed)


# Show all students ordered from highest to lowest percentage.
# Students with the same percentage get the same rank.
def show_ranking():
    data = load_data()
    if not data:
        messagebox.showinfo("Ranking", "No students found yet")
        return
    ranked = sorted(
        data.items(), key=lambda item: item[1]["percentage"], reverse=True
    )
    refresh(ranked)
    lines = []
    rank = 0
    last_percentage = None
    for position, (roll, s) in enumerate(ranked, start=1):
        # A new rank starts only when the percentage changes
        if s["percentage"] != last_percentage:
            rank = position
            last_percentage = s["percentage"]
        lines.append(f"{rank}. {s['name']} (Roll {roll}) - {s['percentage']}%")
    messagebox.showinfo("Ranking", "\n".join(lines))


# Save all results to a CSV file that opens in Excel
def export_csv():
    data = load_data()
    if not data:
        messagebox.showinfo("Export", "No students to export")
        return
    # Ask the user where to save the file
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV file", "*.csv")],
        initialfile="results.csv",
    )
    if not path:
        return   # user pressed Cancel
    try:
        # utf-8-sig makes Excel read the file correctly
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Roll No", "Name", "Subjects", "Total", "Percentage", "Grade", "Status"]
            )
            for roll, s in data.items():
                writer.writerow([
                    roll,
                    s["name"],
                    subjects_to_text(s["subjects"]),
                    f"{s['total']:g}",
                    s["percentage"],
                    s["grade"],
                    get_status(s),
                ])
    except OSError as e:
        # For example, the file is already open in Excel
        messagebox.showerror("Error", f"Could not save file: {e}")
        return
    messagebox.showinfo("Done", "Results exported successfully!")


# Add many students at once from a CSV file (made in Excel).
# The first row must contain "Roll No" and "Name". Every other
# column is treated as a subject, and the cell holds the marks.
# Rows with a problem are skipped and reported at the end.
def import_csv():
    path = filedialog.askopenfilename(filetypes=[("CSV file", "*.csv")])
    if not path:
        return   # user pressed Cancel

    data = load_data()
    added = 0
    skipped = []

    try:
        with open(path, "r", newline="", encoding="utf-8-sig", errors="replace") as f:
            # Detect if the file uses commas or semicolons
            sample = f.read(2048)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            except csv.Error:
                dialect = csv.excel

            reader = csv.DictReader(f, dialect=dialect)
            headers = [h.strip().lower() for h in (reader.fieldnames or [])]
            if "roll no" not in headers or "name" not in headers:
                messagebox.showerror(
                    "Error", "The first row must contain 'Roll No' and 'Name' columns"
                )
                return

            # line_no starts at 2 because line 1 is the header row
            for line_no, row in enumerate(reader, start=2):
                clean = {}
                for k, v in row.items():
                    if k is None:
                        continue
                    clean[k.strip()] = (v or "").strip()
                lower = {k.lower(): v for k, v in clean.items()}

                roll = lower.get("roll no", "")
                name = lower.get("name", "")
                if not roll or not name:
                    skipped.append(f"Row {line_no}: Roll No or Name is missing")
                    continue
                if roll in data:
                    skipped.append(f"Row {line_no}: Roll {roll} already exists")
                    continue

                # Collect the marks from every subject column
                try:
                    subjects = {}
                    for col, value in clean.items():
                        low = col.lower()
                        if low in IGNORED_COLUMNS or not value:
                            continue
                        if low == "subjects":
                            subjects.update(parse_subjects(value))
                        else:
                            subjects.update(parse_subjects(f"{col}:{value}"))
                    if not subjects:
                        raise ValueError("No marks found")
                except ValueError as e:
                    skipped.append(f"Row {line_no}: {e}")
                    continue

                data[roll] = build_record(name, subjects)
                added += 1
    except OSError as e:
        # For example, the file is still open in Excel
        messagebox.showerror("Error", f"Could not read file: {e}")
        return

    save_data(data)
    refresh()

    message = f"{added} student(s) imported."
    if skipped:
        message += f"\n\n{len(skipped)} row(s) skipped:\n" + "\n".join(skipped[:10])
        if len(skipped) > 10:
            message += "\n..."
    messagebox.showinfo("Import finished", message)


# --------------------------------------------------------------
# Screen layout
# --------------------------------------------------------------
# Subject names used the last time the spreadsheet window was opened
sheet_subjects = {"text": "Math, English, Urdu,science"}


# Open a window that looks like an Excel sheet. Each row is one
# student. The columns are Roll No, Name and one column per subject.
# The user types directly in the cells and saves all rows at once.
def open_sheet():
    win = tk.Toplevel(root, bg=BG, padx=16, pady=14)
    win.title("Sheet Entry")
    win.transient(root)   # keep this window on top of the main window

    subjects_text = tk.StringVar(value=sheet_subjects["text"])
    message_var = tk.StringVar(value="")
    headings = []    # column headings: Roll No, Name, then the subjects
    cells = []       # cells[r][c] = the text box in row r, column c
    cell_vars = []   # cell_vars[r][c] = the text typed in that box

    # Width (in characters) of each column
    def column_width(c):
        return 10 if c == 0 else 24 if c == 1 else 10

    # Scroll the sheet so the active cell is visible
    def ensure_visible(widget):
        win.update_idletasks()
        total = grid_frame.winfo_height()
        view = canvas.winfo_height()
        if total <= view:
            return
        top = canvas.canvasy(0)
        y = widget.winfo_y()
        h = widget.winfo_height()
        if y < top:
            canvas.yview_moveto(y / total)
        elif y + h > top + view:
            canvas.yview_moveto((y + h - view) / total)

    # Put the cursor in a cell and select its text
    # (typing then replaces the old text, like in Excel)
    def focus_cell(r, c):
        entry = cells[r][c]
        entry.focus_set()
        entry.select_range(0, "end")
        entry.icursor("end")

    # Go to another row in the same column (adds rows at the bottom)
    def move(r, c):
        r = max(r, 0)
        if r >= len(cells):
            add_rows(5)
        focus_cell(r, c)
        return "break"

    # Right arrow: go to the next cell when the cursor is at the end
    def step_right(r, c):
        entry = cells[r][c]
        at_end = entry.selection_present() or entry.index("insert") >= len(entry.get())
        if at_end and c + 1 < len(headings):
            focus_cell(r, c + 1)
            return "break"

    # Left arrow: go to the previous cell when the cursor is at the start
    def step_left(r, c):
        entry = cells[r][c]
        at_start = entry.selection_present() or entry.index("insert") == 0
        if at_start and c > 0:
            focus_cell(r, c - 1)
            return "break"

    # Paste cells copied from Excel (Ctrl + V). Columns are separated
    # by tabs and rows by new lines. Pasting starts at the active cell.
    def paste_cells(r, c):
        try:
            text = win.clipboard_get()
        except tk.TclError:
            return "break"
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if lines and lines[-1] == "":
            lines.pop()   # Excel adds an empty line at the end
        lines = [line.split("\t") for line in lines]
        # Skip the heading row if it was copied together with the data
        if lines and c == 0 and lines[0][0].strip().lower() in ("roll no", "roll", "roll no."):
            lines.pop(0)
        if not lines:
            return "break"
        for i, values in enumerate(lines):
            while r + i >= len(cells):
                add_rows(5)
            for j, value in enumerate(values):
                if c + j < len(headings):
                    cell_vars[r + i][c + j].set(value.strip())
        message_var.set(f"Pasted {len(lines)} row(s)")
        return "break"

    # Add empty rows at the bottom of the sheet
    def add_rows(count):
        for _ in range(count):
            r = len(cells)
            tk.Label(
                grid_frame, text=str(r + 1), font=(FONT, 9), fg=MUTED,
                bg="#e5e7eb", width=4,
            ).grid(row=r + 1, column=0, padx=1, pady=1, sticky="ns")
            row_entries = []
            row_vars = []
            for c in range(len(headings)):
                var = tk.StringVar()
                entry = tk.Entry(
                    grid_frame, textvariable=var, width=column_width(c),
                    font=(FONT, 11), relief="flat", bd=3, bg="white",
                    highlightthickness=1, highlightbackground="#d1d5db",
                    highlightcolor=BLUE,
                )
                entry.grid(row=r + 1, column=c + 1, padx=0, pady=0)
                entry.bind("<Return>", lambda e, r=r, c=c: move(r + 1, c))
                entry.bind("<Down>", lambda e, r=r, c=c: move(r + 1, c))
                entry.bind("<Up>", lambda e, r=r, c=c: move(r - 1, c))
                entry.bind("<Right>", lambda e, r=r, c=c: step_right(r, c))
                entry.bind("<Left>", lambda e, r=r, c=c: step_left(r, c))
                entry.bind("<Control-v>", lambda e, r=r, c=c: paste_cells(r, c))
                entry.bind("<Control-V>", lambda e, r=r, c=c: paste_cells(r, c))
                entry.bind("<FocusIn>", lambda e: ensure_visible(e.widget))
                # Tab in the last column goes to the Name cell of the next row
                if c == len(headings) - 1:
                    entry.bind("<Tab>", lambda e, r=r: move(r + 1, 1))
                row_entries.append(entry)
                row_vars.append(var)
            cells.append(row_entries)
            cell_vars.append(row_vars)

    # Create (or re-create) the sheet using the subject names typed above.
    # What is already typed is kept for the columns that stay.
    def build_grid():
        names = []
        for part in subjects_text.get().split(","):
            part = part.strip()
            if part and part not in names:
                names.append(part)
        if not names:
            messagebox.showerror("Error", "Type at least one subject name", parent=win)
            return
        if any(":" in n for n in names):
            messagebox.showerror("Error", "Subject names cannot contain ':'", parent=win)
            return

        old = [
            {headings[c]: cell_vars[r][c].get() for c in range(len(headings))}
            for r in range(len(cells))
        ]
        sheet_subjects["text"] = ", ".join(names)
        headings[:] = ["Roll No", "Name"] + names
        for child in grid_frame.winfo_children():
            child.destroy()
        cells.clear()
        cell_vars.clear()

        # Heading row
        tk.Label(
            grid_frame, text="#", font=(FONT, 10, "bold"), fg="white",
            bg=HEADER_BG, width=4, pady=6,
        ).grid(row=0, column=0, padx=1, pady=(0, 1), sticky="ew")
        for c, head in enumerate(headings):
            tk.Label(
                grid_frame, text=head, font=(FONT, 10, "bold"), fg="white",
                bg=HEADER_BG, width=column_width(c), pady=6,
            ).grid(row=0, column=c + 1, padx=1, pady=(0, 1), sticky="ew")

        add_rows(max(len(old), 30))
        for r, record in enumerate(old):
            for c, head in enumerate(headings):
                cell_vars[r][c].set(record.get(head, ""))

        win.update_idletasks()
        canvas.configure(
            width=min(grid_frame.winfo_reqwidth(), win.winfo_screenwidth() - 140)
        )
        focus_cell(0, 1)

    # Remove the red color from all cells
    def reset_colors():
        for row in cells:
            for entry in row:
                entry.config(bg="white")

    # Empty every cell of the sheet
    def clear_grid():
        if messagebox.askyesno("Confirm", "Clear everything typed in the sheet?", parent=win):
            for row in cell_vars:
                for var in row:
                    var.set("")
            reset_colors()
            message_var.set("")
            focus_cell(0, 1)

    # Save every filled row as a student. Rows with a problem turn
    # red and stay in the sheet so they can be fixed. Saved rows are
    # cleared from the sheet.
    def save_all():
        reset_colors()
        data = load_data()
        used = set(data)   # roll numbers that are already taken
        numbers = [int(k) for k in data if k.isdecimal()]
        next_number = max(numbers) + 1 if numbers else 1
        saved_rows = []
        problems = []
        problem_rows = []

        # Remember a problem and color its row red
        def problem(r, text):
            problems.append(f"Row {r + 1}: {text}")
            problem_rows.append(r)
            for entry in cells[r]:
                entry.config(bg="#fee2e2")

        for r in range(len(cells)):
            values = [var.get().strip() for var in cell_vars[r]]
            if not any(values):
                continue   # empty row, ignore it
            roll, name = values[0], values[1]
            if not name:
                problem(r, "Name is missing")
                continue
            if not roll:
                # No roll number typed: use the next free number
                while str(next_number) in used:
                    next_number += 1
                roll = str(next_number)
            if roll in used:
                problem(r, f"Roll {roll} already exists")
                continue

            # Read the marks of every subject column
            subjects = {}
            bad = False
            for sub, text in zip(headings[2:], values[2:]):
                if not text:
                    continue   # empty cell = student does not have this subject
                try:
                    marks = float(text)
                except ValueError:
                    problem(r, f"Marks for {sub} must be a number")
                    bad = True
                    break
                if not 0 <= marks <= 100:
                    problem(r, f"Marks for {sub} must be between 0 and 100")
                    bad = True
                    break
                subjects[sub] = marks
            if bad:
                continue
            if not subjects:
                problem(r, "No marks entered")
                continue

            data[roll] = build_record(name, subjects)
            used.add(roll)
            saved_rows.append(r)

        if not saved_rows and not problems:
            messagebox.showinfo("Save", "The sheet is empty. Nothing to save.", parent=win)
            return

        if saved_rows:
            save_data(data)
            refresh()
            for r in saved_rows:
                for var in cell_vars[r]:
                    var.set("")

        message = f"{len(saved_rows)} student(s) saved."
        if problems:
            message += f"\n\n{len(problems)} row(s) need fixing (shown in red):\n"
            message += "\n".join(problems[:10])
            if len(problems) > 10:
                message += "\n..."
        message_var.set(f"Saved: {len(saved_rows)}   |   Need fixing: {len(problems)}")
        messagebox.showinfo("Save finished", message, parent=win)
        focus_cell(problem_rows[0] if problem_rows else 0, 1)

    # ----- Layout of the Sheet Entry window -----
    tk.Label(
        win, text="Sheet Entry", font=(FONT, 14, "bold"), fg=TEXT, bg=BG
    ).pack(anchor="w")
    tk.Label(
        win,
        text="Type like in Excel.  Enter = down,  Tab = next cell,  arrow keys also move.  "
        "You can copy cells from Excel and paste them here with Ctrl + V.",
        font=(FONT, 9),
        fg=MUTED,
        bg=BG,
    ).pack(anchor="w", pady=(2, 8))

    subject_row = tk.Frame(win, bg=BG)
    subject_row.pack(fill="x")
    tk.Label(
        subject_row, text="Subjects:", font=(FONT, 10), fg=TEXT, bg=BG
    ).pack(side="left")
    subject_box = ttk.Entry(
        subject_row, textvariable=subjects_text, width=50, font=(FONT, 11)
    )
    subject_box.pack(side="left", padx=8)
    subject_box.bind("<Return>", lambda e: build_grid())
    ttk.Button(
        subject_row, text="Set Subjects", style="Blue.TButton", command=build_grid
    ).pack(side="left")

    # The sheet: a canvas with a scrollbar, so many rows can be shown
    holder = tk.Frame(
        win, bg=CARD_BG, highlightbackground="#e5e7eb", highlightthickness=1
    )
    holder.pack(fill="both", expand=True, pady=(10, 0))
    canvas = tk.Canvas(holder, bg=CARD_BG, highlightthickness=0, height=380)
    scrollbar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    grid_frame = tk.Frame(canvas, bg=CARD_BG)
    canvas.create_window((0, 0), window=grid_frame, anchor="nw")
    grid_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    # Mouse wheel scrolls the sheet
    win.bind(
        "<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units")
    )

    bottom = tk.Frame(win, bg=BG)
    bottom.pack(fill="x", pady=(12, 0))
    ttk.Button(
        bottom, text="Save All", style="Green.TButton", command=save_all
    ).pack(side="left")
    ttk.Button(
        bottom, text="Add 10 Rows", style="Blue.TButton", command=lambda: add_rows(10)
    ).pack(side="left", padx=8)
    ttk.Button(
        bottom, text="Clear Sheet", style="Red.TButton", command=clear_grid
    ).pack(side="left")
    ttk.Button(
        bottom, text="Close", style="Gray.TButton", command=win.destroy
    ).pack(side="right")
    tk.Label(
        bottom, textvariable=message_var, font=(FONT, 10), fg=MUTED, bg=BG
    ).pack(side="left", padx=12)

    build_grid()
    win.focus_force()
# A white box with a thin border, used for the form and the buttons
def make_card(parent):
    return tk.Frame(
        parent,
        bg=CARD_BG,
        padx=16,
        pady=12,
        highlightbackground="#e5e7eb",
        highlightthickness=1,
    )


# Put several colored buttons side by side
def add_buttons(parent, specs):
    for text, command, color in specs:
        ttk.Button(
            parent,
            text=text,
            command=command,
            style=f"{color}.TButton",
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))


# ----- Header -----
header = tk.Frame(root, bg=HEADER_BG, padx=24, pady=14)
header.pack(fill="x")
tk.Label(
    header,
    text="Student Result Manager",
    font=(FONT, 20, "bold"),
    fg="white",
    bg=HEADER_BG,
).pack(anchor="w")
tk.Label(
    header,
    text="Add students, manage marks and see results at a glance",
    font=(FONT, 10),
    fg="#cbd5e1",
    bg=HEADER_BG,
).pack(anchor="w")

# ----- Status bar (packed early so it always stays at the bottom) -----
tk.Label(
    root,
    textvariable=status_var,
    anchor="w",
    font=(FONT, 9),
    fg=MUTED,
    bg="#e5e7eb",
    padx=20,
    pady=4,
).pack(side="bottom", fill="x")

# ----- Stat cards -----
stats = tk.Frame(root, bg=BG)
stats.pack(fill="x", padx=20, pady=(14, 10))

for column, (key, caption, color) in enumerate([
    ("total", "Total Students", BLUE),
    ("passed", "Passed", GREEN),
    ("failed", "Failed", RED),
    ("top", "Highest Percentage", ORANGE),
]):
    card = make_card(stats)
    card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0))
    stats.columnconfigure(column, weight=1)
    number = tk.Label(card, text="0", font=(FONT, 22, "bold"), fg=color, bg=CARD_BG)
    number.pack(anchor="w")
    tk.Label(card, text=caption, font=(FONT, 9), fg=MUTED, bg=CARD_BG).pack(anchor="w")
    stat_labels[key] = number

# ----- Form: text boxes for roll number, name and subjects -----
form = make_card(root)
form.pack(fill="x", padx=20, pady=(0, 10))

tk.Label(
    form, text="Student Details", font=(FONT, 12, "bold"), fg=TEXT, bg=CARD_BG
).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

tk.Label(form, text="Roll No", font=(FONT, 10), fg=TEXT, bg=CARD_BG).grid(
    row=1, column=0, sticky="w"
)
ttk.Entry(form, textvariable=roll_var, width=16, font=(FONT, 11)).grid(
    row=1, column=1, sticky="w", padx=(8, 24), pady=4
)
tk.Label(form, text="Name", font=(FONT, 10), fg=TEXT, bg=CARD_BG).grid(
    row=1, column=2, sticky="w"
)
ttk.Entry(form, textvariable=name_var, font=(FONT, 11)).grid(
    row=1, column=3, sticky="ew", padx=8, pady=4
)

tk.Label(form, text="Subjects", font=(FONT, 10), fg=TEXT, bg=CARD_BG).grid(
    row=2, column=0, sticky="w"
)
ttk.Entry(form, textvariable=subjects_var, font=(FONT, 11)).grid(
    row=2, column=1, columnspan=3, sticky="ew", padx=8, pady=4
)
tk.Label(
    form,
    text="Format:  Math:85, English:78, Urdu:90",
    font=(FONT, 9),
    fg=MUTED,
    bg=CARD_BG,
).grid(row=3, column=1, columnspan=3, sticky="w", padx=8)
form.columnconfigure(3, weight=1)

# ----- Buttons -----
controls = make_card(root)
controls.pack(fill="x", padx=20, pady=(0, 10))

row1 = tk.Frame(controls, bg=CARD_BG)
row1.pack(fill="x")
add_buttons(row1, [
    ("Add", add_student, "Green"),
    ("Sheet Entry", open_sheet, "Orange"),
    ("Update", update_student, "Blue"),
    ("Delete", delete_student, "Red"),
    ("Clear", clear_fields, "Gray"),
])
# Import and Export buttons sit on the right side of the first row
file_group = tk.Frame(row1, bg=CARD_BG)
file_group.pack(side="right")
add_buttons(file_group, [
    ("Import CSV", import_csv, "Teal"),
    ("Export CSV", export_csv, "Teal"),
])

row2 = tk.Frame(controls, bg=CARD_BG)
row2.pack(fill="x", pady=(8, 0))
add_buttons(row2, [
    ("Search", search_student, "Blue"),
    ("Show All", refresh, "Gray"),
    ("Show Topper", show_topper, "Orange"),
    ("Show Failed", show_failed, "Red"),
    ("Show Ranking", show_ranking, "Purple"),
])

# ----- Table: shows the list of students -----
table_frame = tk.Frame(root, bg=BG)
table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

columns = ("roll", "name", "subjects", "total", "percentage", "grade", "status")
table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings",
    style="Table.Treeview",
    selectmode="browse",
)
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
table.configure(yscrollcommand=scrollbar.set)

# (heading text, width, text alignment, can stretch)
column_info = {
    "roll": ("Roll No", 80, "center", False),
    "name": ("Name", 170, "w", True),
    "subjects": ("Subjects", 320, "w", True),
    "total": ("Total", 80, "center", False),
    "percentage": ("Percentage", 100, "center", False),
    "grade": ("Grade", 70, "center", False),
    "status": ("Status", 80, "center", False),
}
for col, (heading, width, align, stretch) in column_info.items():
    table.heading(col, text=heading, anchor=align)
    table.column(col, width=width, anchor=align, stretch=stretch)

# Row colors
table.tag_configure("odd", background=ROW_ODD[0], foreground=ROW_ODD[1])
table.tag_configure("even", background=ROW_EVEN[0], foreground=ROW_EVEN[1])
table.tag_configure("fail", background=ROW_FAIL[0], foreground=ROW_FAIL[1])
table.tag_configure("selected", background=ROW_SELECTED[0], foreground=ROW_SELECTED[1])

scrollbar.pack(side="right", fill="y")
table.pack(side="left", fill="both", expand=True)

# Call on_select whenever the user clicks a row
table.bind("<<TreeviewSelect>>", on_select)

# Show all students when the window opens, then keep the window running
refresh()
root.mainloop()