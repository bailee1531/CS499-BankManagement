function openDepositModal() {
    populateAccountDropdown(currentCustomerID, "depositAccountId");
    document.getElementById("depositModal").style.display = "block";
}


function closeDepositModal() {
    document.getElementById("depositModal").style.display = "none";
}

function submitDeposit() {
    const accountId = document.getElementById("depositAccountId").value;
    const amount = document.getElementById("depositAmount").value;

    if (!accountId || !amount) {
        alert("Please enter both Account ID and the deposit amount.");
        return;
    }

    const payload = {
        accountId: accountId,
        amount: amount
    };

    fetch("/teller/deposit", {
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
        alert("Failed to process deposit.");
        console.error(err);
    });
}

function openWithdrawModal() {
    populateAccountDropdown(currentCustomerID, "withdrawAccountId");
    document.getElementById("withdrawModal").style.display = "block";
}


function closeWithdrawModal() {
    document.getElementById("withdrawModal").style.display = "none";
}

function submitWithdraw() {
    const accountId = document.getElementById("withdrawAccountId").value;
    const amount = document.getElementById("withdrawAmount").value;

    if (!accountId || !amount) {
        alert("Please enter both Account ID and the withdrawal amount.");
        return;
    }

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
            alert(data.message);
            location.reload();
        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(err => {
        alert("Failed to process withdrawal.");
        console.error(err);
    });
}

function openTransferModal() {
    populateAccountDropdown(currentCustomerID, "sourceAccountId");
    populateAccountDropdown(currentCustomerID, "destinationAccountId");
    document.getElementById("transferModal").style.display = "block";
}


function closeTransferModal() {
    document.getElementById("transferModal").style.display = "none";
}

function submitTransfer() {
    const sourceAccountId = document.getElementById("sourceAccountId").value;
    const destinationAccountId = document.getElementById("destinationAccountId").value;
    const amount = document.getElementById("transferAmount").value;

    if (!sourceAccountId || !destinationAccountId || !amount) {
        alert("Please enter Source Account ID, Destination Account ID, and the transfer amount.");
        return;
    }

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
            alert(data.message);
            location.reload();
        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(err => {
        alert("Failed to process transfer.");
        console.error(err);
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