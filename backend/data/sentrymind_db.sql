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

CREATE INDEX idx_trans_num ON sentrymind_transactions (transaction_id);
CREATE INDEX idx_cust_id ON sentrymind_transactions (customer_id);
CREATE INDEX idx_merchant ON sentrymind_transactions (merchant_name);	
CREATE INDEX idx_city ON sentrymind_transactions (merchant_city);	
CREATE INDEX idx_trans_date ON sentrymind_transactions (transaction_date);	
CREATE INDEX idx_trans_fraud_date_cust 
ON sentrymind_transactions(fraud_type, transaction_date, customer_id, transaction_amount);
