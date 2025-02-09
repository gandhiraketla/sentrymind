import os
import sys
import mysql.connector
from typing import Dict, List, Any
from decimal import Decimal
from datetime import datetime

# Add parent directory to system path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from util.envutils import EnvUtils

class AgentTools:
    def __init__(self):
        """
        Initialize database connection using environment variables
        """
        # Initialize environment utilities
        self.env_utils = EnvUtils()

        # Read database configuration from environment variables
        self.host = self.env_utils.get_required_env("DB_HOST")
        self.user = self.env_utils.get_required_env("DB_USER")
        self.password = self.env_utils.get_required_env("DB_PASSWORD")
        self.database = self.env_utils.get_required_env("DB_NAME")

    def get_connection(self):
        """
        Establish a connection to the MySQL database
        
        :return: MySQL database connection
        """
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return connection
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL database: {e}")
            return None

    def _convert_transaction_to_json_friendly(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert transaction data to JSON-friendly format
        
        :param transaction: Transaction dictionary from database
        :return: JSON-friendly transaction dictionary
        """
        if not transaction:
            return None
        
        # Create a copy to avoid modifying the original
        converted = transaction.copy()
        
        # Convert datetime to ISO format string
        if 'trans_date' in converted and isinstance(converted['trans_date'], datetime):
            converted['trans_date'] = converted['trans_date'].isoformat()
        
        # Convert Decimal to float
        if 'amt' in converted and isinstance(converted['amt'], Decimal):
            converted['amt'] = float(converted['amt'])
        
        return converted

    def getTransactions(self, trans_num: str) -> Dict[str, Any]:
        """
        Retrieve current transaction and last 6 transactions for a given transaction number
        
        :param trans_num: Transaction number to look up
        :return: Dictionary containing current and past transactions
        """
        connection = self.get_connection()
        if not connection:
            return {"error": "Database connection failed"}

        try:
            cursor = connection.cursor(dictionary=True)

            # Query 1: Current Transaction
            current_query = """
            SELECT 
                trans_num, 
                trans_date, 
                cc_num, 
                merchant, 
                category, 
                amount as amt, 
                city, 
                is_fraud
            FROM transactions
            WHERE trans_num = %s
            """
            cursor.execute(current_query, (trans_num,))
            current_transaction = self._convert_transaction_to_json_friendly(cursor.fetchone())

            # Query 2: Last 10 Transactions
            past_query = """
            SELECT 
                trans_num, 
                trans_date, 
                merchant, 
                category, 
                amount as amt, 
                city, 
                is_fraud
            FROM transactions
            WHERE cc_num = (SELECT cc_num FROM transactions WHERE trans_num = %s)
            AND trans_num != %s
            ORDER BY trans_date DESC
            LIMIT 10
            """
            cursor.execute(past_query, (trans_num, trans_num))
            past_transactions = [
                self._convert_transaction_to_json_friendly(transaction) 
                for transaction in cursor.fetchall()
            ]

            # Construct return dictionary
            result = {
                "current_transaction": current_transaction,
                "past_transactions": past_transactions
            }

            cursor.close()
            connection.close()

            return result

        except mysql.connector.Error as e:
            print(f"Error executing query: {e}")
            return {"error": str(e)}
        finally:
            if connection and connection.is_connected():
                connection.close()

def main():
    """
    Example usage and testing of AgentTools class
    """
    # Create AgentTools instance (credentials loaded from .env)
    agent_tools = AgentTools()

    # Example transaction number to test
    test_trans_num = '14b8331a59459499ea6fc0015aea4ae4'
    
    # Retrieve transactions
    transactions = agent_tools.getTransactions(test_trans_num)
    
    # Print the results
    import json
    print(json.dumps(transactions, indent=2))

if __name__ == "__main__":
    main()