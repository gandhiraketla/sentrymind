import xgboost as xgb
import pandas as pd
import json
import os

class FraudDetectionAgent:
    def __init__(self, model_path="fraud_detection_model_new.bin"):
        """Load the trained fraud detection model."""
        self.model = xgb.Booster()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "fraud_detection_model_new.bin")
        self.model.load_model(model_path)
        self.fraud_labels = [
            "Legitimate Transaction",
            "Frequent Offshore Transfers",
            "Layering",
            "Structuring",
            "Rapid In-Out",
            "Large Wire Transfer",
        ]

    def preprocess_transaction(self, transaction):
        """Convert transaction details into model input format."""
        return {
            "real_transaction_amount": transaction["transaction_amount"],
            "num_transactions_last_30d": transaction["transaction_frequency"],
            "num_large_transactions_30d": 1 if transaction["transaction_amount"] > 9000 else 0,
            "num_layering_attempts_30d": 1 if transaction["transaction_type"] == "Wire Transfer" else 0,
            "velocity_score": abs(transaction["account_balance_after"] - transaction["account_balance_before"]),
            "country_risk_score": 5 if transaction["destination_country"] in ["Panama", "Cayman Islands", "Switzerland"] else 1,
            "transaction_amount_change_rate": 0,  # Placeholder: Implement if needed
            "is_transaction_between_5000_and_9000": 1 if 5000 <= transaction["transaction_amount"] <= 9000 else 0,
            "is_dest_cayman_islands": 1 if transaction["destination_country"] == "Cayman Islands" else 0,
            "is_dest_switzerland": 1 if transaction["destination_country"] == "Switzerland" else 0,
            "is_dest_panama": 1 if transaction["destination_country"] == "Panama" else 0,
        }


    def predict_fraud_type(self, transaction):
        """Predict fraud type for a given transaction."""
        df_input = pd.DataFrame([self.preprocess_transaction(transaction)])
        dinput = xgb.DMatrix(df_input)

        y_pred = self.model.predict(dinput)
        predicted_label = self.fraud_labels[int(y_pred[0])]

        return predicted_label

    def process_transactions(self, input_json):
        """Process recent transactions and append fraud predictions."""
        transactions = input_json["recentTransactions"]

        for transaction in transactions:
            transaction["predicted_fraud_type"] = self.predict_fraud_type(transaction)

        return input_json


# ✅ **Test the Class with Sample Input**
if __name__ == "__main__":
    # Load sample input JSON
    input_json = {
        "customerInfo": {
            "customer_id": "42e60d56-b222-4c67-9432-cfab2520fde0",
            "account_number": "1125218191",
            "name": "Brett Johnson",
            "address": "563 Nunez Locks\nLake Hunterview, MO 87868",
            "city": "Benjaminburgh",
            "country": "Panama",
            "account_type": "Checking",
            "is_business": 0,
            "business_category": None,
            "created_at": "2024-10-12 12:47:01",
            "risk_level": "medium",
            "risk_score": 50.0,
        },
        "fraudStats": {
            "total_fraud_transactions": 10,
            "total_fraud_amount": 106990.0,
        },
        "recentTransactions": [
            {
                "transaction_id": "TXN_51e8448fa0934eaab399a28449b46d4e",
                "transaction_date": "2025-02-01 15:38:47",
                "transaction_amount": 1921.48,
                "transaction_type": "Card Payment",
                "merchant_category": "Entertainment",
                "destination_country": "Panama",
                "transaction_frequency": 6,
                "account_balance_before": 28833.7,
                "account_balance_after": 30755.2,
                "is_fraud": 0,
            },
            {
                "transaction_id": "TXN_82e26da418d3460db0bf2a229e9b2bf3",
                "transaction_date": "2025-01-31 13:37:33",
                "transaction_amount": 13156.3,
                "transaction_type": "Wire Transfer",
                "merchant_category": "Utilities",
                "destination_country": "Cayman Islands",
                "transaction_frequency": 8,
                "account_balance_before": 78670.1,
                "account_balance_after": 65513.8,
                "is_fraud": 1,
            },
            {
            "transaction_id": "TXN_84e33231db1d4d0cb515dea78f20995e",
            "transaction_date": "2025-01-30 15:40:08",
            "transaction_amount": 223.04,
            "transaction_type": "Card Payment",
            "merchant_category": "Entertainment",
            "destination_country": "Panama",
            "transaction_frequency": 2,
            "account_balance_before": 28833.7,
            "account_balance_after": 29056.7,
            "is_fraud": 0
            },
            {
            "transaction_id": "TXN_d0778bf74efb4ea69dd7ea62a115347c",
            "transaction_date": "2025-01-29 16:37:33",
            "transaction_amount": 9697.62,
            "transaction_type": "Wire Transfer",
            "merchant_category": "Education",
            "destination_country": "Cayman Islands",
            "transaction_frequency": 4,
            "account_balance_before": 88367.7,
            "account_balance_after": 78670.1,
            "is_fraud": 1
            },
            {
            "transaction_id": "TXN_a3f6b8abe4854710ba2240d348c7adf3",
            "transaction_date": "2025-01-27 16:37:33",
            "transaction_amount": 13245.6,
            "transaction_type": "Wire Transfer",
            "merchant_category": "Restaurant",
            "destination_country": "Panama",
            "transaction_frequency": 8,
            "account_balance_before": 101613.0,
            "account_balance_after": 88367.7,
            "is_fraud": 1
            },
            {
            "transaction_id": "TXN_633ae03a24814219b2bbdbfc4dbad8b5",
            "transaction_date": "2025-01-25 01:37:33",
            "transaction_amount": 9291.03,
            "transaction_type": "Wire Transfer",
            "merchant_category": "Travel",
            "destination_country": "Cayman Islands",
            "transaction_frequency": 8,
            "account_balance_before": 110904.0,
            "account_balance_after": 101613.0,
            "is_fraud": 1
            },
            {
            "transaction_id": "TXN_652e81b160bd42bc86efcff6569d81f9",
            "transaction_date": "2025-01-24 15:35:55",
            "transaction_amount": 24799.7,
            "transaction_type": "Wire Transfer",
            "merchant_category": "Restaurant",
            "destination_country": "Panama",
            "transaction_frequency": 9,
            "account_balance_before": 28833.7,
            "account_balance_after": 53633.4,
            "is_fraud": 0
            },
            {
            "transaction_id": "TXN_37ec67e02fc24b3e89ae868a010b71f3",
            "transaction_date": "2025-01-23 15:44:02",
            "transaction_amount": 3640.38,
            "transaction_type": "Cash Deposit",
            "merchant_category": "Utilities",
            "destination_country": "Panama",
            "transaction_frequency": 2,
            "account_balance_before": 28833.7,
            "account_balance_after": 32474.1,
            "is_fraud": 0
            },
            {
            "transaction_id": "TXN_9214f80b85554df293ebe6243226ecea",
            "transaction_date": "2025-01-22 15:35:21",
            "transaction_amount": 2857.69,
            "transaction_type": "Cash Deposit",
            "merchant_category": "Education",
            "destination_country": "Panama",
            "transaction_frequency": 1,
            "account_balance_before": 28833.7,
            "account_balance_after": 31691.4,
            "is_fraud": 0
            },
            {
            "transaction_id": "TXN_a10a25dd8e2842cead647e6b54e8fac3",
            "transaction_date": "2025-01-21 15:37:33",
            "transaction_amount": 6602.3,
            "transaction_type": "Wire Transfer",
            "merchant_category": "Automotive",
            "destination_country": "Panama",
            "transaction_frequency": 4,
            "account_balance_before": 117507.0,
            "account_balance_after": 110904.0,
            "is_fraud": 1
            }
        ],
    }

    # Initialize the fraud detection agent
    agent = FraudDetectionAgent()

    # Process transactions and get updated JSON
    updated_json = agent.process_transactions(input_json)

    # Print the updated JSON with predictions
    print(json.dumps(updated_json, indent=4))
