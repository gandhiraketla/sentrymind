from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
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
from datetime import datetime
from tools.database_manager import DatabaseManager
from agents.agent_manager import TransactionAnalyzer  # Assuming this exists
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize database manager and analyzer
db_manager = DatabaseManager()
analyzer = TransactionAnalyzer()


# API Model for Query Parameters
class FraudTransactionQuery(BaseModel):
    page_number: int = Query(1, ge=1, description="Page number for pagination")
    page_size: int = Query(10, ge=1, le=100, description="Number of records per page")
    start_date: Optional[str] = None  # Date format: YYYY-MM-DD HH:MM:SS
    end_date: Optional[str] = None  # Date format: YYYY-MM-DD HH:MM:SS


@app.post("/fraudulent-transactions")
async def get_fraudulent_transactions(query: FraudTransactionQuery):
    """
    Endpoint to get customers with fraudulent transactions within a given date range.
    Supports pagination with page number and page size.
    """
    try:
        if not query.start_date or not query.end_date:
            raise HTTPException(status_code=400, detail="Both start_date and end_date are required.")
            
        # Invoke db_manager method
        print(query.start_date)
        print(query.end_date)
        result = db_manager.get_customers_with_fraudulent_transactions(
            page_number=query.page_number,
            page_size=query.page_size,
            start_date=query.start_date,
            end_date=query.end_date
        )
        print(result)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze-transaction/{customer_id}")
async def analyze_transaction(customer_id: str):
    """
    Endpoint to analyze a transaction for a specific customer ID.
    """
    try:
        result = analyzer.process_transaction(customer_id)
        return {"customer_id": customer_id, "analysis_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/")
async def get_reports():
    """
    Endpoint to analyze a transaction for a specific customer ID.
    """
    try:
        result = db_manager.getReports()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
