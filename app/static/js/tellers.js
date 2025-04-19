function openCreateModal() {
    document.getElementById("createFormModal").style.display = "flex";
}
function closeCreateModal() {
    document.getElementById("createFormModal").style.display = "none";
    document.getElementById("firstNameInput").value = "";
    document.getElementById("lastNameInput").value = "";
}

function openViewModal(id, username) {
    document.getElementById("modalEmployeeID").textContent = id;
    document.getElementById("modalEmpUsername").textContent = username;
    document.getElementById("editUsernameInput").value = "";
    document.getElementById("viewModal").style.display = "flex";

    fetch("/admin/check-employee", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ employeeID: id })
    })
    .then(res => res.json())
    .then(data => {
        if(!data.exists) {
            const editButton = document.querySelector('#viewModal .modal-buttons button:first-child');
            if (editButton) {
                editButton.disabled = true;
            }
        }
    })
}
function closeViewModal() {
    document.getElementById("viewModal").style.display = "none";
}

function submitTeller() {
    const firstName = document.getElementById("firstNameInput").value.trim();
    const lastName = document.getElementById("lastNameInput").value.trim();

    if (!firstName || !lastName) {
        injectFlashMessage("danger", "Please enter both first and last name.");
        return;
    }

    fetch("/admin/create-teller", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ firstName, lastName })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            injectFlashMessage("success", `Teller ${firstName} ${lastName} has been successfully created.`);
            // Wait for a tiny delay
            setTimeout(() => {
              location.reload();
            }, 3000);
        }
        else injectFlashMessage("danger", "Failed to create teller: " + data.message);
    })
    .catch(err => injectFlashMessage("danger", "Something went wrong."));
}

function submitEdit() {
    const id = document.getElementById("modalEmployeeID").textContent;
    const newUsername = document.getElementById("editUsernameInput").value.trim();

    if (!newUsername) {
        injectFlashMessage("danger", "Please enter a new username.");
        return;
    }

    fetch('/admin/edit-teller', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({employeeID: id, newUsername: newUsername})
    })
    .then(res => res.json())
    .then(editData => {
        if (editData.success) {
            injectFlashMessage("success", data.message);
            document.getElementById('modalEmpUsername').textContent = newUsername;
            closeViewModal();
        }
        else {
            injectFlashMessage("danger", "Failed to update teller information: " + editData.message);
        }
    })
}

function submitDelete() {
    const id = document.getElementById("modalEmployeeID").textContent;

    showConfirm(`Are you sure you want to delete this teller?`, () => {
        fetch("/admin/delete-teller", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ employeeID: id })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                injectFlashMessage("success", `Teller ${id} has been successfully deleted.`);
                setTimeout(() => {
                    location.reload();
                }, 3000);
            } else {
                injectFlashMessage("danger", "Failed to delete teller: " + data.message);
            }
        })
        .catch(err => {
            injectFlashMessage("danger", data.message);
        });
    });
}

function filterTellers() {
    const input = document.getElementById("tellerSearchBar").value.toLowerCase();
    const cards = document.querySelectorAll(".teller-card");

    cards.forEach(card => {
        const name = card.querySelector("strong").innerText.toLowerCase();
        card.classList.toggle("hidden", !name.includes(input));
    });
}