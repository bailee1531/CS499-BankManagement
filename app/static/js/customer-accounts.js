/**
 * Fetches and displays all accounts for a given customer in a modal.
 */
function openAccountsModal(customerId) {
    fetch(`/employee/customer/${customerId}/accounts`)
      .then(res => res.json())
      .then(data => {
        const list = document.getElementById("accountList");
        const transactionSection = document.getElementById("transactionSection");
        const modal = document.getElementById("viewAccountsModal");
  
        // Clear previous content
        list.innerHTML = "";
        transactionSection.style.display = "none";
  
        if (!data.success) {
          alert("Failed to fetch accounts.");
          return;
        }
  
        if (data.accounts.length === 0) {
          list.innerHTML = "<li>No accounts found.</li>";
          return;
        }
  
        // Populate accounts list
        data.accounts.forEach(account => {
          const li = document.createElement("li");
          li.classList.add("account-box");
  
          li.innerHTML = `
            <h3>${account.AccountType}</h3>
            <p>ID: ${account.AccountID}</p>
            <p>$${account.CurrBal}</p>
          `;
  
          li.onclick = () => loadTransactions(account.AccountID, account.AccountType);
          list.appendChild(li);
        });
  
        // Display the modal
        modal.style.display = "flex";
      })
      .catch(error => {
        console.error("Error fetching accounts:", error);
        alert("An error occurred while loading accounts.");
      });
  }
  