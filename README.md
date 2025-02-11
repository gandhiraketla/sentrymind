# SentryMind

SentryMind is an advanced monitoring and compliance system designed to help organizations maintain regulatory compliance and detect potential financial crimes. It leverages AI and machine learning to analyze documents, monitor transactions, and provide real-time insights for better risk management.

## Prerequisites

- MySQL Database
- Python 3.8 or higher
- Node.js and npm
- Git

## Installation and Setup

### 1. Database Setup

1. Install MySQL database on your system
2. Clone the repository:
   ```bash
   git clone https://github.com/gandhiraketla/sentrymind.git
   ```
3. Navigate to the database scripts folder:
   ```bash
   cd sentrymind\backend\data
   ```
4. Run the database initialization script:
   ```bash
   mysql -u your_username -p < sentrymind_db.sql
   ```

### 2. Backend Setup

1. Navigate to the project root:
   ```bash
   cd C:\sentrymind
   ```

2. Create and activate Python virtual environment:
   ```bash
   python -m venv env
   .\env\Scripts\activate  # For Windows
   source env/bin/activate # For Unix/MacOS
   ```

3. Create `.env` file in the backend folder with the following properties:
   ```plaintext
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_INDEX=guidelines
   LOCAL_FOLDER_MONITOR_PATH=<Path to your synthetic internal company docs and FATF docs>
   PINECONE_API_KEY=
   MODEL_TYPE=openai/ollama
   DB_HOST=your_db_host
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=your_db_name
   ```

### 3. Data Initialization

1. Initialize document storage:
   ```bash
   cd sentrymind\backend
   python main.py
   ```
   After running, add your internal company synthetic docs to the `LOCAL_FOLDER_MONITOR_PATH`. This will index all documents in Pinecone.

2. Generate synthetic data:
   ```bash
   cd backend\data
   python synthetic_customer_data.py
   python synthetic_data_generator.py
   ```
   
   Optionally, to retrain the model:
   ```bash
   python synthetic_train_data.py
   ```

### 4. Starting the Application

1. Start the backend API server:
   ```bash
   cd sentrymind\backend\api
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. Start the frontend development server:
   ```bash
   cd sentrymind\frontend\sentrymind-app
   npm run dev
   ```

3. Access the application:
   Open your browser and navigate to [http://localhost:5173/#](http://localhost:5173/#)

## Contributing

Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.