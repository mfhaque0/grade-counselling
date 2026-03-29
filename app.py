from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

from modules.colleges import get_all_colleges, get_college_by_id


app = Flask(__name__)
app.secret_key = "engineering_portal_secure_key"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "faizan"

# -------------------------------
# ADMIN LOGIN
# -------------------------------

@app.route("/admin", methods=["GET","POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")

        else:
            return render_template("admin.html", error="Invalid login")

    return render_template("admin.html")

# -------------------------------
# ADMIN DASHBOARD
# -------------------------------

@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()

    colleges = conn.execute(
        "SELECT * FROM colleges ORDER BY id DESC"
    ).fetchall()

    counselling = conn.execute(
        "SELECT * FROM counselling"
    ).fetchall()

    news = conn.execute(
        "SELECT * FROM news ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        colleges=colleges,
        counselling=counselling,
        news=news
    )

# -------------------------------
# ADMIN LOGOUT
# -------------------------------

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect("/")

# -------------------------------
# IMAGE UPLOAD CONFIG
# -------------------------------

UPLOAD_FOLDER = "static/images/colleges"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# -------------------------------
# DATABASE CONNECTION
# -------------------------------

def get_db_connection():
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "database", "colleges.db")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------
# HOME PAGE
# -------------------------------

@app.route("/")
def home():

    conn = get_db_connection()

    news = conn.execute(
        "SELECT * FROM news ORDER BY id DESC LIMIT 3"
    ).fetchall()

    counselling = conn.execute("""
    SELECT c.id, c.name, c.slug,
           COUNT(col.id) AS college_count
    FROM counselling c
    LEFT JOIN colleges col
    ON col.counselling_id = c.id
    GROUP BY c.id
    ORDER BY college_count DESC
""").fetchall()

    conn.close()

    colleges = get_all_colleges(limit=3)

    return render_template(
        "home.html",
        colleges=colleges,
        news=news,
        counselling=counselling   
    )


# -------------------------------
# EXAMS PAGE
# -------------------------------

@app.route("/entrance-exams")
def exams():

    conn = get_db_connection()

    exams = conn.execute(
        "SELECT * FROM exams"
    ).fetchall()

    conn.close()

    return render_template(
        "exam.html",
        exams=exams
    )


# -------------------------------
# EXAM DETAIL
# -------------------------------

@app.route("/entrance-exams/<slug>")
def exam_detail(slug):

    conn = get_db_connection()

    exam = conn.execute(
        "SELECT * FROM exams WHERE slug=?",
        (slug,)
    ).fetchone()

    conn.close()

    if not exam:
        return "Exam not found", 404

    return render_template(
        "exam_detail.html",
        exam=exam
    )


# -------------------------------
# COUNSELLING LIST
# -------------------------------

@app.route("/counselling")
def counselling_page():

    conn = get_db_connection()

    portals = conn.execute("""
        SELECT c.id, c.name, c.slug,
               COUNT(col.id) AS college_count
        FROM counselling c
        LEFT JOIN colleges col
        ON col.counselling_id = c.id
        GROUP BY c.id
        ORDER BY college_count DESC
    """).fetchall()

    conn.close()

    return render_template(
        "counselling.html",
        portals=portals
    )


# -------------------------------
# COUNSELLING COLLEGES
# -------------------------------
@app.route("/admin/edit-counselling/<int:id>", methods=["GET","POST"])
def edit_counselling(id):

    if not session.get("admin_logged_in"):
        return redirect("/admin")

    conn = get_db_connection()

    if request.method == "POST":

        conn.execute("""
            UPDATE counselling SET
            name=?, slug=?
            WHERE id=?
        """, (
            request.form["name"],
            request.form["slug"],
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/admin/dashboard")

    data = conn.execute(
        "SELECT * FROM counselling WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template("edit_counselling.html", c=data)



@app.route("/admin/add-counselling", methods=["POST"])
def add_counselling():

    if not session.get("admin_logged_in"):
        return redirect("/admin")

    name = request.form["name"]
    slug = request.form["slug"]

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO counselling (name, slug)
        VALUES (?, ?)
    """, (name, slug))

    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")


@app.route("/counselling/<slug>")
def counselling_detail(slug):

    conn = get_db_connection()

    colleges = conn.execute("""
        SELECT col.*
        FROM colleges col
        JOIN counselling c
        ON col.counselling_id = c.id
        WHERE c.slug = ?
    """, (slug,)).fetchall()

    conn.close()

    return render_template(
        "college.html",
        colleges=colleges,
        title=slug
    )


# -------------------------------
# ALL COLLEGES
# -------------------------------

@app.route("/colleges")
def all_colleges_list():

    colleges = get_all_colleges()

    return render_template(
        "college.html",
        colleges=colleges,
        title="All Engineering Colleges"
    )


# -------------------------------
# COLLEGE DETAIL
# -------------------------------

@app.route("/college/<int:id>")
def college_detail(id):

    college = get_college_by_id(id)

    if not college:
        return "College not found", 404

    return render_template(
        "college_detail.html",
        college=college
    )
 
# -------------------------------
# college finder
# -------------------------------
@app.route("/college-finder", methods=["GET", "POST"])
def finder():

    if request.method == "POST":

        exam = request.form["exam"]
        rank = request.form["rank"]
        counselling = request.form["counselling"]

        colleges = predict_colleges(rank, exam, counselling)

        return render_template(
            "finder.html",
            colleges=colleges,
            rank=rank
        )

    return render_template("finder.html")
# -------------------------------
# NEWS
# -------------------------------
@app.route("/admin/edit-news/<int:id>", methods=["GET","POST"])
def edit_news(id):

    if not session.get("admin_logged_in"):
        return redirect("/admin")

    conn = get_db_connection()

    if request.method == "POST":

        conn.execute("""
            UPDATE news SET
            title=?,
            summary=?,
            date=?,
            category=?
            WHERE id=?
        """, (
            request.form["title"],
            request.form["summary"],
            request.form["date"],
            request.form["category"],
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/admin/dashboard")

    article = conn.execute(
        "SELECT * FROM news WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template("edit_news.html", article=article)


@app.route("/admin/add-news", methods=["POST"])
def add_news():

    if not session.get("admin_logged_in"):
        return redirect("/admin")

    title = request.form["title"]
    summary = request.form["summary"]
    date = request.form["date"]

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO news (title, summary, date)
        VALUES (?, ?, ?)
    """, (title, summary, date))

    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")

@app.route("/news")
def news_page():

    conn = get_db_connection()

    articles = conn.execute(
        "SELECT * FROM news ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "news.html",
        articles=articles
    )


@app.route("/news/<int:id>")
def news_detail(id):

    conn = get_db_connection()

    article = conn.execute(
        "SELECT * FROM news WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    if not article:
        return "News article not found", 404

    return render_template(
        "news_detail.html",
        article=article
    )
# -------------------------------
# college predictor logic
# -------------------------------
def predict_colleges(rank, exam, counselling):

    rank = int(rank)

    conn = get_db_connection()

    query = "SELECT * FROM colleges WHERE closing_rank >= ?"
    params = [rank]

    if counselling:
        query += " AND counselling_id = (SELECT id FROM counselling WHERE name=?)"
        params.append(counselling)

    colleges = conn.execute(query, params).fetchall()
    conn.close()
    colleges = sorted(
        colleges,
        key=lambda x: int(x["closing_rank"])
    )

    return colleges

# -------------------------------
# ADMIN ADD COLLEGE (WITH IMAGE)
# -------------------------------
@app.route("/admin/edit-college/<int:id>", methods=["GET","POST"])
def edit_college(id):

    if not session.get("admin_logged_in"):
        return redirect("/admin")

    conn = get_db_connection()

    if request.method == "POST":

        conn.execute("""
            UPDATE colleges SET
            name=?,
            location=?,
            closing_rank=?,
            overview=?,
            facilities=?,
            airport=?,
            railway=?
            WHERE id=?
        """, (
            request.form["name"],
            request.form["location"],
            request.form["closing_rank"],
            request.form["overview"],
            request.form["facilities"],
            request.form["airport"],
            request.form["railway"],
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/admin/dashboard")

    college = conn.execute(
        "SELECT * FROM colleges WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template("edit_college.html", college=college)

@app.route("/admin/add-college", methods=["POST"])
def admin_add_college():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    name = request.form["name"]
    location = request.form["location"]
    closing_rank = request.form["closing_rank"]
    counselling_id = request.form["counselling_id"]

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO colleges (name, location, closing_rank, counselling_id)
        VALUES (?, ?, ?, ?)
    """, (name, location, closing_rank, counselling_id))

    college_id = cursor.lastrowid

    images = request.files.getlist("images")

    for image in images:

        if image.filename == "":
            continue

        filename = secure_filename(image.filename)

        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        image.save(image_path)

        conn.execute("""
            INSERT INTO college_images (college_id, image)
            VALUES (?, ?)
        """, (college_id, filename))

    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")

# -------------------------------
# DELETE COLLEGE (SAFE DELETE)
# -------------------------------

@app.route("/admin/delete-college/<int:id>")
def delete_college(id):

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_db_connection()

    images = conn.execute(
        "SELECT image FROM college_images WHERE college_id=?",
        (id,)
    ).fetchall()

    for img in images:

        path = os.path.join(app.config["UPLOAD_FOLDER"], img["image"])

        if os.path.exists(path):
            os.remove(path)

    conn.execute(
        "DELETE FROM college_images WHERE college_id=?",
        (id,)
    )

    conn.execute(
        "DELETE FROM colleges WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")



# -------------------------------
# PREDICTOR
# -------------------------------

@app.route("/predictor/marks", methods=["POST"])
def marks_to_percentile():

    marks = int(request.form["marks"])
    
    conn = get_db_connection()

    result = conn.execute("""
        SELECT percentile
        FROM jee_main_marks_percentile
        WHERE marks <= ?
ORDER BY marks DESC
LIMIT 1
    """, (marks,)).fetchone()

    conn.close()

    percentile = result["percentile"] if result else 0

    return render_template(
        "finder.html",
        marks=marks,
        percentile=percentile
    )

@app.route("/predictor/percentile", methods=["POST"])
def percentile_to_rank():

    percentile = float(request.form["percentile"])

    conn = get_db_connection()

    result = conn.execute("""
        SELECT rank
        FROM jee_main_percentile_rank
        ORDER BY ABS(percentile - ?) ASC
        LIMIT 1
    """, (percentile,)).fetchone()

    conn.close()

    rank = result["rank"] if result else 0

    return render_template(
        "finder.html",
        percentile=percentile,
        rank=rank
    )

