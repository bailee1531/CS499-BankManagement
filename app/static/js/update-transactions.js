function updateTransactions() {
  const url = `/api/transactions/${window.accountId}`;

  fetch(url)
    .then(res => res.json())
    .then(data => {
      const currentList = document.getElementById("current-transactions-list");
      const pastList = document.getElementById("past-transactions-list");

      currentList.innerHTML = ""; // Clear loading message
      pastList.innerHTML = "";

      if (data.error) {
        currentList.innerHTML = `<li>Error: ${data.error}</li>`;
        pastList.innerHTML = `<li>Error: ${data.error}</li>`;
        return;
      }

      const addItems = (list, transactions) => {
        if (!transactions.length) {
          list.innerHTML = "<li>No transactions</li>";
        } else {
          for (const tx of transactions) {
            const li = document.createElement("li");
            li.classList.add("transaction-item");
      
            const dateSpan = document.createElement("span");
            dateSpan.classList.add("transaction-date");
            dateSpan.textContent = tx.TransDate;
      
            const infoSpan = document.createElement("span");
            infoSpan.classList.add("transaction-info");
            infoSpan.textContent = `${tx.description} - $${tx.amount.toFixed(2)}`;
      
            li.appendChild(dateSpan);
            li.appendChild(infoSpan);
            list.appendChild(li);
          }
        }
      };
      

      addItems(currentList, data.current_transactions);
      addItems(pastList, data.past_transactions);
    })
    .catch(err => {
      console.error("Error loading transactions:", err);
    });
}

  
  
  // Call on page load and then every 10 seconds
  updateTransactions();
  setInterval(updateTransactions, 10000);
  
  