import React, { useState, useEffect } from 'react';

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedTab, setExpandedTab] = useState(null);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/reports');
      const data = await response.json();
      setReports(data);
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const TransactionTable = ({ transactions }) => (
    <div className="overflow-x-auto mt-4">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fraud Type</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Analysis</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {transactions.map((txn) => (
            <tr key={txn.transaction_id}>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {new Date(txn.transaction_date).toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {txn.transaction_type}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${txn.transaction_amount.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  txn.is_fraud 
                    ? 'bg-red-100 text-red-800' 
                    : 'bg-green-100 text-green-800'
                }`}>
                  {txn.is_fraud ? 'Fraud' : 'Legitimate'}
                </span>
              </td>
              <td className="px-6 py-4 text-sm text-gray-500">
                {txn.predicted_fraud_type}
              </td>
              <td className="px-6 py-4 text-sm text-gray-500">
                {txn.llm_analysis}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Fraud Analysis Reports</h2>
      
      {loading ? (
        <div className="w-full h-2 bg-gray-200 rounded overflow-hidden">
          <div className="h-full bg-blue-600 animate-[loading_1s_ease-in-out_infinite]" style={{width: '100%'}}></div>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div key={report.unique_id} className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => setExpandedTab(expandedTab === report.unique_id ? null : report.unique_id)}
                className="w-full px-6 py-4 text-left bg-white hover:bg-gray-50 flex justify-between items-center"
              >
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    {report.json_data.customerInfo.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    Account: {report.account_number}
                  </p>
                </div>
                <svg
                  className={`w-5 h-5 transform transition-transform ${
                    expandedTab === report.unique_id ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {expandedTab === report.unique_id && (
                <div className="px-6 py-4 bg-gray-50">
                  <div className="mb-6">
                    <h4 className="text-lg font-medium text-gray-900 mb-2">Overall Analysis</h4>
                    <p className="text-gray-700">{report.json_data.overall_analysis}</p>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg mb-4">
                    <h4 className="text-md font-medium text-gray-900 mb-2">Fraud Statistics</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">Total Fraud Amount</p>
                        <p className="text-lg font-medium text-gray-900">
                          ${report.json_data.fraudStats.total_fraud_amount.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Total Fraud Transactions</p>
                        <p className="text-lg font-medium text-gray-900">
                          {report.json_data.fraudStats.total_fraud_transactions}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-lg font-medium text-gray-900 mb-4">Recent Transactions</h4>
                    <TransactionTable transactions={report.json_data.recentTransactions} />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Reports;