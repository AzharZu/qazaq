async function postXP(amount = 1) {
  try {
    await fetch("/xp/add", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ xp: amount, reason: "vocabulary_game" }),
    });
  } catch (e) {
    // optional endpoint, ignore failures
  }
}

async function startRepeatGame() {
  const box = document.getElementById("repeat-feedback");
  box.textContent = "Загружаю слово...";
  const res = await fetch("/vocabulary/game/repeat?format=json", { credentials: "include" });
  const data = await res.json();
  const word = data.word;
  if (!word || !word.id) {
    box.textContent = "Нет слов для игры.";
    return;
  }
  const answer = prompt(`Прослушайте слово и введите его:\n${word.word}`);
  if (word.word) {
    const utter = new SpeechSynthesisUtterance(word.word);
    speechSynthesis.speak(utter);
  }
  if (answer === null) return;
  const form = new FormData();
  form.append("word_id", word.id);
  form.append("answer", answer);
  const check = await fetch("/vocabulary/game/repeat/check", { method: "POST", body: form, credentials: "include" });
  const result = await check.json();
  if (result.correct) {
    box.textContent = "✔ Правильно";
    box.className = "game-feedback small text-success";
  } else {
    const correct = result.correct_answer ? `Правильно: ${result.correct_answer}` : "";
    const hint = result.hint || "";
    box.textContent = correct || hint || "Неверно";
    box.className = "game-feedback small text-danger";
  }
  if (result.correct) postXP();
}

async function startChooseGame() {
  const box = document.getElementById("choose-feedback");
  box.textContent = "Загружаю слово...";
  const res = await fetch("/vocabulary/game/mc?format=json", { credentials: "include" });
  const data = await res.json();
  const word = data.word;
  const options = data.options || [];
  if (!word || !word.id) {
    box.textContent = "Нет слов для игры.";
    return;
  }
  const picked = prompt(`${word.word}\n\nВарианты:\n${options.map((o, i) => `${i + 1}) ${o}`).join("\n")}\nВведите номер варианта`);
  if (picked === null) return;
  const choice = options[Number(picked) - 1] || "";
  const form = new FormData();
  form.append("word_id", word.id);
  form.append("selected", choice);
  const check = await fetch("/vocabulary/game/mc/check", { method: "POST", body: form, credentials: "include" });
  const result = await check.json();
  if (result.correct) {
    box.textContent = "✔ Верно";
    box.className = "game-feedback small text-success";
  } else {
    const correct = result.correct_answer ? `Правильно: ${result.correct_answer}` : "Неверно";
    box.textContent = correct;
    box.className = "game-feedback small text-danger";
  }
  if (result.correct) postXP();
}

async function startWriteGame() {
  const box = document.getElementById("write-feedback");
  box.textContent = "Загружаю слово...";
  const res = await fetch("/vocabulary/game/write?format=json", { credentials: "include" });
  const data = await res.json();
  const word = data.word;
  if (!word || !word.id) {
    box.textContent = "Нет слов для игры.";
    return;
  }
  const answer = prompt(`${word.word}\nВведите перевод:`);
  if (answer === null) return;
  const form = new FormData();
  form.append("word_id", word.id);
  form.append("answer", answer);
  const check = await fetch("/vocabulary/game/write/check", { method: "POST", body: form, credentials: "include" });
  const result = await check.json();
  if (result.correct) {
    box.textContent = "✔ Отлично";
    box.className = "game-feedback small text-success";
  } else {
    const correct = result.correct_answer ? `Правильно: ${result.correct_answer}` : "Неверно";
    const hint = result.hint ? ` · ${result.hint}` : "";
    box.textContent = correct + hint;
    box.className = "game-feedback small text-danger";
  }
  if (result.correct) postXP();
}

function startRepeatGameManual(word) {
  if (word) {
    const utter = new SpeechSynthesisUtterance(word);
    speechSynthesis.speak(utter);
  }
}

function submitGameAnswer() {
  // Placeholder hook to align with prompt; logic handled per-game above.
}
