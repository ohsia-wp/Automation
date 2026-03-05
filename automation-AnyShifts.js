(() => {
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

  async function claimAllOpenShifts() {
    const shiftCards = document.querySelectorAll("div.shift-card");
    if (!shiftCards.length) {
      console.log("No open shift cards found yet.");
      return false;
    }

    let foundAny = false;
    for (const card of shiftCards) {
      try {
        const timeHeader = card.querySelector("h3");
        if (!timeHeader) continue;

        const shiftTime = normalizeTime(timeHeader.textContent);
        if (claimedShifts.has(shiftTime)) {
          console.log(`Already claimed earlier: ${shiftTime}`);
          continue;
        }

        const takeShiftButton = [...card.querySelectorAll("button")]
          .find(btn => btn.innerText.includes("Take Shift"));

        if (takeShiftButton) {
          console.log(`Attempting to claim: ${shiftTime}`);
          card.scrollIntoView({ behavior: "smooth", block: "center" });
          takeShiftButton.click();
          foundAny = true;

          // Wait for modal and confirm
          await new Promise(r => setTimeout(r, 1200));
          clickTakeOpenShiftButton();

          claimedShifts.add(shiftTime);
          // Small delay before next claim
          await new Promise(r => setTimeout(r, 2000));
        } else {
          console.log(`Take Shift button not found for: ${shiftTime}`);
        }
      } catch (err) {
        console.warn("Error processing shift card:", err);
      }
    }

    return foundAny;
  }

  async function loopClaimProcess() {
    console.log("Checking for open shifts...");
    const found = await claimAllOpenShifts();

    if (found) {
      console.log("Claimed all available shifts! Checking again in 10 seconds...");
      setTimeout(loopClaimProcess, 10000); // stay on the same page
    } else {
      console.log("No open shifts found. Refreshing page in 5 seconds...");
      setTimeout(() => location.reload(), 5000);
    }
  }

  // Start automation
  loopClaimProcess();
})();
