/**
 * Fetches and displays all accounts for a given customer in a modal.
 */
function openAccountsModal(customerId, firstName, lastName) {
    fetch(`/employee/customer/${customerId}/accounts`)
      .then(res => res.json())
      .then(data => {
        const list = document.getElementById("accountList");
        const transactionSection = document.getElementById("transactionSection");
        const modal = document.getElementById("viewAccountsModal");
        const modalTitle = document.getElementById("accountsModalTitle");
  
        // Clear previous content
        list.innerHTML = "";
        transactionSection.style.display = "none";
  
        // Set the modal title to "custID's Accounts"
        modalTitle.textContent = `${firstName} ${lastName}'s Accounts`;

        if (!data.success) {
          alert("Failed to fetch accounts.");
          return;
        }
  
        // Populate accounts list
        data.accounts.forEach(account => {
          const li = document.createElement("li");
          li.classList.add("account-box");
  
          const isDeletable = parseFloat(account.CurrBal) === 0;

          li.innerHTML = `
            <h3>${account.AccountType}</h3>
            <p>ID: ${account.AccountID}</p>
            <p>$${parseFloat(account.CurrBal).toFixed(2)}</p>
            <button class="delete-account-btn" ${!isDeletable ? "disabled title='Balance must be $0.00 to delete'" : ""} onclick="deleteAccountFromModal(${account.AccountID})">
              Delete
            </button>
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
  