import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import Reports from './components/Reports';
import TransactionTable from './components/TransactionTable';

const AILogo = () => (
  <svg className="w-10 h-10" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
    <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" strokeWidth="2" className="text-white" />
    <path d="M15,25 L35,25" stroke="currentColor" strokeWidth="2" className="text-white" />
    <path d="M25,15 L25,35" stroke="currentColor" strokeWidth="2" className="text-white" />
    <circle cx="25" cy="25" r="5" fill="currentColor" className="text-white">
      <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite" />
    </circle>
    <circle cx="25" cy="25" r="12" fill="none" stroke="currentColor" strokeWidth="1" className="text-white">
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
    <div className="fixed top-0 left-0 right-0 z-10">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 opacity-95"></div>
      
      <div className="relative">
        <div className="flex justify-between items-center h-16 px-6">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center p-2 rounded-lg bg-white/20">
              <AILogo />
            </div>
            <div className="flex flex-col">
              <span className="text-2xl font-bold text-white">
                SentryMind
              </span>
              <span className="text-xs text-blue-100">
                Fraud Analysis Platform
              </span>
            </div>
          </div>
          
          <div className="flex items-center">
            <div className="flex items-center space-x-2 bg-white/20 px-4 py-2 rounded-lg border border-white/20 text-white">
              <Clock className="w-5 h-5" />
              <div className="flex flex-col">
                <span className="text-sm font-medium">
                  {currentDateTime.toLocaleTimeString()}
                </span>
                <span className="text-xs opacity-80">
                  {currentDateTime.toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-200/30 to-transparent"></div>
      </div>
    </div>
  );
};

const Sidebar = ({ currentView, setCurrentView }) => {
  return (
    <div className="fixed top-16 left-0 bottom-0 w-64 bg-white border-r border-gray-200 shadow-sm">
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