// Spring 2025 Authors: Braden Doty
// Simple toggle functionality for collapsible sections
document.addEventListener('DOMContentLoaded', function(){
    const toggleButtons = document.querySelectorAll('.toggle-btn');
    toggleButtons.forEach(function(btn){
      btn.addEventListener('click', function(){
        const targetId = btn.getAttribute('data-target');
        const targetSection = document.getElementById(targetId);
        if (targetSection.style.display === "none" || targetSection.style.display === "") {
          targetSection.style.display = "block";
          btn.textContent = "Hide " + btn.getAttribute('data-label');
        } else {
          targetSection.style.display = "none";
          btn.textContent = "Show " + btn.getAttribute('data-label');
        }
      });
    });
  });