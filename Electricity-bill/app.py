from flask import Flask, render_template, jsonify, request, redirect, url_for
import pyodbc

app = Flask(__name__)

def get_db_connection():
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=DESKTOP-KHKO40I\\SQLEXPRESS;"
            "DATABASE=ELEC-Learn;"
            "Trusted_Connection=yes;"
        )
        cursor = conn.cursor()
        print("Connected to SQL Server successfully!")

        # Ensure the table exists (create it if not)
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'customers')
        BEGIN
            CREATE TABLE customers (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(100),
                meter_number NVARCHAR(50),
                address NVARCHAR(255),
                city NVARCHAR(50),
                state NVARCHAR(50),
                email NVARCHAR(100),
                phone_number NVARCHAR(20)
            )
        END
        """)
        conn.commit()
        print("Table checked/created successfully.")

        return conn  # Return the connection
    except pyodbc.Error as e:
        print("Failed to connect to SQL Server.")
        print("Error:", e)
        return None  # Return None if connection fails

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/add-customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'GET':
        return render_template("new_customer.html")
    
    try:
        data = request.get_json()  # Get JSON data from request

        # Extract data fields
        name = data.get('name')
        meter_number = data.get('meter_number')
        address = data.get('address')
        city = data.get('city')
        state = data.get('state')
        email = data.get('email')
        phone_number = data.get('phone_number')

        # Connect to SQL Server
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Insert into database
        cursor.execute("""
            INSERT INTO customers (name, meter_number, address, city, state, email, phone_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, meter_number, address, city, state, email, phone_number))

        conn.commit()
        conn.close()

        return jsonify({"message": "Customer added successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/update-customer', methods=['GET', 'POST'])
def update():
    if request.method == 'GET':
        return render_template("update.html")
    
    try:
        data = request.get_json()  # Get JSON data from request

        # Extract data fields
        name = data.get('name')
        meter_number = data.get('meter_number')
        address = data.get('address')
        city = data.get('city')
        state = data.get('state')
        email = data.get('email')
        phone_number = data.get('phone_number')

        # Connect to SQL Server
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # Insert into database
        cursor.execute("""
            INSERT INTO customers (name, meter_number, address, city, state, email, phone_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, meter_number, address, city, state, email, phone_number))

        conn.commit()
        conn.close()

        return jsonify({"message": "Customer added successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generated-bill',methods = ['GET', 'POST'])
def view_bill():
    
    return render_template('bill.hmtl')

@app.route('/generate-bill', methods=['GET', 'POST'])
def generate_bill():
    if request.method == 'POST':
        data = request.get_json()
        ca_number = data.get('ca_number')  # Fetching CA Number dynamically

        if not ca_number:
            return jsonify({"error": "CA_Number is required"}), 400

        query = '''
        WITH Consumption_Diff AS (
            SELECT 
                e1.CA_Number,
                e1.Customer_Name,
                e1.Meter_Number,
                e1.Tariff_Plan,
                e1.Fixed_Charge,
                e1.Power_Factor,
                e2.Billing_Month AS Current_Month,
                e1.Billing_Month AS Previous_Month,
                e2.Kwh_Consumption - e1.Kwh_Consumption AS Kwh_Difference
            FROM Electricity_Bills e1
            JOIN Electricity_Bills2 e2 ON e1.CA_Number = e2.CA_Number
            WHERE e1.CA_Number = ?
        )
        SELECT 
            CA_Number,
            Customer_Name,
            Meter_Number,
            Tariff_Plan,
            Fixed_Charge,
            Current_Month,
            Previous_Month,
            Kwh_Difference,

            -- Energy Charge Calculation Based on kWh Slabs
            CASE 
                WHEN Kwh_Difference <= 100 THEN Kwh_Difference * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)
                WHEN Kwh_Difference <= 300 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                               ((Kwh_Difference - 100) * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END))
                WHEN Kwh_Difference <= 500 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                               (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                                               ((Kwh_Difference - 300) * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END))
                ELSE (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                     (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                     (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END)) + 
                     ((Kwh_Difference - 500) * (CASE WHEN Tariff_Plan = 'Residential' THEN 8.5 ELSE 12 END))
            END AS Energy_Charge,

            -- Fuel Surcharge (Assuming 15% per kWh)
            (Kwh_Difference * 0.15) AS Fuel_Surcharge,

            -- Tax Calculation (10% of total charges)
            (0.10 * (Fixed_Charge + 
                     CASE 
                        WHEN Kwh_Difference <= 100 THEN Kwh_Difference * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)
                        WHEN Kwh_Difference <= 300 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                                      ((Kwh_Difference - 100) * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END))
                        WHEN Kwh_Difference <= 500 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                                      (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                                                      ((Kwh_Difference - 300) * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END))
                        ELSE (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                             (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                             (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END)) + 
                             ((Kwh_Difference - 500) * (CASE WHEN Tariff_Plan = 'Residential' THEN 8.5 ELSE 12 END))
                     END + 
                     (Kwh_Difference * 0.15))) AS Tax,

            -- Power Factor Penalty (5% penalty if Power Factor < 0.90)
            CASE 
                WHEN Power_Factor < 0.90 THEN 0.05 * (Fixed_Charge + 
                    CASE 
                        WHEN Kwh_Difference <= 100 THEN Kwh_Difference * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)
                        WHEN Kwh_Difference <= 300 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                                      ((Kwh_Difference - 100) * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END))
                        WHEN Kwh_Difference <= 500 THEN (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                                                      (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                                                      ((Kwh_Difference - 300) * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END))
                        ELSE (100 * (CASE WHEN Tariff_Plan = 'Residential' THEN 5 ELSE 7 END)) + 
                             (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 6.5 ELSE 8.5 END)) + 
                             (200 * (CASE WHEN Tariff_Plan = 'Residential' THEN 7.5 ELSE 10 END)) + 
                             ((Kwh_Difference - 500) * (CASE WHEN Tariff_Plan = 'Residential' THEN 8.5 ELSE 12 END))
                    END + 
                    (Kwh_Difference * 0.15)) 
                ELSE 0 
            END AS Power_Factor_Penalty

        FROM Consumption_Diff;
        '''

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(query, (ca_number,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()

            if not result:
                return jsonify({"message": "No data found for the given CA_Number"}), 404

            # Convert result into a JSON-friendly format
            global bill_data 
            bill_data = []
            for row in result:
                bill_data.append({
                    "CA_Number": row[0],
                    "Customer_Name": row[1],
                    "Meter_Number": row[2],
                    "Tariff_Plan": row[3],
                    "Fixed_Charge": row[4],
                    "Current_Month": row[5],
                    "Previous_Month": row[6],
                    "Kwh_Difference": row[7],
                    "Energy_Charge": row[8],
                    "Fuel_Surcharge": row[9],
                    "Tax": row[10],
                    "Power_Factor_Penalty": row[11]
                })
            print(bill_data)
            return jsonify(bill_data)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Handle GET request (show the form)
    return render_template('generate_bill.html', bill=None)



@app.route('/pay-bill')
def pay_bill():
    return render_template('pay_bill.html')

@app.route('/calculate-bill')
def calculate_bill():
    return render_template('calculate_bill.html')

@app.route('/delete-customer', methods=['GET', 'POST'])
def delete_customer():
    if request.method == 'POST':
        customer_id = request.form.get('id')  # Use 'id' instead of 'name' for accuracy

        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        try:
            # Delete customer from the database
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500

    return render_template('delete_customer.html')

if __name__ == '__main__':
    app.run(debug=True)
