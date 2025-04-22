document.addEventListener("DOMContentLoaded", () => {
  function updateTransactions() {
    console.log("Updating transactions...");
    const currentList = document.getElementById("current-transactions-list");
    const pastList = document.getElementById("past-transactions-list");

    // If transaction containers are missing, there's nothing to update
    if (!currentList || !pastList) {
      console.log("Transaction containers not found, skipping update");
      return;
    }

    const url = `/api/transactions/${window.accountId}`;
    console.log(`Fetching transactions from: ${url}`);

    fetch(url)
      .then(res => res.json())
      .then(data => {
        currentList.innerHTML = "";
        pastList.innerHTML = "";

        if (data.error) {
          console.error(`Transaction error: ${data.error}`);
          currentList.innerHTML = `<li>Error: ${data.error}</li>`;
          pastList.innerHTML = `<li>Error: ${data.error}</li>`;
          return;
        }

        const addItems = (list, transactions) => {
          if (!transactions.length) {
            list.innerHTML = "<li>No transactions</li>";
            return;
          }
          
          console.log(`Adding ${transactions.length} transactions to list`);
          
          for (const tx of transactions) {
            const li = document.createElement("li");
            li.classList.add("transaction-item");
            
            // Add payment-specific classes for styling
            const isPayment = tx.description.toLowerCase().includes('payment') || 
                              tx.description.toLowerCase().includes('bill');
            
            if (isPayment) {
              li.classList.add("payment-transaction");
            }

            const dateSpan = document.createElement("span");
            dateSpan.classList.add("transaction-date");
            dateSpan.textContent = tx.TransDate;

            const descSpan = document.createElement("span");
            descSpan.classList.add("transaction-desc");
            descSpan.textContent = tx.description;

            const amountSpan = document.createElement("span");
            amountSpan.classList.add("transaction-amount");
            amountSpan.textContent = `$${tx.amount.toFixed(2)}`;
            
            // Add debit/credit classes for styling
            const isDebit = isPayment || 
                          tx.description.toLowerCase().includes('withdraw') || 
                          tx.description.toLowerCase().includes('transfer to');
                          
            if (isDebit) {
              amountSpan.classList.add("debit-amount");
            } else {
              amountSpan.classList.add("credit-amount");
            }

            li.appendChild(dateSpan);
            li.appendChild(descSpan);
            li.appendChild(amountSpan);
            list.appendChild(li);
          }
        };

        addItems(currentList, data.current_transactions);
        addItems(pastList, data.past_transactions);
        
        // After updating transactions, also update the account balance
        // by triggering the balance update function if it exists
        if (typeof updateMinBillDue === 'function') {
          console.log("Triggering balance update after transactions refresh");
          updateMinBillDue();
        }
      })
      .catch(err => {
        console.error("Error loading transactions:", err);
      });
  }

  // Run immediately and set interval
  updateTransactions();
  setInterval(updateTransactions, 10000);
});