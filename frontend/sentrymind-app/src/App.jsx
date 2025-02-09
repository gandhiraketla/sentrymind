import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import Reports from './components/Reports';
import TransactionTable from './components/TransactionTable';

const AILogo = () => (
  <svg className="w-10 h-10" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
    <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" strokeWidth="2" className="text-blue-600" />
    <path d="M15,25 L35,25" stroke="currentColor" strokeWidth="2" className="text-blue-600" />
    <path d="M25,15 L25,35" stroke="currentColor" strokeWidth="2" className="text-blue-600" />
    <circle cx="25" cy="25" r="5" fill="currentColor" className="text-blue-600">
      <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite" />
    </circle>
    <circle cx="25" cy="25" r="12" fill="none" stroke="currentColor" strokeWidth="1" className="text-blue-600">
      <animate attributeName="r" values="12;14;12" dur="2s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite" />
    </circle>
  </svg>
);

const Header = () => {
  const [currentDateTime, setCurrentDateTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 z-10 bg-gradient-to-r from-blue-50 to-blue-100 border-b border-blue-200">
      <div className="flex justify-between items-center h-16 px-4">
        <div className="flex items-center space-x-3">
          <div className="flex items-center justify-center">
            <AILogo />
          </div>
          <div className="flex flex-col">
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-blue-800">
              SentryMind
            </span>
            <span className="text-xs text-blue-600">Fraud Analysis Platform</span>
          </div>
        </div>
        <div className="flex items-center space-x-2 bg-white/80 px-4 py-2 rounded-lg border border-blue-200">
          <Clock className="w-5 h-5 text-blue-600" />
          <span className="text-blue-800">
            {currentDateTime.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
};

const Sidebar = ({ currentView, setCurrentView }) => {
  return (
    <div className="fixed top-16 left-0 bottom-0 w-64 bg-blue-50 border-r border-blue-200">
      <nav className="h-full p-4">
        <ul className="space-y-2">
          <li>
            <a 
              href="#" 
              onClick={(e) => {
                e.preventDefault();
                setCurrentView('transactions');
              }}
              className={`flex items-center space-x-2 py-2 px-4 hover:bg-white hover:shadow-sm rounded-lg transition-all duration-150 group ${
                currentView === 'transactions' ? 'bg-white' : ''
              }`}
            >
              <div className="w-1 h-8 rounded bg-blue-600 opacity-0 group-hover:opacity-100 transition-opacity absolute left-0"></div>
              <span className="text-sm font-medium group-hover:text-blue-600">Transactions</span>
            </a>
          </li>
          <li>
            <a 
              href="#" 
              onClick={(e) => {
                e.preventDefault();
                setCurrentView('reports');
              }}
              className={`flex items-center space-x-2 py-2 px-4 hover:bg-white hover:shadow-sm rounded-lg transition-all duration-150 group ${
                currentView === 'reports' ? 'bg-white' : ''
              }`}
            >
              <div className="w-1 h-8 rounded bg-blue-600 opacity-0 group-hover:opacity-100 transition-opacity absolute left-0"></div>
              <span className="text-sm font-medium group-hover:text-blue-600">Reports</span>
            </a>
          </li>
        </ul>
      </nav>
    </div>
  );
};

const MainContent = ({ currentView }) => {
  return (
    <div className="fixed top-16 left-64 right-0 bottom-0 bg-gray-100 overflow-auto">
      {currentView === 'transactions' ? (
        <TransactionTable />
      ) : (
        <Reports />
      )}
    </div>
  );
};

const App = () => {
  const [currentView, setCurrentView] = useState('transactions');

  return (
    <div className="h-screen w-screen overflow-hidden">
      <Header />
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
      <MainContent currentView={currentView} />
    </div>
  );
};

export default App;