import pymysql
import random
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any
import time
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

# Constants
BATCH_SIZE = 10000
TOTAL_RECORDS = 1000000
FRAUD_PERCENTAGE = 0.10

# Transaction types and countries
TRANSACTION_TYPES = ['Cash Deposit', 'Wire Transfer', 'Card Payment', 'Crypto Exchange']
ACCOUNT_TYPES = ['Checking', 'Savings', 'Business']
MERCHANT_CATEGORIES = [
    'Retail', 'Travel', 'Entertainment', 'Groceries', 'Electronics',
    'Healthcare', 'Automotive', 'Restaurant', 'Utilities', 'Education'
]
COUNTRIES = [
    'USA', 'Canada', 'UK', 'Germany', 'France', 'Japan', 'Australia',
    'Switzerland', 'Singapore', 'UAE', 'Cayman Islands', 'Panama'
]
HIGH_RISK_COUNTRIES = ['Cayman Islands', 'Panama', 'UAE']

class CustomerRiskManager:
    def __init__(self, cursor):
        self.cursor = cursor
        self.customer_profiles = {}
        self.high_risk_customers = set()
        self.medium_risk_customers = set()
        self.low_risk_customers = set()
        self.customer_fraud_types = {}
        self.initialize_customer_profiles()

    def initialize_customer_profiles(self):
        """Initialize customer risk profiles from database"""
        # First, fetch all relevant customer data
        self.cursor.execute("""
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
                risk_score
            FROM sentrymind_customers
        """)
        customers = self.cursor.fetchall()
        
        # Calculate initial risk distribution
        all_customer_ids = [row[0] for row in customers]
        total_customers = len(all_customer_ids)
        high_risk_count = int(total_customers * 0.20)  # 20% high risk
        medium_risk_count = int(total_customers * 0.30)  # 30% medium risk
        
        # Randomly shuffle for initial distribution
        random.shuffle(all_customer_ids)
        initial_high_risk = set(all_customer_ids[:high_risk_count])
        initial_medium_risk = set(all_customer_ids[high_risk_count:high_risk_count + medium_risk_count])
        initial_low_risk = set(all_customer_ids[high_risk_count + medium_risk_count:])
        
        # Update database with initial risk levels
        # Set high risk customers
        self.cursor.executemany(
            "UPDATE sentrymind_customers SET risk_level = 'high', risk_score = 75.0 WHERE customer_id = %s",
            [(cid,) for cid in initial_high_risk]
        )
        
        # Set medium risk customers
        self.cursor.executemany(
            "UPDATE sentrymind_customers SET risk_level = 'medium', risk_score = 50.0 WHERE customer_id = %s",
            [(cid,) for cid in initial_medium_risk]
        )
        
        # Set low risk customers
        self.cursor.executemany(
            "UPDATE sentrymind_customers SET risk_level = 'low', risk_score = 25.0 WHERE customer_id = %s",
            [(cid,) for cid in initial_low_risk]
        )
        
        # Commit the updates
        self.cursor.connection.commit()
        
        # Fetch updated data
        self.cursor.execute("""
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
                risk_score
            FROM sentrymind_customers
        """)
        updated_customers = self.cursor.fetchall()
        
        # Create profiles using actual customer data
        for row in updated_customers:
            customer_id = row[0]
            risk_level = row[10]  # risk_level is at index 10
            
            # Assign to appropriate risk set
            if risk_level == 'high':
                self.high_risk_customers.add(customer_id)
            elif risk_level == 'medium':
                self.medium_risk_customers.add(customer_id)
            else:
                self.low_risk_customers.add(customer_id)
            
            # Create profile with actual customer data
            self.customer_profiles[customer_id] = {
                'customer_id': row[0],
                'account_number': row[1],
                'name': row[2],
                'address': row[3],
                'city': row[4],
                'country': row[5],
                'account_type': row[6],
                'is_business': row[7],
                'business_category': row[8],
                'created_at': row[9],
                'risk_level': risk_level,
                'risk_score': float(row[11]) if row[11] is not None else 0.0,
                'last_transaction_date': None,
                'fraud_types': set(),
                'suspicious_activity_count': 0,
                'base_balance': random.uniform(10000, 200000)  # Adding base_balance here
            }

    def get_fraud_candidates(self, fraud_type: str, count: int) -> List[str]:
        """Get suitable customers for a specific fraud type, prioritizing consistent behavior"""
        # First, find customers who have already done this type of fraud
        existing_fraudsters = [
            customer_id 
            for customer_id, profile in self.customer_profiles.items()
            if fraud_type in profile['fraud_types']
        ]
        
        # If we have existing fraudsters, prioritize them
        if existing_fraudsters:
            needed_count = count - len(existing_fraudsters)
            if needed_count <= 0:
                return random.sample(existing_fraudsters, count)
            
            # Use existing fraudsters and add new ones if needed
            candidates = existing_fraudsters.copy()
            
            # Get new candidates based on risk level
            if fraud_type in ['Structuring', 'Large Wire Transfer', 'Layering']:
                new_pool = list(self.high_risk_customers - set(existing_fraudsters))
            elif fraud_type in ['Frequent Offshore Transfers', 'Inconsistent Business Activity']:
                new_pool = list((self.high_risk_customers | self.medium_risk_customers) - set(existing_fraudsters))
            else:  # Rapid In-Out
                new_pool = list((self.high_risk_customers | self.medium_risk_customers) - set(existing_fraudsters))
            
            if new_pool:
                candidates.extend(random.sample(new_pool, min(needed_count, len(new_pool))))
            
            return candidates
        
        # If no existing fraudsters, follow risk-based selection
        if fraud_type in ['Structuring', 'Large Wire Transfer', 'Layering']:
            eligible_customers = list(self.high_risk_customers)
        elif fraud_type in ['Frequent Offshore Transfers', 'Inconsistent Business Activity']:
            eligible_customers = list(self.high_risk_customers | self.medium_risk_customers)
        else:  # Rapid In-Out
            customers = list(self.high_risk_customers | self.medium_risk_customers)
            weights = [0.7 if c in self.high_risk_customers else 0.3 for c in customers]
            return random.choices(customers, weights=weights, k=count)
        
        return random.sample(eligible_customers, min(count, len(eligible_customers)))

    def record_fraud_activity(self, customer_id: str, fraud_type: str):
        """Record that a customer has performed a specific type of fraud"""
        if customer_id in self.customer_profiles:
            self.customer_profiles[customer_id]['fraud_types'].add(fraud_type)

    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get customer profile including risk level and fraud history"""
        return self.customer_profiles.get(customer_id, None)

    def update_last_transaction(self, customer_id: str, transaction_date: datetime):
        """Update the last transaction date for a customer"""
        if customer_id in self.customer_profiles:
            self.customer_profiles[customer_id]['last_transaction_date'] = transaction_date

    def get_legitimate_customers(self, count: int) -> List[str]:
        """Get a list of legitimate customers"""
        # Prioritize low-risk and medium-risk customers
        legitimate_pool = list(self.low_risk_customers | self.medium_risk_customers)
        
        # If not enough legitimate customers, include some from high-risk group
        if len(legitimate_pool) < count:
            legitimate_pool.extend(list(self.high_risk_customers))
        
        return random.sample(legitimate_pool, min(count, len(legitimate_pool)))

def create_db_connection():
    """Create database connection"""
    return pymysql.connect(**DB_CONFIG)

def generate_transaction_amount(transaction_type: str, is_fraud: bool) -> float:
    """Generate transaction amount based on type and fraud status"""
    if is_fraud:
        if transaction_type == 'Cash Deposit':  # Structuring
            return random.uniform(9000, 9999)
        elif transaction_type == 'Wire Transfer':  # Large transfers
            return random.uniform(50000, 1000000)
    
    # Normal transactions
    base_amounts = {
        'Cash Deposit': (100, 5000),
        'Wire Transfer': (1000, 25000),
        'Card Payment': (10, 2000),
        'Crypto Exchange': (500, 10000)
    }
    min_amt, max_amt = base_amounts[transaction_type]
    return round(random.uniform(min_amt, max_amt), 2)

def generate_legitimate_transaction(customer_id: str, risk_manager: 'CustomerRiskManager') -> Dict[str, Any]:
    """Generate legitimate transaction"""
    customer = risk_manager.get_customer_profile(customer_id)
    transaction_type = random.choice(TRANSACTION_TYPES)
    amount = generate_transaction_amount(transaction_type, False)
    base_balance = customer['base_balance']
    account_type = customer['account_type']
    
    return {
        'transaction_id': f"TXN_{uuid.uuid4().hex}",
        'customer_id': customer_id,
        'transaction_date': datetime.now() - timedelta(days=random.randint(1, 180)),
        'transaction_amount': amount,
        'transaction_type': transaction_type,
        'account_type': account_type,
        'merchant_category': customer['business_category'] if customer['is_business'] else random.choice(MERCHANT_CATEGORIES),
        'destination_country': customer['country'],
        'transaction_frequency': random.randint(1, 10),
        'account_balance_before': base_balance,
        'account_balance_after': base_balance + amount,
        'is_fraud': 0,
        'fraud_type': None
    }

# The rest of the functions remain the same as in the original code (generate_structuring_pattern, generate_layering_pattern, etc.)
# I've omitted them for brevity, but they should be included in the full script
def create_db_connection():
    """Create database connection"""
    return pymysql.connect(**DB_CONFIG)

def generate_transaction_amount(transaction_type: str, is_fraud: bool) -> float:
    """Generate transaction amount based on type and fraud status"""
    if is_fraud:
        if transaction_type == 'Cash Deposit':  # Structuring
            return random.uniform(9000, 9999)
        elif transaction_type == 'Wire Transfer':  # Large transfers
            return random.uniform(50000, 1000000)
    
    # Normal transactions
    base_amounts = {
        'Cash Deposit': (100, 5000),
        'Wire Transfer': (1000, 25000),
        'Card Payment': (10, 2000),
        'Crypto Exchange': (500, 10000)
    }
    min_amt, max_amt = base_amounts[transaction_type]
    return round(random.uniform(min_amt, max_amt), 2)

def generate_structuring_pattern(customer_id: str, risk_manager: 'CustomerRiskManager') -> List[Dict[str, Any]]:
    """Generate structuring pattern (multiple cash deposits under $10K)"""
    transactions = []
    customer = risk_manager.get_customer_profile(customer_id)
    base_date = datetime.now() - timedelta(days=random.randint(1, 180))
    
    # Generate appropriate starting balance based on account type and business status
    if customer['is_business']:
        starting_balance = random.uniform(50000, 200000)
    else:
        starting_balance = random.uniform(10000, 50000)
    
    current_balance = starting_balance
    
    # Use actual customer account type and business status
    account_type = customer['account_type']
    is_business = customer['is_business']
    
    # Record this fraud type for the customer
    risk_manager.record_fraud_activity(customer_id, 'Structuring')
    
    for _ in range(random.randint(3, 5)):
        amount = random.uniform(9000, 9999)
        balance_before = current_balance
        balance_after = current_balance + amount
        current_balance = balance_after
        
        transaction = {
            'transaction_id': f"TXN_{uuid.uuid4().hex}",
            'customer_id': customer_id,
            'transaction_date': base_date + timedelta(hours=random.randint(1, 72)),
            'transaction_amount': amount,
            'transaction_type': 'Cash Deposit',
            'account_type': account_type,
            'merchant_category': customer['business_category'] if is_business else random.choice(MERCHANT_CATEGORIES),
            'destination_country': customer['country'],
            'transaction_frequency': random.randint(1, 5),
            'account_balance_before': balance_before,
            'account_balance_after': balance_after,
            'is_fraud': 1,
            'fraud_type': ''
        }
        transactions.append(transaction)
        base_date += timedelta(days=1)
        risk_manager.update_last_transaction(customer_id, transaction['transaction_date'])
    
    return transactions

def generate_layering_pattern(customer_id: str, risk_manager: 'CustomerRiskManager') -> List[Dict[str, Any]]:
    """Generate layering pattern (rapid money movement through multiple accounts)"""
    transactions = []
    customer = risk_manager.get_customer_profile(customer_id)
    base_date = datetime.now() - timedelta(days=random.randint(1, 180))
    
    # Higher starting balance for layering operations
    if customer['is_business']:
        starting_balance = random.uniform(200000, 500000)
    else:
        starting_balance = random.uniform(100000, 300000)
    
    current_balance = starting_balance
    account_type = customer['account_type']
    
    risk_manager.record_fraud_activity(customer_id, 'Layering')
    
    num_transfers = random.randint(4, 8)
    for i in range(num_transfers):
        amount = random.uniform(20000, 45000)
        is_incoming = i % 2 == 0
        balance_before = current_balance
        balance_after = current_balance + (amount if is_incoming else -amount)
        current_balance = balance_after
        
        transaction = {
            'transaction_id': f"TXN_{uuid.uuid4().hex}",
            'customer_id': customer_id,
            'transaction_date': base_date + timedelta(hours=random.randint(1, 12)),
            'transaction_amount': amount,
            'transaction_type': 'Wire Transfer',
            'account_type': account_type,
            'merchant_category': 'Crypto Exchange' if random.random() < 0.7 else 'Financial Services',
            'destination_country': random.choice(HIGH_RISK_COUNTRIES if not is_incoming else COUNTRIES),
            'transaction_frequency': random.randint(5, 10),
            'account_balance_before': balance_before,
            'account_balance_after': balance_after,
            'is_fraud': 1,
            'fraud_type': ''
        }
        transactions.append(transaction)
        base_date += timedelta(hours=random.randint(2, 8))
        risk_manager.update_last_transaction(customer_id, transaction['transaction_date'])
    
    return transactions

def generate_large_wire_pattern(customer_id: str, risk_manager: 'CustomerRiskManager') -> Dict[str, Any]:
    """Generate large wire transfer pattern"""
    customer = risk_manager.get_customer_profile(customer_id)
    
    # High starting balance for large wire transfers
    if customer['is_business']:
        starting_balance = random.uniform(500000, 1000000)
    else:
        starting_balance = random.uniform(200000, 500000)
    
    amount = random.uniform(50000, 1000000)
    account_type = customer['account_type']
    
    risk_manager.record_fraud_activity(customer_id, 'Large Wire Transfer')
    
    transaction = {
        'transaction_id': f"TXN_{uuid.uuid4().hex}",
        'customer_id': customer_id,
        'transaction_date': datetime.now() - timedelta(days=random.randint(1, 180)),
        'transaction_amount': amount,
        'transaction_type': 'Wire Transfer',
        'account_type': account_type,
        'merchant_category': customer['business_category'] if customer['is_business'] else random.choice(MERCHANT_CATEGORIES),
        'destination_country': random.choice(HIGH_RISK_COUNTRIES),
        'transaction_frequency': random.randint(1, 3),
        'account_balance_before': starting_balance,
        'account_balance_after': starting_balance - amount,
        'is_fraud': 1,
        'fraud_type': ''
    }
    risk_manager.update_last_transaction(customer_id, transaction['transaction_date'])
    
    return transaction

def generate_frequent_offshore_pattern(customer_id: str, risk_manager: 'CustomerRiskManager') -> List[Dict[str, Any]]:
    """Generate frequent small transfers to offshore accounts"""
    transactions = []
    customer = risk_manager.get_customer_profile(customer_id)
    base_date = datetime.now() - timedelta(days=random.randint(1, 180))
    
    # Starting balance for offshore transfers
    if customer['is_business']:
        starting_balance = random.uniform(100000, 300000)
    else:
        starting_balance = random.uniform(50000, 150000)
    
    current_balance = starting_balance
    account_type = customer['account_type']
    
    risk_manager.record_fraud_activity(customer_id, 'Frequent Offshore Transfers')
    
    num_transfers = random.randint(5, 8)
    for _ in range(num_transfers):
        amount = random.uniform(5000, 15000)
        balance_before = current_balance
        balance_after = current_balance - amount
        current_balance = balance_after
        
        transaction = {
            'transaction_id': f"TXN_{uuid.uuid4().hex}",
            'customer_id': customer_id,
            'transaction_date': base_date + timedelta(hours=random.randint(12, 48)),
            'transaction_amount': amount,
            'transaction_type': 'Wire Transfer',
            'account_type': account_type,
            'merchant_category': customer['business_category'] if customer['is_business'] else random.choice(MERCHANT_CATEGORIES),
            'destination_country': random.choice(HIGH_RISK_COUNTRIES),
            'transaction_frequency': random.randint(4, 8),
            'account_balance_before': balance_before,
            'account_balance_after': balance_after,
            'is_fraud': 1,
            'fraud_type': ''
        }
        transactions.append(transaction)
        base_date += timedelta(days=random.randint(1, 3))
        risk_manager.update_last_transaction(customer_id, transaction['transaction_date'])
    
    return transactions

def generate_legitimate_transaction(customer_id: str, risk_manager: 'CustomerRiskManager') -> Dict[str, Any]:
    """Generate legitimate transaction"""
    customer = risk_manager.get_customer_profile(customer_id)
    transaction_type = random.choice(TRANSACTION_TYPES)
    amount = generate_transaction_amount(transaction_type, False)
    
    # Generate appropriate starting balance based on profile
    if customer['is_business']:
        starting_balance = random.uniform(50000, 200000)
    else:
        starting_balance = random.uniform(5000, 50000)
    
    return {
        'transaction_id': f"TXN_{uuid.uuid4().hex}",
        'customer_id': customer_id,
        'transaction_date': datetime.now() - timedelta(days=random.randint(1, 180)),
        'transaction_amount': amount,
        'transaction_type': transaction_type,
        'account_type': customer['account_type'],
        'merchant_category': customer['business_category'] if customer['is_business'] else random.choice(MERCHANT_CATEGORIES),
        'destination_country': customer['country'],
        'transaction_frequency': random.randint(1, 10),
        'account_balance_before': starting_balance,
        'account_balance_after': starting_balance + amount,
        'is_fraud': 0,
        'fraud_type': None
    }

def generate_rapid_inout_pattern(customer_id: str, risk_manager: 'CustomerRiskManager') -> List[Dict[str, Any]]:
    """Generate rapid deposit and withdrawal pattern"""
    transactions = []
    customer = risk_manager.get_customer_profile(customer_id)
    base_date = datetime.now() - timedelta(days=random.randint(1, 180))
    base_balance = customer['base_balance']
    account_type = customer['account_type']
    
    risk_manager.record_fraud_activity(customer_id, 'Rapid In-Out')
    
    deposit_amount = random.uniform(10000, 50000)
    deposit = {
        'transaction_id': f"TXN_{uuid.uuid4().hex}",
        'customer_id': customer_id,
        'transaction_date': base_date,
        'transaction_amount': deposit_amount,
        'transaction_type': random.choice(['Cash Deposit', 'Wire Transfer']),
        'account_type': account_type,
        'merchant_category': random.choice(MERCHANT_CATEGORIES),
        'destination_country': customer['country'],
        'transaction_frequency': random.randint(2, 5),
        'account_balance_before': base_balance,
        'account_balance_after': base_balance + deposit_amount,
        'is_fraud': 1,
        'fraud_type': ''
    }
    transactions.append(deposit)
    
    withdrawal_amount = deposit_amount * random.uniform(0.9, 0.95)
    withdrawal = {
        'transaction_id': f"TXN_{uuid.uuid4().hex}",
        'customer_id': customer_id,
        'transaction_date': base_date + timedelta(hours=random.randint(1, 12)),
        'transaction_amount': withdrawal_amount,
        'transaction_type': 'Wire Transfer',
        'account_type': account_type,
        'merchant_category': deposit['merchant_category'],
        'destination_country': random.choice(HIGH_RISK_COUNTRIES),
        'transaction_frequency': deposit['transaction_frequency'],
        'account_balance_before': deposit['account_balance_after'],
        'account_balance_after': deposit['account_balance_after'] - withdrawal_amount,
        'is_fraud': 1,
        'fraud_type': ''
    }
    transactions.append(withdrawal)
    risk_manager.update_last_transaction(customer_id, withdrawal['transaction_date'])
    
    return transactions

def generate_legitimate_transaction(customer_id: str, risk_manager: 'CustomerRiskManager') -> Dict[str, Any]:
    """Generate legitimate transaction"""
    customer = risk_manager.get_customer_profile(customer_id)
    transaction_type = random.choice(TRANSACTION_TYPES)
    amount = generate_transaction_amount(transaction_type, False)
    base_balance = customer['base_balance']
    account_type = customer['account_type']
    
    return {
        'transaction_id': f"TXN_{uuid.uuid4().hex}",
        'customer_id': customer_id,
        'transaction_date': datetime.now() - timedelta(days=random.randint(1, 180)),
        'transaction_amount': amount,
        'transaction_type': transaction_type,
        'account_type': account_type,
        'merchant_category': random.choice(MERCHANT_CATEGORIES),
        'destination_country': customer['country'],
        'transaction_frequency': random.randint(1, 10),
        'account_balance_before': base_balance,
        'account_balance_after': base_balance + amount,
        'is_fraud': 0,
        'fraud_type': None
    }

def insert_transactions(conn, transactions: List[Dict[str, Any]]):
    """Insert transactions into database"""
    with conn.cursor() as cursor:
        for transaction in transactions:
            sql = """INSERT INTO sentrymind_transactions (
                transaction_id, customer_id, transaction_date, transaction_amount,
                transaction_type, account_type, merchant_category, destination_country,
                transaction_frequency, account_balance_before, account_balance_after,
                is_fraud, fraud_type
            ) VALUES (
                %(transaction_id)s, %(customer_id)s, %(transaction_date)s, %(transaction_amount)s,
                %(transaction_type)s, %(account_type)s, %(merchant_category)s, %(destination_country)s,
                %(transaction_frequency)s, %(account_balance_before)s, %(account_balance_after)s,
                %(is_fraud)s, %(fraud_type)s
            )"""
            cursor.execute(sql, transaction)
    conn.commit()

def main():
    conn = create_db_connection()
    records_generated = 0
    batch_number = 1
    
    try:
        cursor = conn.cursor()
        
        # Initialize customer risk manager
        risk_manager = CustomerRiskManager(cursor)
        
        while records_generated < TOTAL_RECORDS:
            batch_transactions = []
            
            # Calculate fraud distribution for this batch
            fraud_count = int(BATCH_SIZE * FRAUD_PERCENTAGE)
            legitimate_count = BATCH_SIZE - fraud_count
            
            # Generate fraud transactions
            fraud_types = {
                'structuring': {'weight': 0.15, 'generator': generate_structuring_pattern},
                'layering': {'weight': 0.15, 'generator': generate_layering_pattern},
                'large_wire': {'weight': 0.15, 'generator': generate_large_wire_pattern},
                'frequent_offshore': {'weight': 0.20, 'generator': generate_frequent_offshore_pattern},
                'rapid_inout': {'weight': 0.20, 'generator': generate_rapid_inout_pattern}
            }
            
            fraud_distribution = []
            remaining_fraud_count = fraud_count
            
            # Calculate how many transactions of each type to generate
            for fraud_type, details in fraud_types.items():
                count = int(remaining_fraud_count * details['weight'])
                if count > 0:
                    fraud_distribution.append((fraud_type, count))
            
            # Generate fraud transactions by type
            for fraud_type, count in fraud_distribution:
                # Get suitable customers for this fraud type
                fraud_customers = risk_manager.get_fraud_candidates(fraud_type.replace('_', ' ').title(), count)
                
                for customer_id in fraud_customers:
                    new_transactions = fraud_types[fraud_type]['generator'](customer_id, risk_manager)
                    if isinstance(new_transactions, list):
                        batch_transactions.extend(new_transactions)
                    else:
                        batch_transactions.append(new_transactions)
            
            # Generate legitimate transactions
            legitimate_customers = risk_manager.get_legitimate_customers(legitimate_count)
            for customer_id in legitimate_customers:
                transaction = generate_legitimate_transaction(customer_id, risk_manager)
                batch_transactions.append(transaction)
            
            # Randomize the order of transactions
            random.shuffle(batch_transactions)
            
            # Insert transactions
            insert_transactions(conn, batch_transactions)
            
            records_generated += len(batch_transactions)
            print(f"Batch {batch_number} completed. Total records: {records_generated}")
            batch_number += 1
            
            # Small delay to prevent database overload
            time.sleep(1)
        
        print(f"\nData generation completed successfully!")
        print(f"Total records generated: {records_generated}")
        
        # Verify fraud distribution
        cursor.execute("""
            SELECT fraud_type, COUNT(*) as count, 
                   COUNT(DISTINCT customer_id) as unique_customers,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM sentrymind_transactions 
            WHERE is_fraud = 1 
            GROUP BY fraud_type
        """)
        print("\nFraud Distribution:")
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} transactions ({row[2]} unique customers) - {row[3]}%")
        
        # Verify risk level distribution
        print("\nRisk Level Distribution:")
        print(f"High Risk Customers: {len(risk_manager.high_risk_customers)}")
        print(f"Medium Risk Customers: {len(risk_manager.medium_risk_customers)}")
        print(f"Low Risk Customers: {len(risk_manager.low_risk_customers)}")
    
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()