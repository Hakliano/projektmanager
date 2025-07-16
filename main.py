# main.py

from database import create_connection
from fpdf import FPDF


def add_project():
    conn = create_connection()
    cursor = conn.cursor()

    print("\n➕ Nový projekt")
    name = input("Název projektu: ")
    contact_person = input("Kontaktní osoba: ")
    contact_email = input("Kontaktní email: ")
    tech_email = input("Technický email: ")
    website = input("Web: ")
    nickname = input("Nick: ")
    password = input("Heslo (bude uloženo jako text): ")
    hourly_rate = float(input("Cena za hodinu (Kč): "))
    external_expenses = float(input("Externí výdaje (Kč): "))
    discount_percent = float(input("Sleva v %: "))
    discount_amount = float(input("Sleva v Kč: "))
    comment = input("Komentář: ")

    cursor.execute('''
        INSERT INTO projects 
        (name, contact_person, contact_email, tech_email, website, nickname, password,
         hourly_rate, external_expenses, discount_percent, discount_amount, comment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, contact_person, contact_email, tech_email, website, nickname, password,
          hourly_rate, external_expenses, discount_percent, discount_amount, comment))

    conn.commit()
    conn.close()
    print("✅ Projekt byl uložen.")

def list_projects():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM projects")
    projects = cursor.fetchall()
    conn.close()

    print("\n📋 Projekty:")
    for proj in projects:
        print(f"{proj[0]}. {proj[1]}")

def menu():
    while True:
        print("\n--- Projekt Manager ---")
        print("1. Přidat nový projekt")
        print("2. Vypsat projekty")
        print("3. Přidat záznam o odpracovaném dni")
        print("4. Spočítat celkovou cenu projektu")
        print("5. Exportovat projekt do PDF")
        print("0. Konec")

        choice = input("Zvolte akci: ")
        if choice == "1":
            add_project()
        elif choice == "2":
            list_projects()
        elif choice == "3":
            add_worklog()
        elif choice == "4":
            calculate_project_total()
        elif choice == "5":
            export_project_pdf()
        elif choice == "0":
            break
        else:
            print("Neplatná volba.")


def add_worklog():
    list_projects()
    try:
        project_id = int(input("Zadejte ID projektu: "))
        work_date = input("Datum (YYYY-MM-DD): ")
        hours = float(input("Počet hodin: "))
    except ValueError:
        print("❌ Neplatný vstup.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO worklogs (project_id, work_date, hours)
        VALUES (?, ?, ?)
    ''', (project_id, work_date, hours))

    conn.commit()
    conn.close()
    print("✅ Záznam o práci byl uložen.")

def calculate_project_total():
    list_projects()
    try:
        project_id = int(input("Zadejte ID projektu: "))
    except ValueError:
        print("❌ Neplatný vstup.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    # Načteme projekt
    cursor.execute("SELECT name, hourly_rate, external_expenses, discount_percent, discount_amount FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()

    if not project:
        print("❌ Projekt nenalezen.")
        conn.close()
        return

    name, rate, expenses, discount_pct, discount_abs = project

    # Součet hodin
    cursor.execute("SELECT SUM(hours) FROM worklogs WHERE project_id = ?", (project_id,))
    total_hours = cursor.fetchone()[0] or 0

    # Výpočet ceny
    base_price = total_hours * rate
    price_after_percent_discount = base_price * (1 - discount_pct / 100)
    total_price = price_after_percent_discount - discount_abs + expenses

    print(f"\n🧾 Shrnutí pro projekt: {name}")
    print(f"Celkem hodin: {total_hours}")
    print(f"Sazba: {rate:.2f} Kč/hod")
    print(f"Základní cena: {base_price:.2f} Kč")
    print(f"Sleva %: {discount_pct:.2f}% → {base_price - price_after_percent_discount:.2f} Kč")
    print(f"Sleva Kč: {discount_abs:.2f} Kč")
    print(f"Externí výdaje: {expenses:.2f} Kč")
    print(f"\n💰 **Celková cena pro klienta: {total_price:.2f} Kč**")

    conn.close()



def export_project_pdf():
    list_projects()
    try:
        project_id = int(input("Zadejte ID projektu: "))
    except ValueError:
        print("❌ Neplatný vstup.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT name, contact_person, contact_email, tech_email, website, nickname,
               password, hourly_rate, external_expenses, discount_percent,
               discount_amount, comment
        FROM projects WHERE id = ?
    ''', (project_id,))
    project = cursor.fetchone()

    if not project:
        print("❌ Projekt nenalezen.")
        return

    # Rozbalení dat projektu
    (name, contact_person, contact_email, tech_email, website, nickname,
     password, rate, expenses, discount_pct, discount_abs, comment) = project

    # Součet hodin
    cursor.execute("SELECT work_date, hours FROM worklogs WHERE project_id = ?", (project_id,))
    worklogs = cursor.fetchall()

    total_hours = sum([log[1] for log in worklogs])
    base_price = total_hours * rate
    price_after_percent_discount = base_price * (1 - discount_pct / 100)
    total_price = price_after_percent_discount - discount_abs + expenses

    # 🧾 PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_title(f"Report projektu: {name}")

    pdf.cell(0, 10, f"Projekt: {name}", ln=True)
    pdf.cell(0, 10, f"Kontaktní osoba: {contact_person}", ln=True)
    pdf.cell(0, 10, f"Kontaktní email: {contact_email}", ln=True)
    pdf.cell(0, 10, f"Technický email: {tech_email}", ln=True)
    pdf.cell(0, 10, f"Web: {website}", ln=True)
    pdf.cell(0, 10, f"Nick: {nickname}", ln=True)
    pdf.cell(0, 10, f"Heslo: {password}", ln=True)
    pdf.cell(0, 10, f"Komentář: {comment}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Záznamy práce:", ln=True)
    pdf.set_font("Arial", size=12)

    for date, hours in worklogs:
        pdf.cell(0, 10, f"{date}: {hours} hod.", ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, f"Celkem hodin: {total_hours}", ln=True)
    pdf.cell(0, 10, f"Sazba: {rate} Kč/hod", ln=True)
    pdf.cell(0, 10, f"Základní cena: {base_price:.2f} Kč", ln=True)
    pdf.cell(0, 10, f"Sleva %: {discount_pct}% ({base_price - price_after_percent_discount:.2f} Kč)", ln=True)
    pdf.cell(0, 10, f"Sleva Kč: {discount_abs} Kč", ln=True)
    pdf.cell(0, 10, f"Externí výdaje: {expenses} Kč", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Celková cena: {total_price:.2f} Kč", ln=True)

    # 🖨️ Uložit PDF
    filename = f"projekt_{project_id}_{name.replace(' ', '_')}.pdf"
    pdf.output(filename)
    print(f"✅ PDF export dokončen: {filename}")

    conn.close()

if __name__ == "__main__":
    menu()
