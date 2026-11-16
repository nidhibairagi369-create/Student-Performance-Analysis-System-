
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3

app = Flask(__name__)
app.secret_key = "student-portal-change-this-key"
DB = "students.db"


# ---------------- DATABASE ----------------

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS students (
                roll TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                maths REAL NOT NULL,
                python REAL NOT NULL,
                english REAL NOT NULL,
                attendance REAL NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS grievances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'Pending'
            )
        """)

        count = con.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

        if count == 0:
            con.execute(
                "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("201", "Demo Student", 85, 90, 82, 88,
                 "student201", "student123")
            )


# ---------------- LOGIN SECURITY ----------------

def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))

            if role and session.get("role") != role:
                flash("You are not authorised to access that page.")
                return redirect(url_for("dashboard"))

            return func(*args, **kwargs)
        return wrapper
    return decorator


# ---------------- HELPER FUNCTION ----------------

def get_records(roll=None):
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row

        if roll is None:
            students = con.execute(
                "SELECT * FROM students ORDER BY roll"
            ).fetchall()
        else:
            students = con.execute(
                "SELECT * FROM students WHERE roll=?",
                (roll,)
            ).fetchall()

    records = []

    for s in students:
        percentage = (
            s["maths"] + s["python"] + s["english"]
        ) / 3

        records.append({
            "roll": s["roll"],
            "name": s["name"],
            "maths": s["maths"],
            "python": s["python"],
            "english": s["english"],
            "attendance": s["attendance"],
            "percentage": round(percentage, 2),
            "grade": (
                "A" if percentage >= 80 else
                "B" if percentage >= 60 else
                "C" if percentage >= 40 else "F"
            ),
            "status": (
                "Pass" if min(
                    s["maths"], s["python"], s["english"]
                ) >= 33 else "Fail"
            )
        })

    return records


def get_grievances():
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row

        if session["role"] == "admin":
            return con.execute(
                "SELECT * FROM grievances ORDER BY id DESC"
            ).fetchall()

        return con.execute(
            """SELECT * FROM grievances
               WHERE username=? ORDER BY id DESC""",
            (session["user"],)
        ).fetchall()


def calculate_stats(records):
    average = round(
        sum(r["percentage"] for r in records) / len(records), 2
    ) if records else 0

    pass_rate = round(
        sum(r["status"] == "Pass" for r in records)
        * 100 / len(records), 1
    ) if records else 0

    low_attendance = sum(
        r["attendance"] < 75 for r in records
    )

    return average, pass_rate, low_attendance


# ---------------- DAA ALGORITHMS ----------------

# 1. MERGE SORT
# Sort students by percentage in descending order.

def merge_sort(records):
    if len(records) <= 1:
        return records

    mid = len(records) // 2

    left = merge_sort(records[:mid])
    right = merge_sort(records[mid:])

    return merge(left, right)


def merge(left, right):
    result = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if left[i]["percentage"] >= right[j]["percentage"]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])

    return result


# 2. BINARY SEARCH
# Search a student using roll number.
# Records must be sorted by roll number first.

def binary_search(records, target):
    low = 0
    high = len(records) - 1

    while low <= high:
        mid = (low + high) // 2
        current_roll = records[mid]["roll"]

        if current_roll == target:
            return records[mid]

        elif current_roll < target:
            low = mid + 1

        else:
            high = mid - 1

    return None


# 3. LINEAR SEARCH
# Find students whose percentage is below 60.

def linear_search_low_performers(records):
    low_performers = []

    for student in records:
        if student["percentage"] < 60:
            low_performers.append(student)

    return low_performers


# ---------------- HOME AND LOGIN ----------------

@app.route("/")
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/login/<role>", methods=["GET", "POST"])
def role_login(role):
    if role not in ("admin", "student"):
        return redirect(url_for("login"))

    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if role == "admin":
            if username == "admin" and password == "admin123":
                session.clear()
                session["user"] = "admin"
                session["role"] = "admin"
                session["name"] = "Administrator"
                return redirect(url_for("dashboard"))

            flash("Invalid staff/admin credentials.")

        else:
            with sqlite3.connect(DB) as con:
                student = con.execute(
                    """SELECT roll, name FROM students
                       WHERE username=? AND password=?""",
                    (username, password)
                ).fetchone()

            if student:
                session.clear()
                session["user"] = username
                session["role"] = "student"
                session["roll"] = student[0]
                session["name"] = student[1]
                return redirect(url_for("dashboard"))

            flash("Invalid student credentials.")

    return render_template("role_login.html", role=role)


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
@login_required()
def dashboard():
    if session["role"] == "admin":
        records = get_records()
    else:
        records = get_records(session["roll"])

    grievances = get_grievances()
    average, pass_rate, low_attendance = calculate_stats(records)

    return render_template(
        "dashboard.html",
        records=records,
        average=average,
        pass_rate=pass_rate,
        low_attendance=low_attendance,
        grievances=grievances,
        role=session["role"],
        name=session.get("name", "Administrator")
    )


# ---------------- ADD STUDENT ----------------

@app.route("/add", methods=["POST"])
@login_required("admin")
def add_student():
    data = [
        request.form.get("roll", "").strip(),
        request.form.get("name", "").strip(),
        request.form.get("maths", ""),
        request.form.get("python", ""),
        request.form.get("english", ""),
        request.form.get("attendance", ""),
        request.form.get("username", "").strip(),
        request.form.get("password", "")
    ]

    try:
        if not all(data):
            raise ValueError("Please fill in every field.")

        marks = [float(data[i]) for i in (2, 3, 4, 5)]

        if any(x < 0 or x > 100 for x in marks):
            raise ValueError(
                "Marks and attendance must be from 0 to 100."
            )

        with sqlite3.connect(DB) as con:
            con.execute(
                "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (data[0], data[1], *marks, data[6], data[7])
            )

        flash("Student added successfully.")

    except ValueError as e:
        flash(str(e) or "Enter valid numeric values.")

    except sqlite3.IntegrityError:
        flash("Roll number or username already exists.")

    return redirect(url_for("dashboard"))


# ---------------- DELETE STUDENT ----------------

@app.route("/delete/<roll>", methods=["POST"])
@login_required("admin")
def delete_student(roll):
    with sqlite3.connect(DB) as con:
        con.execute(
            "DELETE FROM students WHERE roll=?",
            (roll,)
        )

    flash("Student record deleted.")
    return redirect(url_for("dashboard"))


# ---------------- EDIT STUDENT ----------------

@app.route("/edit/<roll>", methods=["GET", "POST"])
@login_required("admin")
def edit_student(roll):
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row

        student = con.execute(
            "SELECT * FROM students WHERE roll=?",
            (roll,)
        ).fetchone()

        if student is None:
            flash("Student record not found.")
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()

            try:
                if not name:
                    raise ValueError("Student name is required.")

                marks = [
                    float(request.form.get("maths", "")),
                    float(request.form.get("python", "")),
                    float(request.form.get("english", "")),
                    float(request.form.get("attendance", ""))
                ]

                if any(x < 0 or x > 100 for x in marks):
                    raise ValueError(
                        "Marks and attendance must be from 0 to 100."
                    )

                con.execute(
                    """UPDATE students
                       SET name=?, maths=?, python=?,
                           english=?, attendance=?
                       WHERE roll=?""",
                    (name, *marks, roll)
                )

                flash("Student record updated successfully.")
                return redirect(url_for("dashboard"))

            except ValueError as e:
                flash(str(e) or "Please enter valid numbers.")

    return render_template("edit_student.html", student=student)


# ---------------- GRIEVANCES ----------------

@app.route("/grievance", methods=["POST"])
@login_required()
def grievance():
    message = request.form.get("message", "").strip()

    if message:
        with sqlite3.connect(DB) as con:
            con.execute(
                """INSERT INTO grievances(username, message)
                   VALUES (?, ?)""",
                (session["user"], message)
            )

        flash("Your request has been submitted.")
    else:
        flash("Please enter your request.")

    return redirect(url_for("dashboard"))


@app.route("/resolve/<int:gid>", methods=["POST"])
@login_required("admin")
def resolve(gid):
    with sqlite3.connect(DB) as con:
        con.execute(
            "UPDATE grievances SET status='Resolved' WHERE id=?",
            (gid,)
        )

    flash("Request marked as resolved.")
    return redirect(url_for("dashboard"))


# ---------------- DAA PAGE ----------------

@app.route("/daa", methods=["GET", "POST"])
@login_required("admin")
def daa_page():
    records = get_records()

    # Merge Sort: rank students by percentage.
    ranked_records = merge_sort(records.copy())

    # Linear Search: find students below 60%.
    low_performers = linear_search_low_performers(records)

    search_result = None
    searched_roll = ""

    # Binary Search: search by roll number.
    if request.method == "POST":
        searched_roll = request.form.get("roll", "").strip()

        if searched_roll:
            # Binary Search requires sorted input.
            sorted_by_roll = sorted(
                records,
                key=lambda student: student["roll"]
            )

            search_result = binary_search(
                sorted_by_roll,
                searched_roll
            )

            if search_result is None:
                flash("No student found with this roll number.")
        else:
            flash("Please enter a roll number.")

    return render_template(
        "daa.html",
        ranked_records=ranked_records,
        low_performers=low_performers,
        search_result=search_result,
        searched_roll=searched_roll
    )


# ---------------- OTHER PAGES AND ANALYTICS ----------------

@app.route("/page/<page>")
@login_required()
def portal_page(page):
    allowed_pages = ["students", "analytics", "help"]

    if page not in allowed_pages:
        return redirect(url_for("dashboard"))

    role = session["role"]

    if role != "admin" and page == "students":
        page = "performance"

    if role == "admin":
        records = get_records()
    else:
        records = get_records(session["roll"])

    grievances = get_grievances()
    average, pass_rate, low_attendance = calculate_stats(records)

    if page == "analytics":
        return render_template(
            "analytics.html",
            records=records
        )

    return render_template(
        "page.html",
        page=page,
        role=role,
        records=records,
        average=average,
        pass_rate=pass_rate,
        low_attendance=low_attendance,
        grievances=grievances
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)