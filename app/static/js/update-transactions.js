// Function to update the transactions by polling the API endpoint and filter by date
function updateTransactions() {
  if (typeof transactionApiUrl === "undefined") {
    console.error("transactionApiUrl is not defined");
    return;
  }

  fetch(transactionApiUrl)
    .then(response => response.json())
    .then(data => {
      const transactions = data.transactions || [
        ...(data.current_transactions || []),
        ...(data.past_transactions || [])
      ];

      const today = new Date();
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(today.getDate() - 30);

      const currentTxns = transactions.filter(txn => {
        const txnDate = new Date(txn.TransDate);
        return txnDate >= thirtyDaysAgo;
      });

      const pastTxns = transactions.filter(txn => {
        const txnDate = new Date(txn.TransDate);
        return txnDate < thirtyDaysAgo;
      });

      const currentContainer = document.getElementById('current-transactions-list');
      if (currentTxns.length > 0) {
        currentContainer.innerHTML = currentTxns
          .map(txn => `
            <li class="transaction-item">
              <div class="transaction-date">${txn.TransDate}</div>
              <div class="transaction-info">${txn.description} - $${parseFloat(txn.amount).toFixed(2)}</div>
            </li>
          `)
          .join('');
      } else {
        currentContainer.innerHTML = '<p>No current transactions available.</p>';
      }

      const pastContainer = document.getElementById('past-transactions-list');
      if (pastTxns.length > 0) {
        pastContainer.innerHTML = pastTxns
          .map(txn => `
            <li class="transaction-item">
              <div class="transaction-date">${txn.TransDate}</div>
              <div class="transaction-info">${txn.description} - $${parseFloat(txn.amount).toFixed(2)}</div>
            </li>
          `)
          .join('');
      } else {
        pastContainer.innerHTML = '<p>No past transactions available.</p>';
      }
    })
    .catch(error => console.error('Error fetching transactions:', error));
}

// Call on page load and then every 10 seconds
updateTransactions();
setInterval(updateTransactions, 10000);
