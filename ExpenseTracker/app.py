import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

DB = os.path.join(os.path.dirname(__file__), 'expense_tracker.db')

app = Flask(__name__)
app.secret_key = 'Neeraj_Kumar_18'

# --- Database helpers ---

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# --- Authentication routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        username = request.form['username'].strip().lower()
        password = request.form['password']
        if not (name and username and password):
            flash('Please fill all fields', 'error')
            return render_template('register.html')
        hashed = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name, username, password) VALUES (?, ?, ?)',
                         (name, username, hashed))
            conn.commit()
            conn.close()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username already exists', 'error')
            return render_template('register.html')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '')
            # Debug: show exact received values (repr) to detect hidden whitespace/case
            print(f"[DEBUG] login received username: {repr(username)}")
            print(f"[DEBUG] login received password: {repr(password)}")
            
            if not username or not password:
                flash('Please enter both username and password', 'error')
                return render_template('login.html')
                
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if user:
                if check_password_hash(user['password'], password):
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['name'] = user['name']
                    conn.close()
                    flash('Welcome back, ' + user['name'] + '!', 'success')
                    return redirect(url_for('index'))
            
            conn.close()
            flash('Invalid username or password', 'error')
            return render_template('login.html')
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Main app routes ---

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped

@app.route('/')
@login_required
def index():
    # Ensure user is logged in (login_required decorator covers this)
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip()
    try:
        conn = get_db_connection()
        if q:
            expenses = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? AND description LIKE ? ORDER BY date DESC LIMIT 20",
                (user_id, f'%{q}%')
            ).fetchall()
        else:
            expenses = conn.execute(
                'SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 20',
                (user_id,)
            ).fetchall()

        # Compute total spent for this user
        total_row = conn.execute('SELECT IFNULL(SUM(amount), 0) as total FROM expenses WHERE user_id = ?', (user_id,)).fetchone()
        total = total_row['total'] if total_row is not None else 0
        conn.close()
        return render_template('index.html', expenses=expenses, total=total, query=q)
    except Exception as e:
        print(f"Index error: {str(e)}")
        flash('An error occurred while loading expenses', 'error')
        # On error return empty list and total 0
        return render_template('index.html', expenses=[], total=0, query=q)

@app.route('/add', methods=['POST'])
@login_required
def add_expense():
    description = request.form['description'].strip()
    date = request.form['date']
    category = request.form['category']
    amount = request.form['amount']
    if not (description and date and category and amount):
        flash('Please fill all fields', 'error')
        return redirect(url_for('index'))
    try:
        amount_value = float(amount)
    except ValueError:
        flash('Invalid amount', 'error')
        return redirect(url_for('index'))
    conn = get_db_connection()
    conn.execute('INSERT INTO expenses (user_id, description, date, category, amount) VALUES (?, ?, ?, ?, ?)',
                 (session['user_id'], description, date, category, amount_value))
    conn.commit()
    conn.close()
    flash('Expense added', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', (expense_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Deleted', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<int:expense_id>', methods=['GET','POST'])
@login_required
def edit_expense(expense_id):
    conn = get_db_connection()
    expense = conn.execute('SELECT * FROM expenses WHERE id = ? AND user_id = ?', (expense_id, session['user_id'])).fetchone()
    if not expense:
        conn.close()
        flash('Expense not found', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        description = request.form['description'].strip()
        date = request.form['date']
        category = request.form['category']
        amount = request.form['amount']
        try:
            amount_value = float(amount)
        except ValueError:
            flash('Invalid amount', 'error')
            return redirect(url_for('edit_expense', expense_id=expense_id))
        conn.execute('UPDATE expenses SET description=?, date=?, category=?, amount=? WHERE id=?',
                     (description, date, category, amount_value, expense_id))
        conn.commit()
        conn.close()
        flash('Updated', 'success')
        return redirect(url_for('index'))
    conn.close()
    return render_template('edit.html', expense=expense)

@app.route('/export_pdf')
@login_required
def export_pdf():
    # Gather expenses
    conn = get_db_connection()
    user_id = session['user_id']
    expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date ASC', (user_id,)).fetchall()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    left_margin = 50
    right_margin = 50
    x = left_margin
    y = height - 50

    # Header
    p.setFont('Helvetica-Bold', 18)
    p.drawString(x, y, 'Expense Tracker Report')
    p.setFont('Helvetica', 10)
    y -= 22
    if user:
        p.drawString(x, y, f'User: {user["name"]} ({user["username"]})')
    else:
        p.drawString(x, y, 'User: (unknown)')
    y -= 16

    # Summary: total count and date range
    total_expenses = len(expenses)
    total_amount = sum([e['amount'] for e in expenses]) if expenses else 0
    date_from = expenses[0]['date'] if expenses else ''
    date_to = expenses[-1]['date'] if expenses else ''
    p.drawString(x, y, f'Total records: {total_expenses}    Total amount: ₹ {total_amount:.2f}')
    y -= 16
    if date_from and date_to:
        p.drawString(x, y, f'Date range: {date_from}  to  {date_to}')
        y -= 18

    # Table header
    p.setFont('Helvetica-Bold', 11)
    col_date = x
    col_cat = x + 90
    col_desc = x + 190
    col_amount = x + 430
    p.drawString(col_date, y, 'Date')
    p.drawString(col_cat, y, 'Category')
    p.drawString(col_desc, y, 'Description')
    p.drawString(col_amount, y, 'Amount (₹)')
    y -= 14
    p.setFont('Helvetica', 10)
    p.line(left_margin, y + 6, width - right_margin, y + 6)
    y -= 6

    # Rows
    for exp in expenses:
        if y < 80:
            p.showPage()
            y = height - 50
            # re-draw header on new page
            p.setFont('Helvetica-Bold', 11)
            p.drawString(col_date, y, 'Date')
            p.drawString(col_cat, y, 'Category')
            p.drawString(col_desc, y, 'Description')
            p.drawString(col_amount, y, 'Amount (₹)')
            y -= 16
            p.setFont('Helvetica', 10)
            p.line(left_margin, y + 6, width - right_margin, y + 6)
            y -= 6

        date_text = exp['date']
        cat_text = exp['category']
        desc_text = (exp['description'][:60] + '...') if len(exp['description']) > 60 else exp['description']
        amt_text = f"{exp['amount']:.2f}"

        p.drawString(col_date, y, date_text)
        p.drawString(col_cat, y, cat_text)
        p.drawString(col_desc, y, desc_text)
        p.drawRightString(col_amount + 60, y, amt_text)
        y -= 14

    # Footer summary
    if y < 120:
        p.showPage()
        y = height - 50

    y -= 10
    p.setFont('Helvetica-Bold', 12)
    p.drawString(x, y, f'Total Amount: ₹ {total_amount:.2f}')
    y -= 18
    if date_from and date_to:
        p.setFont('Helvetica', 10)
        p.drawString(x, y, f'Date range: {date_from}  —  {date_to}')

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='expenses_report.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    # auto-init DB if not present
    if not os.path.exists(DB):
        print('DB not found, creating...')
        import init_db
        init_db
    app.run(debug=True)
