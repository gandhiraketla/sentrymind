CREATE DATABASE sentrymind;
USE sentrymind;
CREATE TABLE sentrymind_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    transaction_date DATETIME,
    transaction_amount DECIMAL(15,2),
    transaction_type ENUM('Cash Deposit', 'Wire Transfer', 'Card Payment', 'Crypto Exchange'),
    account_type ENUM('Checking', 'Savings', 'Business'),
    merchant_category VARCHAR(100)
    destination_country VARCHAR(50),
    transaction_frequency INT,
    account_balance_before DECIMAL(15,2),
    account_balance_after DECIMAL(15,2),
    fraud_type VARCHAR(100),
    is_fraud INT
);
CREATE TABLE sentrymind_training_data (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    transaction_date DATETIME,
    transaction_amount DECIMAL(15,2),
    transaction_type ENUM('Cash Deposit', 'Wire Transfer', 'Card Payment', 'Crypto Exchange'),
    account_type ENUM('Checking', 'Savings', 'Business'),
    merchant_category VARCHAR(100)
    destination_country VARCHAR(50),
    transaction_frequency INT,
    account_balance_before DECIMAL(15,2),
    account_balance_after DECIMAL(15,2),
    fraud_type VARCHAR(100),
    is_fraud INT
);
CREATE TABLE customers (
    customer_id VARCHAR(50) NOT NULL PRIMARY KEY,
    account_number VARCHAR(20) UNIQUE,
    name VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(50),
    country VARCHAR(50),
    account_type ENUM('Checking', 'Savings', 'Business'),
    is_business TINYINT(1),
    business_category VARCHAR(100),
    created_at DATETIME,
    risk_level VARCHAR(10) DEFAULT 'low',
    risk_score DECIMAL(10,2) DEFAULT 0.00
);
CREATE TABLE accounts (
    unique_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    account_number VARCHAR(50),
    json_data JSON,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trans_num ON sentrymind_transactions (transaction_id);
CREATE INDEX idx_cust_id ON sentrymind_transactions (customer_id);
CREATE INDEX idx_merchant ON sentrymind_transactions (merchant_name);	
CREATE INDEX idx_city ON sentrymind_transactions (merchant_city);	
CREATE INDEX idx_trans_date ON sentrymind_transactions (transaction_date);	
CREATE INDEX idx_trans_fraud_date_cust 
ON sentrymind_transactions(fraud_type, transaction_date, customer_id, transaction_amount);
