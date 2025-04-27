// Spring 2025 Authors: Braden Doty
function updateAccountInfo() {
  console.log("Running updateAccountInfo...");

  const accountId = window.accountId;
  const balanceApiUrl = `/api/account-balance/${accountId}`;
  const billInfoApiUrl = `/api/bill-info/${accountId}`;

  // First get current account balance
  fetch(balanceApiUrl)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.error("Balance API Error:", data.error);
        return;
      }

      const currentBalance = parseFloat(data.balance || 0);
      const accountType = (data.account_type || "").toUpperCase();

      // Update current balance display
      const accountBalanceElement = document.getElementById("accountBalance");
      if (accountBalanceElement) {
        accountBalanceElement.textContent = currentBalance.toFixed(2);
        console.log(`Updated current balance display to: ${currentBalance.toFixed(2)}`);
      }
      
      // For credit cards, get the current statement info
      if (accountType === "CREDIT CARD") {
        // Get bill information
        fetch(billInfoApiUrl)
          .then(response => response.json())
          .then(billData => {
            if (billData.error) {
              console.error("Bill API Error:", billData.error);
              return;
            }
            
            // Only proceed if we have bill data
            if (billData.amount !== undefined) {
              const statementBalance = parseFloat(billData.amount);
              const minPayment = parseFloat(billData.min_payment || 0);
              const dueDate = billData.due_date || "";
              
              // Update minimum due display - match the extra_info.minimum_due element format
              const extraInfoSection = document.querySelector('.extra-account-info');
              if (extraInfoSection) {
                // Look for existing minimum due element or create it if not found
                let minDueElement = extraInfoSection.querySelector('.info-label:contains("Minimum Due")');
                if (!minDueElement) {
                  // If not found, create and add it
                  const minDuePara = document.createElement('p');
                  minDuePara.innerHTML = '<span class="info-label">Minimum Due:</span> $<span id="min-due-display">0.00</span>';
                  extraInfoSection.appendChild(minDuePara);
                  minDueElement = minDuePara.querySelector('#min-due-display');
                } else {
                  // If found, get the span after it
                  minDueElement = minDueElement.parentElement.querySelector('span:not(.info-label)') || 
                                 minDueElement.parentElement;
                }
                
                // Update the minimum due amount
                if (minDueElement.id === 'min-due-display') {
                  minDueElement.textContent = minPayment.toFixed(2);
                } else {
                  // If no specific span, update the whole text
                  const label = minDueElement.querySelector('.info-label');
                  if (label) {
                    minDueElement.innerHTML = '';
                    minDueElement.appendChild(label);
                    minDueElement.innerHTML += ` $${minPayment.toFixed(2)}`;
                  }
                }
              }
              
              // Add/update statement balance to extra info section
              let statementElement = document.querySelector('.info-label:contains("Statement Balance")');
              if (!statementElement && extraInfoSection) {
                const statementPara = document.createElement('p');
                statementPara.innerHTML = '<span class="info-label">Statement Balance:</span> $<span id="statement-balance">0.00</span>';
                extraInfoSection.appendChild(statementPara);
                statementElement = document.getElementById('statement-balance');
              } else if (statementElement) {
                statementElement = statementElement.parentElement.querySelector('span:not(.info-label)') || 
                                  statementElement.parentElement;
              }
              
              if (statementElement && statementElement.id === 'statement-balance') {
                statementElement.textContent = statementBalance.toFixed(2);
              } else if (statementElement) {
                const label = statementElement.querySelector('.info-label');
                if (label) {
                  statementElement.innerHTML = '';
                  statementElement.appendChild(label);
                  statementElement.innerHTML += ` $${statementBalance.toFixed(2)}`;
                }
              }
              
              // Add/update due date element
              let dueDateElement = document.querySelector('.info-label:contains("Bill Due Date")');
              if (dueDateElement) {
                dueDateElement = dueDateElement.parentElement;
                const label = dueDateElement.querySelector('.info-label');
                if (label) {
                  dueDateElement.innerHTML = '';
                  dueDateElement.appendChild(label);
                  dueDateElement.innerHTML += ` ${dueDate}`;
                }
              }
              
              // Add a "New Transactions" element if it doesn't exist
              let newTransElement = document.querySelector('.info-label:contains("New Transactions")');
              if (!newTransElement && extraInfoSection) {
                const newTransPara = document.createElement('p');
                const newTransAmount = Math.max(0, currentBalance - statementBalance).toFixed(2);
                newTransPara.innerHTML = '<span class="info-label">New Transactions:</span> $<span id="new-transactions">0.00</span>';
                extraInfoSection.appendChild(newTransPara);
                const newTransDisplay = document.getElementById('new-transactions');
                if (newTransDisplay) {
                  newTransDisplay.textContent = newTransAmount;
                }
              } else if (newTransElement) {
                newTransElement = newTransElement.parentElement;
                const newTransAmount = Math.max(0, currentBalance - statementBalance).toFixed(2);
                const label = newTransElement.querySelector('.info-label');
                if (label) {
                  newTransElement.innerHTML = '';
                  newTransElement.appendChild(label);
                  newTransElement.innerHTML += ` $${newTransAmount}`;
                }
              }
            }
          })
          .catch(err => console.error("Failed to get bill information:", err));
      }
      
      // Handle mortgage accounts
      if (accountType === "MORTGAGE LOAN") {
        const mortgageTotal = Math.abs(currentBalance);
        // Check if we have a mortgage-total-display element, if not, we'll need to add it
        let mortgageTotalElement = document.getElementById("mortgage-total-display");
        if (!mortgageTotalElement) {
          // Look for an extra-account-info section to add to
          const extraInfoSection = document.querySelector('.extra-account-info');
          if (extraInfoSection) {
            // Create a mortgage total element
            const mortgagePara = document.createElement('p');
            mortgagePara.innerHTML = '<span class="info-label">Remaining Balance:</span> $<span id="mortgage-total-display">0.00</span>';
            extraInfoSection.appendChild(mortgagePara);
            mortgageTotalElement = document.getElementById('mortgage-total-display');
          }
        }
        
        if (mortgageTotalElement) {
          mortgageTotalElement.textContent = mortgageTotal.toFixed(2);
        }
      }
    })
    .catch(err => console.error("Failed to update account information:", err));
}

// Add a jQuery-like contains selector for older browsers
if (!Element.prototype.matches) {
  Element.prototype.matches = Element.prototype.msMatchesSelector || 
                              Element.prototype.webkitMatchesSelector;
}

if (!document.querySelectorAll) {
  document.querySelectorAll = function(selector) {
    return document.querySelector(selector);
  };
}

// Custom contains selector implementation
document.querySelector = (function(oldFn) {
  return function(selector) {
    if (selector.includes(':contains(')) {
      // Extract the text to find
      const textMatch = selector.match(/:contains\("(.+?)"\)/);
      const text = textMatch ? textMatch[1] : '';
      
      // Get the base selector without the :contains part
      const baseSelector = selector.replace(/:contains\("(.+?)"\)/, '');
      
      // Find elements that match the base selector
      const elements = oldFn.call(this, baseSelector || '*');
      
      // Filter to those containing the text
      for (let i = 0; i < elements.length; i++) {
        if (elements[i].textContent.includes(text)) {
          return elements[i];
        }
      }
      return null;
    }
    return oldFn.call(this, selector);
  };
})(document.querySelector);

document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM loaded, initializing account information update...");
  // Run immediately on page load
  updateAccountInfo();
  
  // Then set up interval for regular updates
  setInterval(updateAccountInfo, 10000); // every 10 seconds
});