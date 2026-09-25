// Apex Core Banking System - Client Interactions
document.addEventListener("DOMContentLoaded", () => {
    // 1. Mobile Menu Toggle
    const mobileToggle = document.getElementById("mobileMenuToggle");
    const navMenu = document.getElementById("navMenu");

    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener("click", () => {
            navMenu.classList.toggle("show");
        });
    }

    // 2. Auto-dismiss flash notifications after 6 seconds
    const flashAlerts = document.querySelectorAll(".flash-alert");
    flashAlerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-6px)";
            setTimeout(() => alert.remove(), 400);
        }, 6000);
    });

    // 3. Quick Amount Preset Chips (Deposit & Withdraw Pages)
    const amountInput = document.getElementById("amountInput");
    const chipButtons = document.querySelectorAll(".chip-btn");

    if (amountInput && chipButtons.length > 0) {
        chipButtons.forEach((chip) => {
            chip.addEventListener("click", (e) => {
                e.preventDefault();
                const addValue = parseFloat(chip.dataset.amount);
                const currentValue = parseFloat(amountInput.value) || 0;
                // If user clicks a preset, set or add value
                amountInput.value = (currentValue + addValue).toFixed(2);
                amountInput.focus();
            });
        });
    }

    // 4. Strict Numeric Input Enforcement (Phone, PIN, Account Number)
    const numericInputs = document.querySelectorAll("input[data-numeric='true']");
    numericInputs.forEach((input) => {
        input.addEventListener("input", (e) => {
            const clean = e.target.value.replace(/\D/g, "");
            const maxLength = e.target.getAttribute("maxlength");
            if (maxLength) {
                e.target.value = clean.slice(0, parseInt(maxLength));
            } else {
                e.target.value = clean;
            }
        });
    });

    // 5. PIN Match Verification on Register & Change PIN
    const newPin = document.getElementById("newPin");
    const confirmPin = document.getElementById("confirmPin");
    const pinMatchNotice = document.getElementById("pinMatchNotice");

    if (newPin && confirmPin && pinMatchNotice) {
        const verifyPinMatch = () => {
            if (!confirmPin.value) {
                pinMatchNotice.textContent = "";
                return;
            }
            if (newPin.value === confirmPin.value) {
                pinMatchNotice.textContent = "✓ PINs match";
                pinMatchNotice.style.color = "#059669";
            } else {
                pinMatchNotice.textContent = "✕ PINs do not match";
                pinMatchNotice.style.color = "#dc2626";
            }
        };

        newPin.addEventListener("input", verifyPinMatch);
        confirmPin.addEventListener("input", verifyPinMatch);
    }
});
