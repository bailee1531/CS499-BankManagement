let currentCustomerID = null;

function submitUsernameEdit() {
    const newUsername = document.getElementById("editUsernameInput").value.trim();
  
    if (!newUsername) return injectFlashMessage("danger", "Please enter a new username.");
  
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
        injectFlashMessage("success", "Username successfully updated.");
        // Wait for a tiny delay
        setTimeout(() => {
          location.reload();
        }, 3000);
      } else {
        injectFlashMessage("danger", "Failed to edit username: " + data.message);
      }
    });
  }
  
function resetCustomerPassword() {
  const oldPassword = document.getElementById("oldPasswordInput").value.trim();
  const newPassword = document.getElementById("newPasswordInput").value.trim();

  if (!oldPassword || !newPassword) {
    return injectFlashMessage("danger", "Please enter both the old and new passwords.");
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
    if (data.success) {
      injectFlashMessage("success", "Password reset successfully.");
    }
    else injectFlashMessage("danger", "Failed to reset password: " + data.message);
  });
}
  
function submitCustomerDelete() {
  const deleteBtn = document.querySelector('#customerModal button[onclick="submitCustomerDelete()"]');

  showConfirm('Are you sure you want to delete this customer?', () => {
    // Disable button temporarily
    deleteBtn.disabled = true;
    deleteBtn.classList.add("disabled");

    // Step 1: Check if user still has active accounts or bills
    fetch(`/teller/check-accounts/${currentCustomerID}`)
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          injectFlashMessage("danger", "Could not check customer account status.");
          return;
        }

        if (data.hasOpenAccountsOrBills) {
          injectFlashMessage("danger", "This customer still has open accounts or unpaid bills. Please resolve them before deletion.");
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
            injectFlashMessage("success", data.message);
            // Wait for a tiny delay
            setTimeout(() => {
              location.reload();
            }, 3000);
          } else {
            injectFlashMessage("danger", "Failed to delete customer: " + data.message);
          }
        });
      })
      .catch(err => {
        injectFlashMessage("danger", "Error checking account status.");
        console.error(err);
      })
      .finally(() => {
        setTimeout(() => {
          deleteBtn.disabled = false;
          deleteBtn.classList.remove("disabled");
        }, 4000);
      });
  });
}