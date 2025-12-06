(() => {
  const data = window.flashcardsData || { cards: [] };
  let cards = Array.isArray(data.cards) ? data.cards : [];

  const learnedCheckbox = document.getElementById("dict-learned");
  const learnedLabel = document.getElementById("dict-learned-label");
  const weekPlay = document.getElementById("week-play");

  const controller = Flashcards.init({
    cards,
    initialIndex: data.initialIndex || 0,
    onChange: handleChange,
    containerId: "flashcard-container",
    arrowPrev: "#vocab-prev",
    arrowNext: "#vocab-next",
    flipButton: "#flip-btn",
    flipBackButton: "#flip-back-btn",
    speakButton: "#speak-btn",
  });

  function handleChange(card) {
    if (!learnedCheckbox) return;
    if (!card) {
      learnedCheckbox.checked = false;
      learnedCheckbox.disabled = true;
      learnedLabel?.classList.add("d-none");
      return;
    }
    learnedCheckbox.disabled = false;
    learnedCheckbox.checked = !!card.learned;
    learnedLabel?.classList.toggle("d-none", !card.learned);
  }

  learnedCheckbox?.addEventListener("change", async () => {
    const current = controller.current();
    if (!current || !learnedCheckbox.checked) return;
    await fetch(`/vocabulary/learn/${current.id}`, { method: "POST", credentials: "include" });
    cards = cards.filter((c) => c.id !== current.id);
    controller.setCards(cards, 0);
  });

  weekPlay?.addEventListener("click", () => {
    const word = weekPlay.dataset.weekWord;
    if (word) Flashcards.speak(word);
  });
})();
