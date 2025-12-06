(() => {
  function speak(word) {
    if (!word) return;
    const msg = new SpeechSynthesisUtterance(word);
    msg.lang = "kk-KZ";
    const voices = speechSynthesis.getVoices();
    const kk = voices.find((v) => (v.lang || "").toLowerCase().startsWith("kk"));
    if (kk) msg.voice = kk;
    speechSynthesis.cancel();
    speechSynthesis.speak(msg);
  }

  function initFlashcards(config) {
    const cfg = config || {};
    let cards = cfg.cards || [];
    let idx = cfg.initialIndex || 0;
    let flipped = false;

    const container = document.getElementById(cfg.containerId || "flashcard-container");
    const cardEl = container?.querySelector(".flashcard");
    const frontWord = container?.querySelector("#card-front-word");
    const backRu = container?.querySelector("#card-back-ru");
    const backMeaning = container?.querySelector("#card-back-meaning");
    const backExample = container?.querySelector("#card-back-example");
    const emptyState = "Пока нет слов";

    function current() {
      return cards[idx] || null;
    }

    function render() {
      const c = current();
      if (!cardEl) return;
      if (!c) {
        frontWord && (frontWord.textContent = emptyState);
        backRu && (backRu.textContent = "Перевод");
        backMeaning && (backMeaning.textContent = "");
        backExample && (backExample.textContent = "");
        cardEl.classList.remove("is-flipped");
        flipped = false;
        cfg.onChange && cfg.onChange(null);
        return;
      }
      frontWord && (frontWord.textContent = c.kz || "");
      backRu && (backRu.textContent = c.ru || "");
      backMeaning && (backMeaning.textContent = c.meaning || "");
      backExample && (backExample.textContent = c.example ? `Пример: ${c.example}` : "");
      cardEl.classList.toggle("is-flipped", flipped);
      cfg.onChange && cfg.onChange(c, idx);
    }

    function flip() {
      flipped = !flipped;
      cardEl?.classList.toggle("is-flipped", flipped);
    }

    function next() {
      if (!cards.length) return;
      idx = (idx + 1) % cards.length;
      flipped = false;
      render();
    }

    function prev() {
      if (!cards.length) return;
      idx = (idx - 1 + cards.length) % cards.length;
      flipped = false;
      render();
    }

    function setCards(newCards, newIndex = 0) {
      cards = newCards || [];
      idx = Math.min(Math.max(newIndex, 0), Math.max(cards.length - 1, 0));
      flipped = false;
      render();
    }

    const bind = (selector, fn) => {
      const el = typeof selector === "string" ? document.querySelector(selector) : selector;
      el && el.addEventListener("click", (e) => {
        e.preventDefault();
        fn();
      });
    };

    bind(cfg.arrowPrev || "#vocab-prev", prev);
    bind(cfg.arrowNext || "#vocab-next", next);
    bind(cfg.flipButton || "#flip-btn", flip);
    bind(cfg.flipBackButton || "#flip-back-btn", flip);
    bind(cfg.speakButton || "#speak-btn", () => speak(current()?.kz));

    render();
    return { next, prev, flip, speakCurrent: () => speak(current()?.kz), current, setCards };
  }

  window.Flashcards = { init: initFlashcards, speak };
})();
