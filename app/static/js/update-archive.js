function updateArchivedBills() {
    if (typeof archivedBillsApiUrl === "undefined") {
      console.error("archivedBillsApiUrl is not defined");
      return;
    }
  
    fetch(archivedBillsApiUrl)
      .then(response => response.json())
      .then(data => {
        const archivedBills = data.archived_bills || [];
  
        const billsContainer = document.getElementById('archived-bills-list');
        if (billsContainer) {
          billsContainer.innerHTML = "";
  
          if (archivedBills.length > 0) {
            archivedBills.forEach(bill => {
              const li = document.createElement("li");
              li.classList.add("transaction-item");
  
              const dateSpan = document.createElement("span");
              dateSpan.classList.add("transaction-date");
              dateSpan.textContent = bill.DueDate || 'N/A';
  
              const infoSpan = document.createElement("span");
              infoSpan.classList.add("transaction-info");
              infoSpan.textContent = `Paid $${parseFloat(bill.Amount).toFixed(2)}`;
  
              li.appendChild(dateSpan);
              li.appendChild(infoSpan);
              billsContainer.appendChild(li);
            });
          } else {
            billsContainer.innerHTML = '<li>No archived credit card bills found.</li>';
          }
        }
      })
      .catch(error => console.error('Error fetching archived bills:', error));
  }
  
  updateArchivedBills();
  setInterval(updateArchivedBills, 30000);  // Refresh every 30 seconds
  