function updateMinBillDue() {
  console.log("🔄 Running updateMinBillDue...");

  const accountId = window.accountId;
  const balanceApiUrl = `/api/account-balance/${accountId}`;

  fetch(balanceApiUrl)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.error("Balance API Error:", data.error);
        return;
      }

      const balance = parseFloat(data.balance || 0);
      const accountType = (data.account_type || "").toUpperCase();

      // Always update the total balance
      const accountBalanceElement = document.getElementById("accountBalance");
      if (accountBalanceElement) {
        accountBalanceElement.textContent = balance.toFixed(2);
      }

      // Only calculate minDue if Credit Card
      if (accountType === "CREDIT CARD") {
        let minDue = 0;
        if (balance >= 100) minDue = 100;
        else if (balance > 0) minDue = balance;

        const minDueDisplay = document.getElementById("min-due-display");
        const minPaymentDisplay = document.getElementById("min-payment-display");

        if (minDueDisplay) {
          minDueDisplay.textContent = `$${minDue.toFixed(2)}`;
        }
        if (minPaymentDisplay) {
          minPaymentDisplay.textContent = `$${minDue.toFixed(2)}`;
        }
      }
    })
    .catch(err => console.error("Failed to update balance and min due:", err));
}

document.addEventListener("DOMContentLoaded", () => {
  updateMinBillDue();
  setInterval(updateMinBillDue, 10000); // every 10 seconds
});
