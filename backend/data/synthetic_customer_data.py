import pymysql
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

import os
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from util.envutils import EnvUtils
# Database configuration
envutils=EnvUtils()
DB_CONFIG = {
    'host': envutils.get_required_env("DB_HOST"),
    'user': envutils.get_required_env("DB_USER"),
    'password': envutils.get_required_env("DB_PASSWORD"),
    'db': envutils.get_required_env("DB_NAME")
}

# Initialize Faker for random data generation
fake = Faker()

# Predefined lists for distribution
HIGH_RISK_COUNTRIES = ["Cayman Islands", "Panama", "Switzerland", "Russia", "China"]
LOW_RISK_COUNTRIES = ["USA", "UK", "Canada", "Germany", "Australia"]
BUSINESS_CATEGORIES = ["Retail", "Crypto Exchange", "Luxury Goods", "Casino", "Electronics", "Travel", "Consulting"]

# Customer distribution settings
TOTAL_CUSTOMERS = 20000

# Function to generate a single customer record
def generate_customer():
    customer_id = str(uuid.uuid4())
    account_number = str(random.randint(1000000000, 9999999999))  # Simulating a 10-digit account number
    name = fake.name()
    address = fake.address()
    city = fake.city()
    country = random.choice(HIGH_RISK_COUNTRIES + LOW_RISK_COUNTRIES)
    account_type = random.choice(["Checking", "Savings", "Business"])
    is_business = account_type == "Business"
    business_category = random.choice(BUSINESS_CATEGORIES) if is_business else None
    created_at = fake.date_time_between(start_date="-2y", end_date="now")  # Accounts created within the last 2 years

    return (
        customer_id, account_number, name, address, city, country,
        account_type, is_business, business_category, created_at
    )

# Generate customer data
customers = [generate_customer() for _ in range(TOTAL_CUSTOMERS)]

# Function to insert generated customers into MySQL
def insert_customers_into_mysql(customers):
    """Inserts generated customers into MySQL database."""
    conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE)
    cursor = conn.cursor()

    sql = """
    INSERT INTO sentrymind_customers (
        customer_id, account_number, name, address, city, country,
        account_type, is_business, business_category, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.executemany(sql, customers)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print(f"Generating {TOTAL_CUSTOMERS} customers...")
    insert_customers_into_mysql(customers)
    print("Data successfully inserted into MySQL.")
