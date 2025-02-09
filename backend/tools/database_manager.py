import os
import sys
import json
import mysql.connector
from datetime import datetime
from decimal import Decimal
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from util.envutils import EnvUtils

class DatabaseManager:
    def __init__(self):
        envutils = EnvUtils()
        self.db_config = {
            'host': envutils.get_required_env("DB_HOST"),
            'user': envutils.get_required_env("DB_USER"),
            'password': envutils.get_required_env("DB_PASSWORD"),
            'database': envutils.get_required_env("DB_NAME")
        }
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
        except mysql.connector.Error as err:
            raise Exception(f"Error connecting to database: {err}")

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def _decimal_to_float(self, obj):
        if isinstance(obj, dict):
            return {k: self._decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._decimal_to_float(v) for v in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj

    

    def getCustomerDetails(self, customer_id):
        try:
            self.connect()
            
            customer_query = """
                SELECT 
                    customer_id,
                    account_number,
                    name,
                    address,
                    city,
                    country,
                    account_type,
                    is_business,
                    business_category,
                    created_at,
                    risk_level,
                    CAST(risk_score AS FLOAT) as risk_score
                FROM sentrymind_customers
                WHERE customer_id = %s
            """
            
            transactions_query = """
                SELECT 
                    transaction_id,
                    transaction_date,
                    CAST(transaction_amount AS FLOAT) as transaction_amount,
                    transaction_type,
                    merchant_category,
                    destination_country,
                    transaction_frequency,
                    CAST(account_balance_before AS FLOAT) as account_balance_before,
                    CAST(account_balance_after AS FLOAT) as account_balance_after,
                    is_fraud
                FROM sentrymind_transactions
                WHERE customer_id = %s
                ORDER BY transaction_date DESC
                LIMIT 10
            """
            
            fraud_stats_query = """
                SELECT 
                    COUNT(*) as total_fraud_transactions,
                    CAST(SUM(transaction_amount) AS FLOAT) as total_fraud_amount
                FROM sentrymind_transactions
                WHERE customer_id = %s AND is_fraud = 1
            """
            
            self.cursor.execute(customer_query, (customer_id,))
            customer_info = self.cursor.fetchone()
            
            if not customer_info:
                return json.dumps({"error": f"Customer {customer_id} not found"})
            
            self.cursor.execute(transactions_query, (customer_id,))
            transactions = self.cursor.fetchall()
            
            self.cursor.execute(fraud_stats_query, (customer_id,))
            fraud_stats = self.cursor.fetchone()
            
            customer_info['created_at'] = customer_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            for transaction in transactions:
                transaction['transaction_date'] = transaction['transaction_date'].strftime('%Y-%m-%d %H:%M:%S')
            
            return json.dumps({
                "customerInfo": customer_info,
                "fraudStats": fraud_stats,
                "recentTransactions": transactions
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)})
        finally:
            self.disconnect()
    def saveSARReport(self,sar_json):
        """Save the SAR report in the database."""
        try:
            if isinstance(sar_json, str):
                sar_json = json.loads(sar_json)
            account_number = sar_json.get("customerInfo", {}).get("account_number", None)
            if not account_number:
                raise ValueError("Account number not found in SAR JSON.")
            self.connect()
            
            insert_query = """
                INSERT INTO sar_reports (account_number, json_data, created_date)
                VALUES (%s, %s, %s)
            """
            
            json_data = json.dumps(sar_json)  # Convert JSON to string
            created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.cursor.execute(insert_query, (account_number, json_data, created_date))
            self.connection.commit()
            
            return {"message": "SAR report saved successfully."}
        
        except mysql.connector.Error as err:
            return {"error": f"Error saving SAR report: {err}"}
        
        finally:
            self.disconnect()
# Usage example:
if __name__ == "__main__":
    db_manager = DatabaseManager()
    sar_report = {
        "customerInfo": {
            "customer_id": "42e60d56-b222-4c67-9432-cfab2520fde0",
            "account_number": "1125218191",
            "name": "Brett Johnson"
        },
        "fraudStats": {"total_fraud_transactions": 10, "total_fraud_amount": 106990.0},
        "recentTransactions": [
            {
                "transaction_id": "TXN_51e8448fa0934eaab399a28449b46d4e",
                "transaction_date": "2025-02-01 15:38:47",
                "transaction_amount": 1921.48
            }
        ]
    }
    db_manager.saveSARReport(sar_report)
    #print("\nCustomer Details:")
    #print(db_manager.getCustomerDetails("42e60d56-b222-4c67-9432-cfab2520fde0"))