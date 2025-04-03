  // Function to update the transactions by polling the API endpoint and filter by date
  function updateTransactions() {
    fetch("{{ url_for('customer.get_transactions', account_id=account.AccountID) }}")
      .then(response => response.json())
      .then(data => {
         // If the API returns a combined list, use it; otherwise combine separate lists.
         const transactions = data.transactions || [
           ...(data.current_transactions || []),
           ...(data.past_transactions || [])
         ];
         
         // Define today's date and calculate the date for 30 days ago.
         const today = new Date();
         const thirtyDaysAgo = new Date();
         thirtyDaysAgo.setDate(today.getDate() - 30);
         
         // Filter transactions: current transactions are those with a date within the last 30 days.
         const currentTxns = transactions.filter(txn => {
           const txnDate = new Date(txn.TransDate);
           return txnDate >= thirtyDaysAgo;
         });
         
         // Past transactions are any with a date older than 30 days.
         const pastTxns = transactions.filter(txn => {
           const txnDate = new Date(txn.TransDate);
           return txnDate < thirtyDaysAgo;
         });
         
         // Update current transactions section
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
         
         // Update past transactions section
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