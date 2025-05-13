from flask import Flask, render_template, request, redirect, url_for
from flask import Flask, render_template_string
from cs50 import SQL
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)

DB_path = "transactions.db"

# Database setup
def init_db():
    conn =sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            trans_date TEXT -- format: 'YYYY-MM-DD' NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount FLOAT       
        )
    ''')
    conn.commit()
    conn.close()

# Get all transactions from the databse
def get_transactions():
    conn=sqlite3.connect(DB_path)
    conn.row_factory = sqlite3.Row
    cursor=conn.cursor()
    cursor.execute('SELECT * FROM transactions')
    transactions = cursor.fetchall()
    conn.close()
    return transactions

# Add transaction to the database
def add_transaction(trans_date, category, description, amount):
    conn=sqlite3.connect(DB_path)
    cursor=conn.cursor()
    cursor.execute('INSERT INTO transactions (trans_date, category, description, amount) VALUES (?, ?, ?, ?)',(trans_date, category, description, amount))
    conn.commit()
    conn.close()

# Update transaction's details
def update_transaction(id, trans_date, category, description, amount):
    conn=sqlite3.connect(DB_path)
    cursor=conn.cursor()
    cursor.execute('UPDATE transactions SET trans_date = ?, category = ?, description = ?, amount = ? WHERE id = ?',(trans_date, category, description, amount, id))
    conn.commit()
    conn.close()

# Delete a transaction by ID
def delete_transaction(id):
    conn=sqlite3.connect(DB_path)
    cursor=conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ?', (id,))
    conn.commit()
    conn.close()

# Home page to list transactions and show form to add a new transaction
@app.route('/', methods=['GET'])
def index():
    transactions = get_transactions()
    conn=sqlite3.connect(DB_path)
    cursor=conn.cursor()
    cursor.execute('SELECT SUM(amount) FROM transactions')
    total = cursor.fetchone()[0]
    conn.close()
    
    return render_template('index.html', total=total or 0,transactions=transactions)

# Add transaction via POST request
@app.route('/add_transaction', methods=['POST'])
def add_transaction_route():
    trans_date = request.form['trans_date']
    category = request.form['category']
    description = request.form['description']
    amount = request.form['amount']
    add_transaction(trans_date, category, description, amount)
    return redirect(url_for('index'))

# Update transaction via POST request
@app.route('/update_transaction/<int:id>', methods=['GET', 'POST'])
def update_transaction_route(id):
    if request.method == 'POST':    
        trans_date = request.form['trans_date']
        category = request.form['category']
        description = request.form['description']
        amount = request.form['amount']
        update_transaction(id, trans_date, category, description, amount)
        return redirect(url_for('index'))

    # Pre-fill form with current transaction data
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE id = ?',(id,))
    transactions = cursor.fetchone()
    conn.close()
    return render_template('update_transaction.html',transactions=transactions)

# Delete user via GET request
@app.route('/delete_transaction/<int:id>',methods=['GET'])
def delete_transaction_route(id):
    delete_transaction(id)
    return redirect(url_for('index'))

# Create Summary Route for transactions
@app.route('/summary')
def summary():
    conn = sqlite3.connect(DB_path)
    c = conn.cursor()
    c.execute('SELECT category, SUM(amount) FROM transactions GROUP BY category')
    rows = c.fetchall()
    conn.close()

    labels = [row[0] for row in rows]
    values = [round(row[1], 2) for row in rows]
    return render_template_string(html, labels=labels, values=values)

#HTML for Summary Chart
html = """    
<!doctype html>
<html>
<head>
    <title>Summary Pie Chart</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 2em;
        }
        .chart-container {
            position: relative;
            width: 100%;
            max-width: 600px;
            margin: auto;
        }
        canvas {
            width: 100% !important;
            height: auto !important;
        }
    </style>
</head>
<body>
    <h1>Amounts by Category (Pie Chart)</h1>
    <div class="chart-container">
        <canvas id="pieChart"></canvas>
    </div>
    <p><a href="/">Back to Home</a></p>
    <script>
        const ctx = document.getElementById('pieChart').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: {{ labels | tojson }},
                datasets: [{
                    label: 'Amount by Category',
                    data: {{ values | tojson }},
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                        '#9966FF', '#FF9F40', '#C9CBCF'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: 'Spending by Category'
                    }
                }
            }
        });
    </script>
</body>
</html>
    """

# Create Filter Route for transactions
@app.route('/filter', methods=['GET'])
def filter_transactions():
    # Get the filter type from query params
    filter_type = request.args.get('filter', 'daily')

    conn = sqlite3.connect(DB_path)
    c = conn.cursor()

    today = datetime.today()
    if filter_type == 'daily':
        date_str = today.strftime('%Y-%m-%d')
        c.execute("SELECT * FROM transactions WHERE trans_date = ?", (date_str,))
    elif filter_type == 'weekly':
        start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        c.execute("SELECT * FROM transactions WHERE trans_date BETWEEN ? AND ?", (start_date, end_date))
    elif filter_type == 'monthly':
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        c.execute("SELECT * FROM transactions WHERE trans_date BETWEEN ? AND ?", (start_date, end_date))
    else:
        c.execute("SELECT * FROM transactions")

    rows = c.fetchall()
    conn.close()

    html = """
    <!doctype html>
    <html>
    <head>
        <title>Filtered Transactions</title>
        <style>
            body { font-family: Arial; padding: 2em; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Filter Transactions</h1>
        <form method="get">
            <label for="filter">Filter by:</label>
            <select name="filter" id="filter">
                <option value="daily" {% if filter_type == 'daily' %}selected{% endif %}>Daily</option>
                <option value="weekly" {% if filter_type == 'weekly' %}selected{% endif %}>Weekly</option>
                <option value="monthly" {% if filter_type == 'monthly' %}selected{% endif %}>Monthly</option>
            </select>
            <button type="submit">Apply</button>
        </form>

        <h2>Results ({{ filter_type.capitalize() }})</h2>
        <table>
            <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Description</th>
                <th>Amount</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row[1] }}</td>
                <td>{{ row[2] }}</td>
                <td>{{ row[3] }}</td>
                <td>${{ "%.2f"|format(row[4]) }}</td>
                
            </tr>
            {% endfor %}
        </table>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """

    return render_template_string(html, rows=rows, filter_type=filter_type)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)