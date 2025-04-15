function setModalTextContent(ids, values) {
    ids.forEach((id, index) => {
      const el = document.getElementById(id);
      if (el) el.textContent = values[index];
    });
  }