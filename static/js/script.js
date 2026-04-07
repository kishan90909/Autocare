// ========================================
// Loading Animation
// ========================================
document.addEventListener("DOMContentLoaded", function () {
  const loading = document.getElementById("loading");

  if (loading) {
    window.addEventListener("load", function () {
      loading.classList.add("hidden");
      setTimeout(() => loading.style.display = "none", 500);
    });

    setTimeout(() => {
      if (loading.style.display !== "none") {
        loading.classList.add("hidden");
        setTimeout(() => loading.style.display = "none", 500);
      }
    }, 3000);
  }
});

// ========================================
// Smooth Scroll
// ========================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", function (e) {
    if (this.getAttribute("href") !== "#") {
      e.preventDefault();
      document.querySelector(this.getAttribute("href"))
        .scrollIntoView({ behavior: "smooth" });
    }
  });
});

// ========================================
// Navbar Shadow
// ========================================
window.addEventListener("scroll", () => {
  const navbar = document.querySelector(".navbar");
  if (!navbar) return;

  if (window.scrollY > 50) {
    navbar.classList.add("shadow");
    navbar.style.background =
      "linear-gradient(135deg, rgba(15,23,42,.95), rgba(30,41,59,.95))";
  } else {
    navbar.classList.remove("shadow");
    navbar.style.background = "";
  }
});

// ========================================
// Animate on Scroll
// ========================================
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("animate__animated", "animate__fadeInUp");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".card, .service-section, .hero")
    .forEach(el => observer.observe(el));
});

// ========================================
// AUTO HIDE ALERTS
// ========================================
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert").forEach(alert => {
    setTimeout(() => {
      alert.classList.remove("show");
      setTimeout(() => alert.remove(), 150);
    }, 5000);
  });
});

// ========================================
// BOOK SERVICE PAGE (FIXED DEFAULT VEHICLE)
// ========================================
document.addEventListener("DOMContentLoaded", () => {

  const vehicleSelect = document.getElementById("vehicle_type");
  const dateInput = document.getElementById("preferred_date");
  const serviceCheckboxes = document.querySelectorAll(".service-checkbox");
  const bookButton = document.getElementById("bookButton");

  if (!vehicleSelect || serviceCheckboxes.length === 0) return;

  // FILTER SERVICES BY VEHICLE
  function filterServicesByVehicle() {

    const selectedVehicle =
      vehicleSelect.value?.trim().toLowerCase();

    document.querySelectorAll(".service-card-wrapper")
      .forEach(wrapper => {

        const checkbox =
          wrapper.querySelector(".service-checkbox");

        if (!checkbox) return;

        const serviceVehicle =
          (checkbox.dataset.vehicle || "")
          .trim()
          .toLowerCase();

        // SHOW ONLY MATCHING SERVICES
        if (
          serviceVehicle === selectedVehicle ||
          serviceVehicle === "all"
        ) {
          wrapper.style.display = "block";
        } else {
          checkbox.checked = false;
          wrapper.style.display = "none";
        }
      });

    updateBookingSummary();
  }

  // UPDATE SUMMARY
  function updateBookingSummary() {

    const checked =
      document.querySelectorAll(".service-checkbox:checked");

    let totalPrice = 0;
    let totalDuration = 0;

    checked.forEach(cb => {
      totalPrice += parseFloat(cb.dataset.price || 0);

      const card = cb.closest(".service-card");
      const text =
        card?.querySelector(".text-muted")?.innerText || "";

      const duration =
        parseInt(text.replace(/[^0-9]/g, "")) || 0;

      totalDuration += duration;
    });

    document.getElementById("selectedCount").innerText =
      checked.length;

    document.getElementById("totalPrice").innerText =
      totalPrice.toFixed(2);

    document.getElementById("totalDuration").innerText =
      totalDuration;

    const vehicleSelected = vehicleSelect.value !== "";
    const dateSelected = dateInput ? dateInput.value !== "" : true;

    if (bookButton) {
      bookButton.disabled =
        !(checked.length > 0 && vehicleSelected && dateSelected);
    }
  }

  // EVENTS
  vehicleSelect.addEventListener("change", filterServicesByVehicle);

  if (dateInput)
    dateInput.addEventListener("change", updateBookingSummary);

  serviceCheckboxes.forEach(cb =>
    cb.addEventListener("change", updateBookingSummary)
  );

  // ⭐ IMPORTANT FIX (delay ensures default selected value loads)
  setTimeout(() => {
    filterServicesByVehicle();
    updateBookingSummary();
  }, 50);

});

// ========================================
// TOAST HELPERS
// ========================================
function mapCategory(cat) {
  switch (cat) {
    case "success": return "success";
    case "error": return "danger";
    case "warning": return "warning";
    case "info": return "info";
    default: return "secondary";
  }
}

function getIcon(cat) {
  switch (cat) {
    case "success": return "check-circle";
    case "error": return "exclamation-triangle";
    case "warning": return "exclamation-circle";
    case "info": return "info-circle";
    default: return "bell";
  }
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toastEl = document.createElement("div");

  toastEl.className =
    `toast align-items-center text-bg-${mapCategory(type)} border-0`;

  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <i class="fas fa-${getIcon(type)} me-2"></i>${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto"
              data-bs-dismiss="toast"></button>
    </div>
  `;

  container.appendChild(toastEl);
  new bootstrap.Toast(toastEl, { delay: 3000 }).show();
}