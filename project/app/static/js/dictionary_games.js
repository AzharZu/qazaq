(() => {
  const cfg = window.gameConfig || {};
  const mode = cfg.mode;
  const wordBox = document.querySelector(".vocab-word");
  const feedback = document.getElementById("game-feedback");
  const playBtn = document.getElementById("game-play");
  const nextBtn = document.getElementById("game-next");

  const showFeedback = (text, ok) => {
    if (!feedback) return;
    feedback.textContent = text;
    feedback.className = `vocab-feedback mt-3 ${ok ? "text-success" : "text-danger"}`;
  };

  const updateWord = (data) => {
    if (!data || !data.word) return;
    if (wordBox) wordBox.textContent = data.word;
    const hiddenId = document.querySelector('input[name="word_id"]');
    if (hiddenId) hiddenId.value = data.id;
    feedback && (feedback.textContent = "");
    const answerInput = document.querySelector('.vocab-form input[name="answer"]');
    if (answerInput) answerInput.value = "";
    const optionsBox = document.getElementById("mc-options");
    if (optionsBox && data.options) {
      optionsBox.innerHTML = "";
      data.options.forEach((opt) => {
        const btn = document.createElement("button");
        btn.className = "btn btn-outline-dark";
        btn.textContent = opt;
        btn.dataset.option = opt;
        optionsBox.appendChild(btn);
      });
    }
  };

  const fetchNext = async () => {
    if (!mode) return;
    const res = await fetch(`/vocabulary/game/${mode}?format=json`, { credentials: "include" });
    const data = await res.json();
    if (!data.word || !data.word.id) {
      showFeedback("Нет слов для игры. Добавьте их в словарь.", false);
      return;
    }
    data.word.options = data.options;
    updateWord({ ...data.word, options: data.options });
  };

  playBtn?.addEventListener("click", async () => {
    const current = document.querySelector(".vocab-word")?.textContent;
    if (!current) return;
    try {
      const res = await fetch(`/tts?word=${encodeURIComponent(current)}`, { credentials: "include" });
      const data = await res.json();
      if (data?.url) {
        new Audio(data.url).play().catch(() => {});
      }
    } catch (e) {
      // noop
    }
  });

  nextBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    fetchNext();
  });

  // repeat mode
  const repeatForm = document.getElementById("repeat-form");
  repeatForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(repeatForm);
    const res = await fetch("/vocabulary/game/repeat/check", { method: "POST", body: fd, credentials: "include" });
    const result = await res.json();
    if (result.correct) {
      showFeedback("✔ Правильно", true);
      postXP();
      setTimeout(fetchNext, 700);
    } else {
      const hint = result.correct_answer ? `Правильно: ${result.correct_answer}` : result.hint || "Неверно";
      showFeedback(hint, false);
    }
  });

  // mc mode
  const mcBox = document.getElementById("mc-options");
  mcBox?.addEventListener("click", async (e) => {
    const target = e.target;
    if (!(target instanceof HTMLElement) || !target.dataset.option) return;
    e.preventDefault();
    const hiddenId = document.querySelector('input[name="word_id"]');
    const fd = new FormData();
    fd.append("word_id", hiddenId?.value || "");
    fd.append("selected", target.dataset.option);
    const res = await fetch("/vocabulary/game/mc/check", { method: "POST", body: fd, credentials: "include" });
    const result = await res.json();
    if (result.correct) {
      showFeedback("✔ Верно", true);
      postXP();
      setTimeout(fetchNext, 700);
    } else {
      const correct = result.correct_answer ? `Правильно: ${result.correct_answer}` : "Неверно";
      showFeedback(correct, false);
    }
  });

  // write mode
  const writeForm = document.getElementById("write-form");
  writeForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(writeForm);
    const res = await fetch("/vocabulary/game/write/check", { method: "POST", body: fd, credentials: "include" });
    const result = await res.json();
    if (result.correct) {
      showFeedback("✔ Отлично", true);
      postXP();
      setTimeout(fetchNext, 700);
    } else {
      const correct = result.correct_answer ? `Правильно: ${result.correct_answer}` : "Неверно";
      const hint = result.hint ? ` · ${result.hint}` : "";
      showFeedback(correct + hint, false);
    }
  });

  async function postXP(amount = 1) {
    try {
      await fetch("/xp/add", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ xp: amount, reason: "vocabulary_game" }),
      });
    } catch (e) {
      // optional endpoint
    }
  }
})();
