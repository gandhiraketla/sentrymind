
from typing import Annotated, Any, Dict, List, Tuple, TypedDict
import operator
import os
import sys
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import Graph, MessageGraph
from langgraph.prebuilt.tool_executor import ToolExecutor
import json
import logging
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
# Add parent directory to system path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from util.envutils import EnvUtils
from tools.agent_tools import AgentTools
from tools.database_manager import DatabaseManager
from model.fraud_detection import FraudDetectionAgent
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transaction_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TransactionAnalysis")

class TransactionAnalyzer:
    def __init__(self):
        self.env_utils = EnvUtils()
        self.model_type = self.env_utils.get_required_env("MODEL_TYPE").lower()
        logger.info(f"Initialized with model type: {self.model_type}")
        self.api_key = self.env_utils.get_required_env("OPENAI_API_KEY")
        self.model=SentenceTransformer("intfloat/multilingual-e5-large")
        self.langchain_embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        self.index_name = self.env_utils.get_required_env("PINECONE_INDEX") 
        self.pinecone_api_key = self.env_utils.get_required_env("PINECONE_API_KEY")
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.index = self.pc.Index(self.index_name)
        self.vectorstore = PineconeVectorStore(
            index=self.index,
            embedding=self.langchain_embeddings,
            text_key="text"
        )
        
    def get_llm(self):
        """Get the appropriate LLM based on environment configuration"""
        if self.model_type == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model="mistral",
                temperature=0
            )
        else:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4",
                temperature=0
            )

    def get_transaction_details(self, state: Dict) -> Dict:
        """Get transaction details from database"""
        logger.debug("Entering get_transaction_details")
        try:
            last_message = state["messages"][-1]
            if isinstance(last_message, HumanMessage):
                customer_id = last_message.content.strip()
                logger.info(f"Processing transaction number: {customer_id}")
                db_manager = DatabaseManager()
                result = db_manager.getCustomerDetails(customer_id)
                #logger.debug(f"Database query result: {json.dumps(result, indent=2)}")
                logger.info("Successfully updated state with transaction details")
            
            return result
        except Exception as e:
            logger.error(f"Error in get_transaction_details: {str(e)}", exc_info=True)
            raise

    def predict_fraud(self, state: Dict) -> Dict:
        """Analyze the transaction data"""
        logger.debug("Entering analyze_transaction")
        try:
           #print(state)
           parsed_json = json.loads(state)
           #parsed_json=json.dumps(parsed_json, indent=3)
           #print(json.dumps(parsed_json, indent=3))
           agent = FraudDetectionAgent()
           updated_json = agent.process_transactions(parsed_json)
           return updated_json
        except Exception as e:
            logger.error(f"Error in analyze_transaction: {str(e)}", exc_info=True)
            raise
    def analyze_transaction(self, state: Dict) -> Dict:
        """Analyze the transaction data"""
        logger.debug("Entering analyze_transaction")
        try:
           
           #state=self.redact_sensitive_data(state)
           parsed_json = json.dumps(state, indent=3)
           #print(parsed_json)
           fraud_types=self.extract_predicted_fraud_types(state)
           #print(fraud_types)
           document_chunks=self.get_document_chunks(fraud_types)
           #print(document_chunks)
           analysis_prompt = PromptTemplate.from_template(
                """Analyze the provided transactions based on the additional context retrieved from compliance documents.
                
                Transactions JSON:
                {transaction_json}
                
                Retrieved Document Chunks:
                {document_chunks}
                
                Instructions:
                - Carefully review each transaction in the JSON.
                - Provide an analysis for each transaction based only on the provided context.
                - Ensure your response is in the same JSON format as the input, with an additional key "llm_analysis" added to each transaction containing your analysis.
                - Provide overall analysis of all transactions.Attach the analysis to the JSON with key "overall_analysis".
                - Provide final SAR Reporting required Yes/No. Attach the analysis to the JSON with key "final_sar_required".
                - You MUST return all the transactions in the JSON
                - You MUST return a well-formatted JSON response
                - You MUST not change the JSON input provided, just append your analysis to same JSON
                
                
                Begin your response with the updated JSON:
                """
    )
           self.llm= self.get_llm()
           evaluation_chain = analysis_prompt | self.llm
           eval_input = {
            "transaction_json": parsed_json,
            "document_chunks": document_chunks
          }
           evaluation_result = evaluation_chain.invoke(eval_input)
           evaluation_response = evaluation_result.content.strip()
           db_manager = DatabaseManager()
           db_manager.saveSARReport(evaluation_response)
           print(f"LLM evaluation response: {evaluation_response}")
           return evaluation_response
        except Exception as e:
            logger.error(f"Error in analyze_transaction: {str(e)}", exc_info=True)
            raise
    
    def extract_predicted_fraud_types(self,transaction_json):
        predicted_fraud_types = set()  # Use a set to avoid duplicates
        for transaction in transaction_json["recentTransactions"]:
            fraud_type = transaction.get("predicted_fraud_type")
            if fraud_type:
                predicted_fraud_types.add(fraud_type)
        return list(predicted_fraud_types)
    def get_document_chunks(self,fraud_types):
        document_chunks = []
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        for fraud_type in fraud_types:
            for source in ["AML & KYC Compliance Reports", 
                       "Internal Fraud Investigation Playbook"
                       ]:
            
                query_string = f"{source} on {fraud_type}"
                retrieved_docs  = self.vectorstore.similarity_search(query_string, k=5)
                for i, doc in enumerate(retrieved_docs, 1):
                    document_chunks.append(doc.page_content)
        return document_chunks
    
   

    def redact_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive information from the transaction data using Presidio
        """
        logger.debug("Entering redact_sensitive_data")
        try:
            # Initialize Presidio engines
            analyzer = AnalyzerEngine()
            anonymizer = AnonymizerEngine()
            
            def process_string(text: str) -> str:
                """Process a single string value to redact PII"""
                try:
                    # Analyze text for PII
                    analyzer_results = analyzer.analyze(
                        text=text,
                        language='en',
                        entities=[
                            "PERSON", 
                            "CREDIT_CARD", 
                            "PHONE_NUMBER", 
                            "EMAIL_ADDRESS", 
                            "US_SSN", 
                            "US_BANK_NUMBER"
                        ]
                    )
                    
                    # Only anonymize if PII is found
                    if analyzer_results:
                        return anonymizer.anonymize(
                            text=text,
                            analyzer_results=analyzer_results
                        ).text
                    return text
                except:
                    return text
            
            def process_value(value):
                """Process any value, handling different types appropriately"""
                if isinstance(value, str):
                    return process_string(value)
                elif isinstance(value, list):
                    return [process_value(item) for item in value]
                elif isinstance(value, dict):
                    return {k: process_value(v) for k, v in value.items()}
                return value
                
            # Process the entire dictionary
            redacted_data = process_value(data)
            return redacted_data
            
        except Exception as e:
            logger.error(f"Error in redact_sensitive_data: {str(e)}", exc_info=True)
            return data  # Return original data if redaction fails
    def create_workflow(self):
        """Create the LangGraph workflow"""
        logger.debug("Creating workflow")
        try:
            workflow = Graph()
            
            workflow.add_node("get_transaction", self.get_transaction_details)
            workflow.add_node("predict_fraud", self.predict_fraud)
            workflow.add_node("analyze", self.analyze_transaction)
            workflow.add_edge("get_transaction", "predict_fraud")
            workflow.add_edge("predict_fraud", "analyze")
            workflow.set_entry_point("get_transaction")
            return workflow.compile()
        except Exception as e:
            logger.error(f"Error in create_workflow: {str(e)}", exc_info=True)
            raise

    def process_transaction(self, transaction_number: str) -> str:
        """Process a transaction and return the final AI-generated message."""
        logger.info(f"Processing transaction: {transaction_number}")
        try:
            workflow = self.create_workflow()
            state = {
                "messages": [HumanMessage(content=transaction_number)],
                "next": ""
            }
            
            all_outputs = list(workflow.stream(state))
            #logger.info(f"All outputs: {all_outputs}")

            # Iterate through all_outputs to find the 'analyze' result
            final_message = "Processed all Transactions"
            #logger.info(f"Final AI-generated message: {final_message}")
            
            return final_message
            
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}", exc_info=True)
            raise

 
def main():
    """Test function"""
    analyzer = TransactionAnalyzer()
    result = analyzer.process_transaction("42e60d56-b222-4c67-9432-cfab2520fde0")
   
if __name__ == "__main__":
    main()
