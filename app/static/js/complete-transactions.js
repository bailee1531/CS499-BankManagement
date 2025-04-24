function openDepositModal() {
    populateAccountDropdown(currentCustomerID, "depositAccountId");
    document.getElementById("depositModal").style.display = "flex";
}


function closeDepositModal() {
    document.getElementById("depositModal").style.display = "none";
}

function submitDeposit() {
    const accountId = document.getElementById("depositAccountId").value;
    const amountStr = document.getElementById("depositAmount").value;
    const depositBtn = document.querySelector('#depositModal .modal-buttons .action-btn');
  
    if (!accountId || !amountStr) {
      injectFlashMessage("danger", "Please enter both Account ID and the deposit amount.");
      return;
    }
    const amount = parseFloat(amountStr);
    if (isNaN(amount) || amount <= 0) {
      injectFlashMessage("danger", "Deposit amount must be a positive number.");
      return;
    }
  
    depositBtn.disabled = true;
    depositBtn.classList.add("disabled");
  
    // Fetch current balance & type
    fetch(`/teller/api/account-balance/${accountId}`)
      .then(r => r.json())
      .then(info => {
        const type    = info.account_type;   
        const balance = parseFloat(info.balance);
  
        // Block over‐payment on Credit Card or Mortgage
        if ((type === "Credit Card" || type === "Mortgage Loan")
            && amount > Math.abs(balance)) {
          injectFlashMessage(
            "danger",
            `Cannot deposit more than remaining balance ($${Math.abs(balance).toFixed(2)}).`
          );
          throw "overpayment";
        }
  
        // Proceed with deposit
        return fetch("/teller/deposit", {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({ accountId, amount: amountStr })
        });
      })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          injectFlashMessage("success", data.message);
          setTimeout(() => location.reload(), 3000);
        } else {
          injectFlashMessage("danger", "Error: " + data.message);
        }
      })
      .catch(err => {
        if (err !== "overpayment") {
          injectFlashMessage("danger", "Failed to process deposit.");
          console.error(err);
        }
      })
      .finally(() => {
        setTimeout(() => {
          depositBtn.disabled = false;
          depositBtn.classList.remove("disabled");
        }, 4000);
      });
  }  

function openWithdrawModal() {
    populateAccountDropdown(currentCustomerID, "withdrawAccountId");
    document.getElementById("withdrawModal").style.display = "flex";
}


function closeWithdrawModal() {
    document.getElementById("withdrawModal").style.display = "none";
}

function submitWithdraw() {
    const accountId = document.getElementById("withdrawAccountId").value;
    const amount = document.getElementById("withdrawAmount").value;
    const withdrawBtn = document.querySelector('#withdrawModal .modal-buttons .action-btn');

    if (!accountId || !amount) {
        injectFlashMessage("danger", "Please enter both Account ID and the withdrawal amount.");
        return;
    }

    // Disable button temporarily
    withdrawBtn.disabled = true;
    withdrawBtn.classList.add("disabled");

    const payload = {
        accountId: accountId,
        amount: amount
    };

    fetch("/teller/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            injectFlashMessage("success", data.message);
            // Wait for a tiny delay
            setTimeout(() => {
              location.reload();
            }, 3000);
        } else {
            injectFlashMessage("danger", "Error: " + data.message);
        }
    })
    .catch(err => {
        injectFlashMessage("danger", "Failed to process withdrawal.");
        console.error(err);
    })
    .finally(() => {
        setTimeout(() => {
            withdrawBtn.disabled = false;
            withdrawBtn.classList.remove("disabled");
        }, 4000);
    });
}

function openTransferModal() {
    populateAccountDropdown(currentCustomerID, "sourceAccountId");
    populateAccountDropdown(currentCustomerID, "destinationAccountId");
    document.getElementById("transferModal").style.display = "flex";
}


function closeTransferModal() {
    document.getElementById("transferModal").style.display = "none";
}

function submitTransfer() {
    const sourceAccountId = document.getElementById("sourceAccountId").value;
    const destinationAccountId = document.getElementById("destinationAccountId").value;
    const amount = document.getElementById("transferAmount").value;
    const transferBtn = document.querySelector('#transferModal .modal-buttons .action-btn');

    if (!sourceAccountId || !destinationAccountId || !amount) {
        injectFlashMessage("danger", "Please enter Source Account ID, Destination Account ID, and the transfer amount.");
        return;
    }

    // Disable button temporarily
    transferBtn.disabled = true;
    transferBtn.classList.add("disabled");

    const payload = {
        sourceAccountId: sourceAccountId,
        destinationAccountId: destinationAccountId,
        amount: amount
    };

    fetch("/teller/transfer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            injectFlashMessage("success", data.message);
            // Wait for a tiny delay
            setTimeout(() => {
              location.reload();
            }, 3000);
        } else {
            injectFlashMessage("danger", "Error: " + data.message);
        }
    })
    .catch(err => {
        injectFlashMessage("danger", "Failed to process transfer.");
        console.error(err);
    })
    .finally(() => {
        setTimeout(() => {
            transferBtn.disabled = false;
            transferBtn.classList.remove("disabled");
        }, 4000);
    });
}

window.onclick = function(event) {
    const depositModal = document.getElementById("depositModal");
    const withdrawModal = document.getElementById("withdrawModal");
    const transferModal = document.getElementById("transferModal");
    if (event.target == depositModal) {
        depositModal.style.display = "none";
    }
    if (event.target == withdrawModal) {
        withdrawModal.style.display = "none";
    }
    if (event.target == transferModal) {
        transferModal.style.display = "none";
    }
}