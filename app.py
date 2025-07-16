# app.py

from flask import Flask, render_template, request, redirect, url_for, make_response
import sqlite3, os
from datetime import date
from fpdf import FPDF
from datetime import datetime
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
import io

auth = HTTPBasicAuth()

# Nastavení uživatele a hesla
users = {
    "ulov": generate_password_hash("tajneheslo123")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

app = Flask(__name__)
DB_NAME = os.path.join(os.path.dirname(__file__), "projektmanager.db")


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    conn = get_db_connection()
    projects = conn.execute("SELECT * FROM projects").fetchall()
    conn.close()
    return render_template("index.html", projects=projects)

@app.route("/new", methods=["GET", "POST"])
def new_project():
    if request.method == "POST":
        data = request.form
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO projects (
                name, contact_person, contact_email, tech_email, website,
                nickname, password, hourly_rate, external_expenses,
                discount_percent, discount_amount, comment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'], data['contact_person'], data['contact_email'],
            data['tech_email'], data['website'], data['nickname'],
            data['password'], data['hourly_rate'], data['external_expenses'],
            data['discount_percent'], data['discount_amount'], data['comment']
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("new.html")




@app.route("/project/<int:project_id>")
def project_detail(project_id):
    conn = get_db_connection()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    worklogs = conn.execute("SELECT * FROM worklogs WHERE project_id = ? ORDER BY work_date DESC", (project_id,)).fetchall()
    
    # Výpočet
    total_hours = sum([w['hours'] for w in worklogs])
    base_price = total_hours * project['hourly_rate']
    price_after_pct = base_price * (1 - (project['discount_percent'] or 0) / 100)
    total_price = price_after_pct - (project['discount_amount'] or 0) + (project['external_expenses'] or 0)
    
    conn.close()
    
    return render_template("detail.html", project=project, worklogs=worklogs, total_hours=total_hours,
                           base_price=base_price, total_price=total_price)

@app.route("/project/<int:project_id>/add-log", methods=["POST"])
def add_worklog(project_id):
    work_date = request.form["work_date"]
    hours = float(request.form["hours"])
    note = request.form.get("note", "")
    
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO worklogs (project_id, work_date, hours, note) VALUES (?, ?, ?, ?)",
        (project_id, work_date, hours, note)
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for("project_detail", project_id=project_id))



@app.route("/project/<int:project_id>/export")
@auth.login_required
def export_project_pdf(project_id):
    conn = get_db_connection()

    # Načtení dat
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    worklogs = conn.execute("SELECT * FROM worklogs WHERE project_id = ? ORDER BY work_date ASC", (project_id,)).fetchall()

    total_hours = sum([w["hours"] for w in worklogs])
    base_price = total_hours * project["hourly_rate"]
    price_after_pct = base_price * (1 - (project["discount_percent"] or 0) / 100)
    final_price = price_after_pct - (project["discount_amount"] or 0) + (project["external_expenses"] or 0)

    # PDF generace
    pdf = FPDF()
    pdf.add_page()
    pdf.image("static/logo_ulovsalon.png", x=160, y=10, w=35)
    pdf.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf', uni=True)            # normální
    pdf.add_font('DejaVu', 'B', 'fonts/DejaVuSans-Bold.ttf', uni=True)      # tučný
    pdf.set_font("DejaVu", '', 12)

    today = datetime.today().strftime('%d.%m.%Y')

    # Hlavička vystavitele
    pdf.cell(0, 10, "Faktura / Výkaz práce", ln=True)
    pdf.cell(0, 10, f"Vystavil: UlovSalon.cz – Jiří Hakl", ln=True)
    pdf.cell(0, 10, f"IČO: čekáme na něj", ln=True)
    pdf.cell(0, 10, f"Sídlo: Aubrechtové 3110/8", ln=True)
    pdf.cell(0, 10, f"Telefon: 797 756 746", ln=True)
    pdf.cell(0, 10, f"E-mail: hakl@salon.cz", ln=True)
    pdf.ln(5)

    # Klient
    pdf.set_font("DejaVu", '', 12)
    pdf.cell(0, 10, f"Pro: {project['contact_person'] or 'Neznámý kontakt'}", ln=True)
    pdf.cell(0, 10, f"E-mail klienta: {project['contact_email'] or 'neuveden'}", ln=True)
    pdf.cell(0, 10, f"Aktuální stav k: {today}", ln=True)
    pdf.ln(5)

    # Tabulka záznamů
    pdf.set_font("DejaVu", 'B', 12)
    pdf.cell(40, 10, "Datum", 1)
    pdf.cell(30, 10, "Hodiny", 1)
    pdf.cell(120, 10, "Poznámka", 1, ln=True)
    pdf.set_font("DejaVu", '', 12)
    for w in worklogs:
        pdf.cell(40, 10, w["work_date"], 1)
        pdf.cell(30, 10, f"{w['hours']:.2f}", 1)
        pdf.multi_cell(115, 10, f"{w['work_date']}   {w['hours']:.2f} h   {w['note'] or ''}", border=1)

    # Výpočty
    pdf.ln(5)
    pdf.set_font("DejaVu", 'B', 12)
    pdf.cell(0, 10, "Výpočet ceny:", ln=True)
    pdf.set_font("DejaVu", '', 12)
    pdf.cell(0, 10, f"Celkový počet hodin: {total_hours} h", ln=True)
    pdf.cell(0, 10, f"Sazba za hodinu: {project['hourly_rate']} Kč", ln=True)
    pdf.cell(0, 10, f"Základní cena: {base_price:.2f} Kč (hodiny × sazba)", ln=True)
    pdf.cell(0, 10, f"Sleva %: -{project['discount_percent']} % → −{base_price - price_after_pct:.2f} Kč", ln=True)
    pdf.cell(0, 10, f"Sleva Kč: −{project['discount_amount']} Kč", ln=True)
    pdf.cell(0, 10, f"Externí výdaje: +{project['external_expenses']} Kč", ln=True)
    pdf.set_font("DejaVu", 'B', 12)
    pdf.cell(0, 10, f"Celková cena pro klienta: {final_price:.2f} Kč", ln=True)

    # Odeslání jako PDF přímo do prohlížeče
    pdf_output = pdf.output(dest='S').encode('latin1')

    response = make_response(pdf_output)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=faktura_{project_id}.pdf'
    return response

@app.route("/project/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):
    conn = get_db_connection()

    if request.method == "POST":
        data = request.form
        conn.execute('''
            UPDATE projects SET
                name = ?, contact_person = ?, contact_email = ?, tech_email = ?,
                website = ?, nickname = ?, password = ?, hourly_rate = ?,
                external_expenses = ?, discount_percent = ?, discount_amount = ?, comment = ?
            WHERE id = ?
        ''', (
            data['name'], data['contact_person'], data['contact_email'], data['tech_email'],
            data['website'], data['nickname'], data['password'], data['hourly_rate'],
            data['external_expenses'], data['discount_percent'], data['discount_amount'],
            data['comment'], project_id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("project_detail", project_id=project_id))

    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    worklogs = conn.execute(
        "SELECT * FROM worklogs WHERE project_id = ? ORDER BY work_date DESC", (project_id,)
    ).fetchall()
    conn.close()

    return render_template("edit.html", project=project, worklogs=worklogs)

@app.route("/worklog/<int:worklog_id>/edit", methods=["GET", "POST"])
def edit_worklog(worklog_id):
    conn = get_db_connection()

    if request.method == "POST":
        work_date = request.form["work_date"]
        hours = float(request.form["hours"])
        note = request.form.get("note", "")
        conn.execute("UPDATE worklogs SET work_date = ?, hours = ?, note = ? WHERE id = ?",
                     (work_date, hours, note, worklog_id))
        conn.commit()
        # Získat ID projektu pro přesměrování
        project_id = conn.execute("SELECT project_id FROM worklogs WHERE id = ?", (worklog_id,)).fetchone()["project_id"]
        conn.close()
        return redirect(url_for("edit_project", project_id=project_id))

    log = conn.execute("SELECT * FROM worklogs WHERE id = ?", (worklog_id,)).fetchone()
    conn.close()
    return render_template("edit_worklog.html", log=log)



@app.route("/worklog/<int:worklog_id>/delete")
def delete_worklog(worklog_id):
    conn = get_db_connection()
    project_id = conn.execute("SELECT project_id FROM worklogs WHERE id = ?", (worklog_id,)).fetchone()["project_id"]
    conn.execute("DELETE FROM worklogs WHERE id = ?", (worklog_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("edit_project", project_id=project_id))


@app.before_request
@auth.login_required
def require_login():
    pass

if __name__ == "__main__":
    app.run(debug=True)
