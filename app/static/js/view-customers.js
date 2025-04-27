// Spring 2025 Authors: Bailee Segars
function openCustomerModal(customerID, username, firstName, lastName, phone, email, address, account) {
    currentCustomerID = customerID;
    selectedCustomerID = customerID;
  
    setModalTextContent(
        [
        "modalUsername",
        "modalCustomerID",
        "modalFirstName",
        "modalLastName",
        "modalPhone",
        "modalEmail",
        "modalAddress"
        ],
        [
        username,
        customerID,
        firstName,
        lastName,
        phone,
        email,
        address
        ]
    );
  
    document.getElementById("editUsernameInput").value = "";
    document.getElementById("customerModal").style.display = "flex";
}
  
function closeCustomerModal() {
    document.getElementById("customerModal").style.display = "none";
}

function closeAccountsModal() {
    document.getElementById("viewAccountsModal").style.display = "none";
}

function viewCustomerAccounts() {
    if (!currentCustomerID) return;
  
    fetch(`/admin/get-accounts/${currentCustomerID}`)
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById("userAccounts");
        if (!container) return;
  
        if (data.success && data.accounts.length > 0) {
          const formatted = data.accounts.map(acc =>
            `• AccountID: ${acc.AccountID}
    Type: ${acc.AccountType}
    Balance: $${parseFloat(acc.CurrBal).toFixed(2)}
    Opened: ${acc.DateOpened}${acc.CreditLimit ? `\n  Credit Limit: $${parseFloat(acc.CreditLimit).toFixed(2)}` : ""}`
          ).join('\n\n');
  
          container.textContent = formatted;
        } else {
          container.textContent = "This user has no accounts.";
        }
    })
    .catch(err => {
        console.error("Error fetching accounts:", err);
        document.getElementById("userAccounts").textContent = "Error loading accounts.";
    });
}
  
let showingAccounts = false;
  
function toggleCustomerView() {
    const infoPanel = document.getElementById("customerInfoPanel");
    const accountsPanel = document.getElementById("userAccountsPanel");
    const toggleBtn = document.getElementById("toggleAccountsBtn");
  
    showingAccounts = !showingAccounts;
  
    if (showingAccounts) {
      infoPanel.style.display = "none";
      accountsPanel.style.display = "block";
      toggleBtn.textContent = "Customer Info";
      viewCustomerAccounts(); // Load accounts only when showing
    } else {
      infoPanel.style.display = "block";
      accountsPanel.style.display = "none";
      toggleBtn.textContent = "User's Accounts";
    }
}

function filterCustomers() {
    const input = document.getElementById("searchBar").value.toLowerCase();
    const cards = document.querySelectorAll(".customer-card");
    cards.forEach(card => {
      const name = card.querySelector("strong").innerText.toLowerCase();
      const account = card.querySelector("p").innerText.toLowerCase();
      card.classList.toggle("hidden", !name.includes(input) && !account.includes(input));
    });
  }