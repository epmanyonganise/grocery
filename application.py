from flask import Flask, render_template, request, jsonify
import mysql.connector
from datetime import datetime
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL Database Configuration
app.config['MYSQL_HOST'] = 'localhost'  # or your MySQL server IP
app.config['MYSQL_USER'] = 'root'  # your MySQL username
app.config['MYSQL_PASSWORD'] = ''  # your MySQL password
app.config['MYSQL_DB'] = 'grocery_shop'

mysql = MySQL(app)

# Route to add a new grocery item
@app.route('/api/add_item', methods=['POST'])
def add_item():
    try:
        # Get JSON data from the request
        data = request.get_json()
        print("Received data:", data)  # Debugging: Print the received data
        
        # Ensure all required fields are present
        if not data.get('name') or not data.get('category') or not data.get('price') or not data.get('quantity'):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Insert the new item into the database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO grocery_items (name, category, price, quantity) VALUES (%s, %s, %s, %s)", 
                    (data['name'], data['category'], data['price'], data['quantity']))
        mysql.connection.commit()
        cur.close()
        
        print("Item added successfully!")  # Debugging: Confirm success
        return jsonify({"message": "Item added successfully!"}), 201
    
    except mysql.connector.Error as err:
        # Handle MySQL errors
        print(f"MySQL Error: {err}")  # Print MySQL error
        return jsonify({"error": f"MySQL Error: {err}"}), 500
    except Exception as e:
        # Handle general errors
        print(f"Error: {e}")  # Print general error
        return jsonify({"error": "Internal server error"}), 500


# Route to get all grocery items
@app.route('/api/items', methods=['GET'])
def get_items():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM grocery_items")
        items = cur.fetchall()
        cur.close()
        
        return jsonify([{
            "id": item[0],
            "name": item[1],
            "category": item[2],
            "price": item[3],
            "quantity": item[4]
        } for item in items])

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": f"MySQL Error: {err}"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Route to add a transaction (purchase of an item)
@app.route('/api/add_transaction', methods=['POST'])
def add_transaction():
    try:
        data = request.get_json()
        cur = mysql.connection.cursor()
        
        # Check if the item exists in the database
        cur.execute("SELECT * FROM grocery_items WHERE id = %s", (data['item_id'],))
        item = cur.fetchone()
        
        if not item:
            return jsonify({"message": "Item not found!"}), 404

        # Check if enough stock is available
        if item[4] < data['quantity']:
            return jsonify({"message": "Not enough stock!"}), 400

        # Update stock quantity
        new_quantity = item[4] - data['quantity']
        cur.execute("UPDATE grocery_items SET quantity = %s WHERE id = %s", (new_quantity, data['item_id']))

        # Insert transaction record
        cur.execute("INSERT INTO transactions (item_id, quantity) VALUES (%s, %s)", (data['item_id'], data['quantity']))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Transaction successful!"}), 201
    
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": f"MySQL Error: {err}"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Route to view all transactions
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT t.id, gi.name, t.quantity, t.date FROM transactions t JOIN grocery_items gi ON t.item_id = gi.id")
        transactions = cur.fetchall()
        cur.close()

        return jsonify([{
            "id": txn[0],
            "item_name": txn[1],
            "quantity": txn[2],
            "date": txn[3]
        } for txn in transactions])
    
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": f"MySQL Error: {err}"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Route to generate a sales report (total sales by item)
@app.route('/api/report', methods=['GET'])
def generate_report():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT gi.name, SUM(t.quantity * gi.price) AS total_sales
            FROM transactions t
            JOIN grocery_items gi ON t.item_id = gi.id
            GROUP BY gi.name
        """)
        report = cur.fetchall()
        cur.close()

        return jsonify([{
            "item_name": r[0],
            "total_sales": r[1]
        } for r in report])

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        return jsonify({"error": f"MySQL Error: {err}"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Route to view the homepage
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_item')
def add_item_page():
    return render_template('add_item.html')

# Route to view all items page
@app.route('/items')
def items_page():
    return render_template('items.html')


# Route to view all transactions page
@app.route('/transactions')
def transactions_page():
    return render_template('transactions.html')


# Route to view sales report page
@app.route('/report')
def report_page():
    return render_template('report.html')


if __name__ == '__main__':
    app.run(debug=True)  # Make sure the debug mode is enabled for error logging
