// Global data store for account information
let billAccountData = {};

/**
 * Opens the account detail modal and populates the account selection dropdown
 */
function openBillPayModal() {
    const customerId = currentCustomerID;
    if (!customerId) {
        injectFlashMessage("danger", "Please select a customer first.");
        return;
    }

    // Fetch customer accounts
    fetch(`/teller/customer/${customerId}/accounts`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch customer accounts');
            return response.json();
        })
        .then(data => {
            const accounts = data.accounts || [];
            populateBillPaymentAccounts(accounts);
            populatePaymentSourceAccounts(accounts);
            // Show the modal
            document.getElementById('billPayModal').style.display = 'flex';
        })
        .catch(error => {
            console.error('Error fetching customer accounts:', error);
            injectFlashMessage("danger", 'Failed to load customer accounts.');
        });
}

/**
 * Resets the account detail modal to its default hidden state
 */
function resetBillPayModalState() {
    const details = document.getElementById('billDetailsSection');
    if (details) details.style.display = 'none';
    document.getElementById('billAmount').textContent = '0.00';
    document.getElementById('minPaymentAmount').textContent = '0.00';
    document.getElementById('billDueDate').textContent      = 'N/A';
    document.getElementById('billPayeeName').textContent    = 'N/A';

    billAccountData = {};
}

/**
 * Populates the account selection dropdown with fetched accounts
 * @param {Array} accounts - List of account objects
 */
function populateBillPaymentAccounts(accounts) {
    const select = document.getElementById('billPaymentAccountId');
    select.innerHTML = '<option value="" disabled selected>Select an account</option>';

    // Separate accounts into billable and other categories
    const billable = accounts.filter(a => ['Credit Card','Mortgage Loan','Travel Visa'].includes(a.AccountType));
    const others   = accounts.filter(a => !['Credit Card','Mortgage Loan','Travel Visa'].includes(a.AccountType));

    // Helper to add option
    function addOption(acc) {
        const option = document.createElement('option');
        option.value = acc.AccountID;
        billAccountData[acc.AccountID] = acc;
        const bal = parseFloat(acc.CurrBal).toFixed(2);
        option.textContent = `${acc.AccountType} - $${bal} (ID: ${acc.AccountID})`;
        option.dataset.accountType = acc.AccountType;
        select.appendChild(option);
    }

    billable.forEach(addOption);
    if (billable.length === 0) {
        select.innerHTML = '<option value="" disabled selected>No bill accounts available</option>';
        select.disabled = true;
    } else {
        select.disabled = false; // Ensure dropdown is enabled if accounts are present
    }
}

function populatePaymentSourceAccounts(accounts) {
    const paymentSourceSelect = document.getElementById('paymentSourceAccountId');
    paymentSourceSelect.innerHTML = '<option value="" disabled selected>Select a payment source</option>';
    
    const eligible = accounts.filter(a =>
      a.AccountType === 'Checking' || a.AccountType === 'Savings'
    );
    eligible.forEach(acc => {
      const opt = document.createElement('option');
      opt.value = acc.AccountID;
      opt.textContent = `${acc.AccountType} – $${parseFloat(acc.CurrBal).toFixed(2)} (ID: ${acc.AccountID})`;
      paymentSourceSelect.appendChild(opt);
    });
  }

/**
 * Fetches and displays bill details for a selected account
 * @param {number|string} accountId
 */
function fetchBillInfo(accountId) {
    if (!accountId) return;

    // Show loading state
    const details = document.getElementById('billDetailsSection');
    details.style.display = 'block';
    document.getElementById('billAmount').textContent = 'Loading...';
    document.getElementById('minPaymentAmount').textContent = 'Loading...';
    document.getElementById('billDueDate').textContent      = 'Loading...';
    document.getElementById('billPayeeName').textContent    = 'Loading...';
    const balElem = document.getElementById('currentBalance');
    if (balElem) balElem.textContent = 'Loading...';

    // Determine account type
    const select = document.getElementById('billPaymentAccountId');
    const type   = select.options[select.selectedIndex].dataset.accountType;

    // Fetch bill info
    fetch(`/teller/api/bill-info/${accountId}`)
        .then(res => {
            if (!res.ok) throw new Error(`Server ${res.status}`);
            if (!res.headers.get('content-type').includes('application/json'))
                throw new Error('Invalid response format');
            return res.json();
        })
        .then(data => {
            if (data.error) throw new Error(data.error);

            // Display details
            if (data.bill_id) {
                document.getElementById('billAmount').textContent = Math.abs(data.amount.toFixed(2));
                document.getElementById('minPaymentAmount').textContent = data.min_payment.toFixed(2);
                document.getElementById('billDueDate').textContent      = data.due_date || 'N/A';
                document.getElementById('billPayeeName').textContent    = data.payee_name || 'Evergreen Bank';
                if (balElem) {
                    const b = Math.abs(parseFloat(billAccountData[accountId].CurrBal));
                    balElem.textContent = b.toFixed(2);
                }
            } else {
                handleNoBillScenario(accountId, type);
            }
        })
        .catch(err => {
            console.error('Error fetching bill information:', err);
            handleNoBillScenario(accountId, select.options[select.selectedIndex].dataset.accountType);
        });
}

/**
 * Fallback display when no active bill is found
 */
function handleNoBillScenario(accountId, accountType) {
    const amtElem = document.getElementById('billAmount');
    const minElem  = document.getElementById('minPaymentAmount');
    const dateElem = document.getElementById('billDueDate');
    const nameElem = document.getElementById('billPayeeName');
    const balElem  = document.getElementById('currentBalance');

    if (['Credit Card','Travel Visa'].includes(accountType)) {
        const bal = Math.abs(parseFloat(billAccountData[accountId]?.CurrBal || 0));
        const min = bal >= 100 ? 100 : bal;
        amtElem.textContent = '0.00';
        minElem.textContent  = min.toFixed(2);
        dateElem.textContent = 'Not scheduled';
        nameElem.textContent = 'Evergreen Bank';
        if (balElem) balElem.textContent = bal.toFixed(2);
    } else if (accountType === 'Mortgage Loan') {
        amtElem.textContent = '0.00';
        minElem.textContent  = '0.00';
        dateElem.textContent = 'No active mortgage bill';
        nameElem.textContent = 'Evergreen Bank';
        if (balElem) balElem.textContent = Math.abs(parseFloat(billAccountData[accountId]?.CurrBal || 0)).toFixed(2);
    } else {
        amtElem.textContent = '0.00';
        minElem.textContent  = '0.00';
        dateElem.textContent = 'No active bills';
        nameElem.textContent = 'N/A';
        if (balElem) balElem.textContent = parseFloat(billAccountData[accountId]?.CurrBal || 0).toFixed(2);
    }
}

/**
 * Triggered when account selection changes
 */
function handleBillAccountChange() {
    const accId = document.getElementById('billPaymentAccountId').value;
    if (accId) fetchBillInfo(accId);
    else       document.getElementById('billDetailsSection').style.display = 'none';
}

/**
 * Closes the modal
 */
function closeBillPayModal() {
    document.getElementById('billPayModal').style.display = 'none';
    resetBillPayModalState();
}

function submitBillPayment() {
    const billAccountIdSelect = document.getElementById('billPaymentAccountId');
    const billAccountId = billAccountIdSelect.value;

    const payAccountIdSelect = document.getElementById('paymentSourceAccountId');
    const payAccountId = payAccountIdSelect.value;

    const amountInput = document.getElementById('billPaymentAmount');
    const amount = amountInput.value.trim(); // Get the entered amount and remove whitespace

    const submitButton = document.getElementById('billpayButton');

    if (!amount) {
        if (submitButton) submitButton.disabled = false;
        return; // Stop if amount is empty
    }

    if (isNaN(amount) || amount <= 0) {
        if (submitButton) submitButton.disabled = false;
        return; // Stop if amount is not a positive number
    }

    const dataToSend = {
        billAmount: amount,
        payAccount: payAccountId
    };

    fetch(`/teller/pay-bill/${billAccountId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSend) // Convert JS object to JSON string
    })
    .then(response => {
        if (!response.ok) {
             return response.json().then(errData => {
                 throw new Error(errData.message || `Server error: ${response.status}`);
             }).catch(() => {
                 throw new Error(`Server error: ${response.status}`);
             });
        }
         const contentType = response.headers.get('content-type');
         if (!contentType || !contentType.includes('application/json')) {
             throw new Error('Received non-JSON response from server.');
         }
        return response.json();
    })
    .then(result => {
        if (result.success) {
            amountInput.value = '';
            fetchBillInfo(billAccountId);
            setTimeout(() => {
                location.reload();
            }, 3000);
            injectFlashMessage('success', 'Bill payment successful');
        }
    })
    .catch(error => {
        console.error('Error submitting bill payment:', error);
    })
    .finally(() => {
        if (submitButton) submitButton.disabled = false;
    });
}

// Attach event listener for account selection
document.addEventListener('DOMContentLoaded', () => {
    const sel = document.getElementById('billPaymentAccountId');
    if (sel) sel.addEventListener('change', handleBillAccountChange);
});

