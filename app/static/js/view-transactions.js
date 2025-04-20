/**
 * Loads and displays transactions for a specific account.
 */
function loadTransactions(accountId, accountType) {
    fetch(`/teller/account/${accountId}/transactions`)
      .then(res => res.json())
      .then(data => {
        const section = document.getElementById("transactionSection");
        const list = document.getElementById("transactionList");
        const label = document.getElementById("selectedAccountLabel");
  
        // Reset UI
        list.innerHTML = "";
        label.textContent = `${accountType} (ID: ${accountId})`;
  
        if (!data.success) {
          injectFlashMessage("danger", "Error fetching transactions.");
          return;
        }
  
        // Populate transaction list
        if (data.transactions.length === 0) {
          list.innerHTML = "<li>No transactions found.</li>";
        } else {
          data.transactions.forEach(txn => {
            const li = document.createElement("li");
            li.textContent = `${txn.TransDate} | ${txn.TransType} | $${txn.Amount}`;
            list.appendChild(li);
          });
        }
  
        // Reveal the transaction section
        section.style.display = "block";
      })
      .catch(error => {
        console.error("Failed to load transactions:", error);
        injectFlashMessage("danger", "An unexpected error occurred while loading transactions.");
      });
  }
  
  