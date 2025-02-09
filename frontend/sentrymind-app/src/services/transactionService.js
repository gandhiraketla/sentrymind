const BASE_URL = 'http://localhost:8000';

export const fetchTransactions = async (pageNumber, pageSize, startDate, endDate) => {
  try {
    const response = await fetch(`${BASE_URL}/fraudulent-transactions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        page_number: pageNumber,
        page_size: pageSize,
        start_date: startDate,
        end_date: endDate
      }),
    });
    return await response.json();
  } catch (error) {
    console.error('Error fetching transactions:', error);
    throw error;
  }
};

export const analyzeTransaction = async (customerId) => {
  try {
    const response = await fetch(`${BASE_URL}/analyze-transaction/${customerId}`);
    return await response.json();
  } catch (error) {
    console.error('Error analyzing transaction:', error);
    throw error;
  }
};