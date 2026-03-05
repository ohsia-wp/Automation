(() => {
  const preferredShifts = [
    "05:00 – 05:30", "05:30 – 06:00", "06:00 – 06:30", "06:30 – 07:00", 
    "07:00 – 07:30", "07:30 – 08:00", "08:00 – 08:30", "08:30 – 09:00",
    "13:00 – 13:30", "13:30 – 14:00", "14:00 – 14:30", "14:30 – 15:00",
    "15:00 – 15:30", "15:30 – 16:00", "16:00 – 16:30", "16:30 – 17:00"
  ];

  // Keep memory of claimed shifts during the session
  const claimedShifts = new Set();

  function normalizeTime(str) {
    return str.replace(/\u00a0/g, " ").trim();
  }

  function clickTakeOpenShiftButton() {
    const confirmBtn = [...document.querySelectorAll("button")]
      .find(btn => btn.textContent.trim() === "Take OpenShift");

    if (confirmBtn) {
      console.log("Confirming 'Take OpenShift'...");
      confirmBtn.click();
    }
  }

  function claimPreferredShifts() {
    const shiftCards = document.querySelectorAll("div.shift-card");
    if (!shiftCards.length) {
      console.log("No open shift cards found yet.");
      return false;
    }

    let claimed = false;
    shiftCards.forEach(card => {
      try {
        const timeHeader = card.querySelector("h3");
        if (!timeHeader) return;

        const shiftTime = normalizeTime(timeHeader.textContent);

        // Skip if not preferred or already claimed
        if (!preferredShifts.includes(shiftTime)) {
          console.log(`Not a preferred shift: ${shiftTime}`);
          return;
        }
        if (claimedShifts.has(shiftTime)) {
          console.log(`Already claimed earlier: ${shiftTime}`);
          return;
        }

        console.log(`Found preferred shift: ${shiftTime}`);
        card.scrollIntoView({ behavior: "smooth", block: "center" });

        const takeShiftButton = [...card.querySelectorAll("button")]
          .find(btn => btn.innerText.includes("Take Shift"));

        if (takeShiftButton) {
          console.log(`Attempting to claim: ${shiftTime}`);
          takeShiftButton.click();

          // Confirm modal after short delay
          setTimeout(() => clickTakeOpenShiftButton(), 1200);

          // Mark as claimed to skip next time
          claimedShifts.add(shiftTime);
          claimed = true;
        } else {
          console.log(`Take Shift button not found for: ${shiftTime}`);
        }

      } catch (err) {
        console.warn("Error processing shift card:", err);
      }
    });

    return claimed;
  }

  // Auto-loop: refresh and retry
  async function loopClaimProcess() {
    console.log("Checking for open shifts...");
    const claimed = claimPreferredShifts();

    if (!claimed) {
      console.log("No new preferred shifts found. Refreshing in 5 seconds...");
      setTimeout(() => location.reload(), 5000);
    } else {
      console.log("Claimed one or more preferred shifts. Checking again in 10 seconds...");
      setTimeout(() => location.reload(), 10000);
    }
  }

  // Start loop
  loopClaimProcess();
})();
