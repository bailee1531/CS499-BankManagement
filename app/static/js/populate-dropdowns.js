function populateAccountDropdown(customerID, dropdownId) {
    fetch(`/teller/get-accounts/${customerID}`)
    .then(res => res.json())
    .then(data => {
        const dropdown = document.getElementById(dropdownId);
        dropdown.innerHTML = ""; // Clear existing options

        if (data.success && data.accounts.length > 0) {
            data.accounts.forEach(acc => {
                const option = document.createElement("option");
                option.value = acc.AccountID;
                option.textContent = `${acc.AccountType} - ${acc.AccountID}`;
                dropdown.appendChild(option);
            });
        } else {
            const option = document.createElement("option");
            option.value = "";
            option.textContent = "No accounts found";
            dropdown.appendChild(option);
        }
    })
    .catch(err => {
        console.error(`Failed to load accounts for ${dropdownId}:`, err);
    });
}
