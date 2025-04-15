let currentCustomerID = null;
let openAccountCustomerID = null;

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
  toggleAccountInputs();
}

function closeCustomerModal() {
  document.getElementById("customerModal").style.display = "none";
}

function openAccountsModal(customerId, firstName, lastName) {
  fetch(`/teller/customer/${customerId}/accounts`)
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

function openAccountModal(id) {
  openAccountCustomerID = id;
  document.getElementById("accountType").value = "Savings";
  document.getElementById("initialDeposit").value = "";
  document.getElementById("openAccountModal").style.display = "flex";
}

function closeAccountModal() {
  document.getElementById("openAccountModal").style.display = "none";
}

function submitAccountOpen() {
  const type = document.getElementById("accountType").value;
  let payload = {
  customerID: currentCustomerID,
  accountType: type
  };

  if (["Checking", "Savings", "Money Market"].includes(type)) {
    const deposit = parseFloat(document.getElementById("initialDeposit").value);
    if (isNaN(deposit)) return alert("Enter a valid deposit amount.");
    payload.depositAmount = deposit;

  } else if (type === "Home Mortgage Loan") {
    const amount = parseFloat(document.getElementById("loanAmount").value);
    const years = parseInt(document.getElementById("loanTerm").value);
    if (isNaN(amount) || isNaN(years)) return alert("Enter valid loan details.");
    payload.loanAmount = amount;
    payload.loanTerm = years;
  }

  fetch("/teller/create-account", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(res => res.json()).then(data => {
    if (data.success) location.reload();
    else alert("Failed to open account: " + data.message);
  });
}

function toggleAccountInputs() {
const type = document.getElementById("accountType").value;

const deposit = document.getElementById("initialDeposit");
const loanAmount = document.getElementById("loanAmount");
const loanTerm = document.getElementById("loanTerm");
const creditNote = document.getElementById("creditNote");

// Hide all by default
deposit.style.display = "none";
loanAmount.style.display = "none";
loanTerm.style.display = "none";
creditNote.style.display = "none";

if (["Checking", "Savings", "Money Market"].includes(type)) {
  deposit.placeholder = "Initial Deposit";
  deposit.style.display = "block";
} else if (type === "Home Mortgage Loan") {
  loanAmount.style.display = "block";
  loanTerm.style.display = "block";
} else if (type === "Travel Visa") {
  creditNote.style.display = "block";
}
}

function goToAccountInfoPage() {
const selectedType = document.getElementById("accountTypeSelect").value;
if (!selectedType) return alert("Please select an account type.");
window.selectedAccountType = selectedType;
document.getElementById("accountTypePage").style.display = "none";
document.getElementById("accountInfoPage").style.display = "block";
}

function goBackToAccountType() {
document.getElementById("accountTypePage").style.display = "block";
document.getElementById("accountInfoPage").style.display = "none";
}

function submitOpenAccount() {
const payload = {
  firstName: document.getElementById("newFirstName").value,
  lastName: document.getElementById("newLastName").value,
  username: document.getElementById("newUsername").value,
  password: document.getElementById("newPassword").value,
  address: document.getElementById("newAddress").value,
  ssn: document.getElementById("newSSN").value,
  email: document.getElementById("newEmail").value,
  phone: document.getElementById("newPhone").value,
  securityQuestion1: document.getElementById("securityQuestion1").value,
  securityAnswer1: document.getElementById("securityAnswer1").value,
  securityQuestion2: document.getElementById("securityQuestion2").value,
  securityAnswer2: document.getElementById("securityAnswer2").value,
  accountType: window.selectedAccountType
};

fetch("/teller/open-account", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
})
.then(res => res.json())
.then(data => {
  if (data.success) {
    alert(data.message);
    location.reload();
  } else {
    alert("Error: " + data.message);
  }
})
.catch(err => {
  alert("Failed to open account.");
  console.error(err);
});
}

function closeAccountsModal() {
  document.getElementById("viewAccountsModal").style.display = "none";
}

function viewCustomerAccounts() {
  if (!currentCustomerID) return;

  fetch(`/teller/get-accounts/${currentCustomerID}`)
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("userAccounts");
      if (!container) return;

      if (data.success && data.accounts.length > 0) {
        const formatted = data.accounts.map(acc => {
          const balance = parseFloat(acc.CurrBal).toFixed(2);
          const creditLimit = acc.CreditLimit ? `<br>Credit Limit: $${parseFloat(acc.CreditLimit).toFixed(2)}` : "";
          const deleteButton = (parseFloat(acc.CurrBal) === 0.0)
            ? `<button class="delete-account-btn" onclick="deleteAccount(${acc.AccountID})">Delete</button>`
            : `<button class="delete-account-btn" disabled title="Balance must be $0.00 to delete">Delete</button>`;

          return `
            <div class="account-box">
              <strong>${acc.AccountType}</strong><br>
              ID: ${acc.AccountID}<br>
              Balance: $${balance}<br>
              Opened: ${acc.DateOpened}${creditLimit}<br>
              ${deleteButton}
            </div>
          `;
        }).join("");

        container.innerHTML = formatted;
      } else {
        container.textContent = "This user has no accounts.";
      }
    })
    .catch(err => {
      console.error("Error fetching accounts:", err);
      document.getElementById("userAccounts").textContent = "Error loading accounts.";
    });
}

function deleteAccountFromModal(accountID) {
  if (!currentCustomerID) return alert("Customer ID not found.");
  if (!confirm(`Are you sure you want to delete Account ID ${accountID}?`)) return;

  fetch("/teller/delete-account", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customerID: currentCustomerID, accountID: accountID })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === "success") {
      alert(data.message);
      openAccountsModal(currentCustomerID); // Refresh the modal
    } else {
      alert("Error: " + data.message);
    }
  })
  .catch(err => {
    console.error("Failed to delete account:", err);
    alert("Server error during account deletion.");
  });
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
  