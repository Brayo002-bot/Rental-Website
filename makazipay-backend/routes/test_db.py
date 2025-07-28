from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)

# ✅ Replace these with your actual values
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'makazipay_user'
app.config['MYSQL_PASSWORD'] = 'securepass123'
app.config['MYSQL_DB'] = 'makazipay_db'

mysql = MySQL(app)

@app.route('/')
def index():
    return {"message": "MakaziPAY Backend is running!"}

@app.route('/test-db')
def test_db():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS total_users FROM users")
        result = cur.fetchone()
        cur.close()
        return {"total_users": result['total_users']}
    except Exception as e:
        return {"error": str(e)}

# ✅ This part is critical to run the Flask server!
if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)
