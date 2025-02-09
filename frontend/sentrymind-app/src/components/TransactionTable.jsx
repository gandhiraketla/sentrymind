import React, { useState } from 'react';
import { fetchTransactions, analyzeTransaction } from '../services/transactionService';

const TransactionTable = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [pageSize] = useState(10);
  const [analysisMessage, setAnalysisMessage] = useState('')

  const handleSearch = async () => {
    setLoading(true);
    try {
      const data = await fetchTransactions(currentPage, pageSize, startDate, endDate);
      console.log('API Response:', data); // Add this to see the full response
      console.log('Transactions:', data.data); // Add this to see the transactions array
      setTransactions(data.customers || []);
      setTotalRecords(data.pagination?.total_records || 0);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (customerId) => {
    setAnalyzing(customerId);
    try {
      console.log('Analyzing customer:', customerId);
      const data = await analyzeTransaction(customerId);
      setAnalysisMessage('Analysis completed and report generated');
      setTimeout(() => {
        setAnalysisMessage('');
      }, 9000);
      console.log('Analysis result:', data);
      // Handle the analysis result as needed
    } finally {
      setAnalyzing('');
    }
  };

  const totalPages = Math.ceil(totalRecords / pageSize);

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-700 mb-6">Analytics Dashboard</h2>
      <div className="flex space-x-4 items-end mb-8">
        <div className="flex flex-col space-y-2">
          <label className="text-sm text-gray-600">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="bg-white border border-gray-200 text-gray-700 rounded-lg p-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </div>
        <div className="flex flex-col space-y-2">
          <label className="text-sm text-gray-600">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="bg-white border border-gray-200 text-gray-700 rounded-lg p-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </div>
        <button 
          onClick={handleSearch}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-150 disabled:bg-blue-400"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      {analysisMessage && (
        <div className="mb-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
        <span className="flex items-center">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
            </svg>
            {analysisMessage}
        </span>
        </div>
    )}
      {loading && (
        <div className="w-full h-2 bg-gray-200 rounded overflow-hidden">
          <div className="h-full bg-blue-600 animate-[loading_1s_ease-in-out_infinite]" style={{width: '100%'}}></div>
        </div>
      )}

      {!loading && transactions.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Account Number</th>
                  <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Account Type</th>
                  <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Fraud Transactions</th>
                  <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Fraud Amount</th>
                  <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((transaction) => (
                  <tr key={transaction.customer_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{transaction.account_number}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{transaction.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{transaction.account_type}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{transaction.total_fraud_transactions}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${transaction.total_fraud_amount.toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <button
                        onClick={() => handleAnalyze(transaction.customer_id)}
                        disabled={analyzing === transaction.customer_id}
                        className="bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200 transition-colors duration-150"
                      >
                        {analyzing === transaction.customer_id ? (
                          <div className="w-16 h-4 relative">
                            <div className="absolute inset-0 bg-blue-200 rounded">
                              <div className="h-full bg-blue-400 rounded animate-[loading_1s_ease-in-out_infinite]" style={{width: '100%'}}></div>
                            </div>
                          </div>
                        ) : 'Analyze'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing page {currentPage} of {totalPages}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  setCurrentPage(prev => Math.max(prev - 1, 1));
                  handleSearch();
                }}
                disabled={currentPage === 1}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
              >
                Previous
              </button>
              <button
                onClick={() => {
                  setCurrentPage(prev => Math.min(prev + 1, totalPages));
                  handleSearch();
                }}
                disabled={currentPage === totalPages}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TransactionTable;