let currentCustomerID = null;

function submitUsernameEdit() {
    const newUsername = document.getElementById("editUsernameInput").value.trim();
  
    if (!newUsername) return alert("Please enter a new username.");
  
    fetch("/teller/edit-username", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        customerId: currentCustomerID,
        newUsername: newUsername
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        location.reload();
      } else {
        alert("Failed to edit username: " + data.message);
      }
    });
  }
  
  function resetCustomerPassword() {
    const oldPassword = document.getElementById("oldPasswordInput").value.trim();
    const newPassword = document.getElementById("newPasswordInput").value.trim();
  
    if (!oldPassword || !newPassword) {
      return alert("Please enter both the old and new passwords.");
    }
  
    fetch("/teller/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        customerID: currentCustomerID, 
        oldPassword, 
        newPassword 
      })
    }).then(res => res.json()).then(data => {
      if (data.success) alert("Password reset successfully.");
      else alert("Failed to reset password: " + data.message);
    });
  }
  
  function submitCustomerDelete() {
    if (!confirm("Are you sure you want to delete this customer?")) return;
  
    // Step 1: Check if user still has active accounts or bills
    fetch(`/teller/check-accounts/${currentCustomerID}`)
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          alert("Could not check customer account status.");
          return;
        }
  
        if (data.hasOpenAccountsOrBills) {
          alert("This customer still has open accounts or unpaid bills. Please resolve them before deletion.");
          return;
        }
  
        // Step 2: Delete
        fetch("/teller/delete-customer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ customerID: currentCustomerID })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert("Customer successfully deleted.");
            location.reload();
          } else {
            alert("Failed to delete customer: " + data.message);
          }
        });
      })
      .catch(err => {
        alert("Error checking account status.");
        console.error(err);
      });
  }