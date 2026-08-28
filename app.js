(() => {
  "use strict";

  const bank = window.QUESTION_BANK || { questions: [], exams: [], taxonomy: { categories: [], auxiliaryTags: {} } };
  const questions = bank.questions || [];
  const taxonomy = bank.taxonomy || { categories: [], auxiliaryTags: {} };
  const STORAGE_KEY = "electronics-question-bank-progress-v1";
  const choiceLabels = ["①", "②", "③", "④", "⑤"];

  const $ = (selector) => document.querySelector(selector);
  const els = {
    total: $("#total-count"), solved: $("#solved-count"), wrong: $("#wrong-count"),
    agency: $("#agency-filter"), year: $("#year-filter"), category: $("#category-filter"),
    topic: $("#topic-filter"), history: $("#history-filter"), resetFilters: $("#reset-filters"), order: $("#order-filter"),
    resultCount: $("#filter-result"), modeInputs: [...document.querySelectorAll("input[name='mode']")],
    batchWrap: $("#batch-size-wrap"), batchSize: $("#batch-size"),
    setup: $("#setup-panel"), practice: $("#practice-panel"), list: $("#question-list"),
    start: $("#start-practice"), back: $("#back-to-setup"), title: $("#practice-title"), progress: $("#practice-progress"),
    toggleAllMeta: $("#toggle-all-meta"), batchActions: $("#batch-actions"), batchState: $("#batch-answer-state"),
    gradeBatch: $("#grade-batch"), result: $("#result-panel"), toast: $("#toast"),
    exportProgress: $("#export-progress"), importProgress: $("#import-progress")
  };

  let progressData = loadProgress();
  let activeMode = "single";
  let activeQuestions = [];
  let singleIndex = 0;
  let answers = new Map();
  let metadataVisible = new Set();
  let allMetadataVisible = false;
  let batchGraded = false;
  const selectedAgencies = new Set();
  const selectedYears = new Set();
  const selectedCategories = new Set();
  const selectedTopics = new Set();
  const selectedHistories = new Set();

  function loadProgress() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
    catch { return {}; }
  }

  function saveProgress() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progressData));
    updateDashboard();
  }

  function updateDashboard() {
    const records = Object.values(progressData);
    els.total.textContent = questions.length.toLocaleString("ko-KR");
    els.solved.textContent = records.filter(record => record.attempts > 0).length.toLocaleString("ko-KR");
    els.wrong.textContent = records.filter(record => record.wrong > 0).length.toLocaleString("ko-KR");
  }

  function initializeFilters() {
    const years = [...new Set(questions.map(q => q.year))].sort((a, b) => a - b);
    renderCheckGroup(els.agency, ["국가직", "지방직", "군무원", "국회직", "서울시"].map(value => ({ value, label: value })), selectedAgencies);
    renderCheckGroup(els.year, years.map(year => ({ value: String(year), label: `${year}년` })), selectedYears);
    renderCheckGroup(els.category, taxonomy.categories.map(category => ({ value: category.id, label: category.label })), selectedCategories);
    renderCheckGroup(els.history, [
      { value: "unseen", label: "미풀이" },
      { value: "wrong", label: "오답" },
      { value: "favorite", label: "즐겨찾기" }
    ], selectedHistories);
    updateDependentFilters();
  }

  function renderCheckGroup(container, items, selected) {
    container.innerHTML = items.map(({ value, label }) => `
      <label class="topic-check ${selected.has(value) ? "is-selected" : ""}">
        <input type="checkbox" value="${escapeHtml(value)}" ${selected.has(value) ? "checked" : ""}>
        <span>${escapeHtml(label)}</span>
      </label>`).join("");
  }

  function updateDependentFilters() {
    const categories = selectedCategories.size
      ? taxonomy.categories.filter(category => selectedCategories.has(category.id))
      : taxonomy.categories;
    const availableTopics = categories.flatMap(category => category.topics || []);
    const availableIds = new Set(availableTopics.map(topic => topic.id));
    [...selectedTopics].forEach(topic => { if (!availableIds.has(topic)) selectedTopics.delete(topic); });
    renderCheckGroup(els.topic, availableTopics.map(topic => ({ value: topic.id, label: topic.label })), selectedTopics);
    updateFilterCount();
  }

  function getFilteredQuestions() {
    return questions.filter(question => {
      const record = progressData[question.id] || {};
      const classification = question.classification || {};
      if (selectedAgencies.size && !selectedAgencies.has(question.agency)) return false;
      if (selectedYears.size && !selectedYears.has(String(question.year))) return false;
      if (selectedCategories.size && !selectedCategories.has(classification.category)) return false;
      const questionTopics = classification.topics || (classification.topic ? [classification.topic] : []);
      if (selectedTopics.size && !questionTopics.some(topic => selectedTopics.has(topic))) return false;
      if (selectedHistories.size && ![...selectedHistories].some(history => {
        if (history === "unseen") return !record.attempts;
        if (history === "wrong") return Boolean(record.wrong);
        return Boolean(record.favorite);
      })) return false;
      return true;
    });
  }

  function updateFilterCount() {
    const count = getFilteredQuestions().length;
    els.resultCount.textContent = `${count.toLocaleString("ko-KR")}문제`;
    els.start.disabled = count === 0;
  }

  function shuffle(items) {
    const result = [...items];
    for (let index = result.length - 1; index > 0; index -= 1) {
      const swap = Math.floor(Math.random() * (index + 1));
      [result[index], result[swap]] = [result[swap], result[index]];
    }
    return result;
  }

  function startPractice() {
    const pool = getFilteredQuestions();
    if (!pool.length) return;
    activeMode = els.modeInputs.find(input => input.checked)?.value || "single";
    const ordered = els.order.value === "random"
      ? shuffle(pool)
      : [...pool].sort((a, b) => a.year - b.year || a.agency.localeCompare(b.agency, "ko") || a.number - b.number);
    activeQuestions = activeMode === "batch" ? ordered.slice(0, Math.min(Number(els.batchSize.value), ordered.length)) : ordered;
    singleIndex = 0;
    answers = new Map();
    metadataVisible = new Set();
    allMetadataVisible = false;
    batchGraded = false;
    els.toggleAllMeta.textContent = "전체 분류 표시";
    els.result.classList.add("is-hidden");
    els.result.innerHTML = "";
    els.setup.classList.add("is-hidden");
    els.practice.classList.remove("is-hidden");
    renderPractice();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function renderPractice() {
    els.list.innerHTML = "";
    if (activeMode === "single") {
      const question = activeQuestions[singleIndex];
      els.title.textContent = "한 문제씩 풀기";
      els.progress.textContent = `${singleIndex + 1} / ${activeQuestions.length}`;
      els.list.append(renderQuestion(question, false));
      els.batchActions.classList.add("is-hidden");
    } else {
      els.title.textContent = `${activeQuestions.length}문제 모아풀기`;
      els.progress.textContent = "한 화면에서 답을 고른 뒤 일괄 채점하세요";
      activeQuestions.forEach(question => els.list.append(renderQuestion(question, true)));
      els.batchActions.classList.remove("is-hidden");
      updateBatchState();
    }
  }

  function renderQuestion(question, isBatch) {
    const card = document.createElement("article");
    card.className = "question-card";
    card.dataset.id = question.id;
    const record = progressData[question.id] || {};
    const metaShown = allMetadataVisible || metadataVisible.has(question.id);
    const classification = question.classification || {};
    const chips = [
      { label: categoryLabel(classification.category), type: "category" },
      ...(classification.topics || (classification.topic ? [classification.topic] : [])).map(topic => ({ label: topicLabel(classification.category, topic), type: "topic" })),
      ...(classification.concepts || []).map(label => ({ label, type: "concept" })),
      ...(classification.auxiliaryTags || []).map(label => ({ label, type: "tag" })),
      ...(classification.questionTypes || []).map(label => ({ label, type: "tag" }))
    ].filter(chip => chip.label);
    const selected = answers.get(question.id);
    const choiceCount = question.choiceCount || (question.agency === "국회직" ? 5 : 4);
    const visibleChoiceLabels = choiceLabels.slice(0, choiceCount);
    card.innerHTML = `
      <header class="question-head">
        <div class="question-source"><strong>문 ${question.number}</strong><span>${question.year}년 ${question.agency}</span></div>
        <div class="question-tools">
          <button class="tool-button favorite ${record.favorite ? "is-active" : ""}" type="button">${record.favorite ? "★ 즐겨찾기" : "☆ 즐겨찾기"}</button>
          <button class="tool-button metadata-toggle" type="button">${metaShown ? "분류 가리기" : "분류 보기"}</button>
          <button class="tool-button copy-image" type="button">이미지 복사</button>
          <a class="tool-button" href="${question.image.src}" download="${question.id}.png">PNG 저장</a>
        </div>
      </header>
      <div class="problem-image-wrap"><img class="problem-image" src="${question.image.src}" alt="${question.year}년 ${question.agency} ${question.number}번 문제"></div>
      <div class="metadata ${metaShown ? "" : "is-hidden"}">${chips.map(chip => `<span class="chip ${chip.type === "concept" || chip.type === "tag" ? "concept" : ""}">${escapeHtml(chip.label)}</span>`).join("")}</div>
      <div class="answer-area">
        <div class="choices" role="group" aria-label="${question.number}번 답 선택">
          ${visibleChoiceLabels.map((label, index) => `<button class="choice ${selected === index + 1 ? "is-selected" : ""}" data-choice="${index + 1}" type="button">${label}</button>`).join("")}
        </div>
        <p class="answer-note">${question.answer?.choice ? "답을 선택하세요." : "정답 미확정 문제입니다. 선택은 저장되지만 채점에는 포함되지 않습니다."}</p>
        ${isBatch ? "" : '<div class="single-actions"><button class="button button-primary grade-single" type="button">채점</button><button class="button button-secondary next-single is-hidden" type="button">다음 문제</button></div>'}
      </div>`;

    card.querySelectorAll(".choice").forEach(button => button.addEventListener("click", () => selectAnswer(question, Number(button.dataset.choice), card)));
    card.querySelector(".favorite").addEventListener("click", event => toggleFavorite(question, event.currentTarget));
    card.querySelector(".metadata-toggle").addEventListener("click", () => toggleMetadata(question.id, card));
    card.querySelector(".copy-image").addEventListener("click", event => copyQuestionImage(question, card.querySelector("img"), event.currentTarget));
    if (!isBatch) {
      card.querySelector(".grade-single").addEventListener("click", () => gradeQuestion(question, card));
      card.querySelector(".next-single").addEventListener("click", nextSingle);
    }
    return card;
  }

  function selectAnswer(question, choice, card) {
    if (card.dataset.graded === "true") return;
    answers.set(question.id, choice);
    card.querySelectorAll(".choice").forEach(button => button.classList.toggle("is-selected", Number(button.dataset.choice) === choice));
    if (activeMode === "batch") updateBatchState();
  }

  function gradeQuestion(question, card) {
    const selected = answers.get(question.id);
    if (!selected) { toast("답을 먼저 선택하세요."); return; }
    applyGrade(question, card, selected);
    card.querySelector(".grade-single").classList.add("is-hidden");
    card.querySelector(".next-single").classList.remove("is-hidden");
  }

  function applyGrade(question, card, selected) {
    card.dataset.graded = "true";
    const note = card.querySelector(".answer-note");
    const correct = question.answer?.choice;
    const verified = ["official", "cross-checked"].includes(question.answer?.status);
    const provisionalSuffix = correct && !verified ? " (잠정 정답 기준)" : "";
    const record = progressData[question.id] || { attempts: 0, correct: 0, wrong: 0, favorite: false };
    record.attempts += 1;
    record.lastAnswer = selected;
    record.lastAttemptAt = new Date().toISOString();
    if (!correct) {
      note.textContent = `선택 ${choiceLabels[selected - 1]} · 정답 미확정으로 채점에서 제외됩니다.`;
      note.className = "answer-note";
    } else if (selected === correct) {
      record.correct += 1;
      card.classList.add("is-correct");
      note.textContent = `정답입니다. (${choiceLabels[correct - 1]})${provisionalSuffix}`;
      note.className = "answer-note success";
    } else {
      record.wrong += 1;
      card.classList.add("is-wrong");
      note.textContent = `오답입니다. 정답은 ${choiceLabels[correct - 1]}입니다.${provisionalSuffix}`;
      note.className = "answer-note error";
    }
    card.querySelectorAll(".choice").forEach(button => {
      const value = Number(button.dataset.choice);
      button.disabled = true;
      if (correct && value === correct) button.classList.add("is-answer");
      if (correct && value === selected && value !== correct) button.classList.add("is-incorrect");
    });
    progressData[question.id] = record;
    saveProgress();
  }

  function nextSingle() {
    if (singleIndex + 1 >= activeQuestions.length) {
      showResult("선택한 조건의 문제를 모두 풀었습니다.");
      return;
    }
    singleIndex += 1;
    renderPractice();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function gradeBatch() {
    if (batchGraded) return;
    const unanswered = activeQuestions.filter(question => !answers.has(question.id));
    if (unanswered.length && !window.confirm(`${unanswered.length}문제가 미응답입니다. 그대로 채점할까요?`)) return;
    batchGraded = true;
    let correctCount = 0;
    let wrongCount = 0;
    let unresolvedCount = 0;
    activeQuestions.forEach(question => {
      const card = els.list.querySelector(`[data-id="${question.id}"]`);
      const selected = answers.get(question.id);
      if (!selected) return;
      applyGrade(question, card, selected);
      if (!question.answer?.choice) unresolvedCount += 1;
      else if (selected === question.answer.choice) correctCount += 1;
      else wrongCount += 1;
    });
    const gradable = correctCount + wrongCount;
    showResult(`채점 가능 ${gradable}문제 중 ${correctCount}문제 정답`, `오답 ${wrongCount}문제 · 정답 미확정 ${unresolvedCount}문제`);
    els.gradeBatch.disabled = true;
  }

  function showResult(title, detail = "") {
    els.result.innerHTML = `<h3>${escapeHtml(title)}</h3>${detail ? `<p>${escapeHtml(detail)}</p>` : ""}<p>오답 문제는 다음 풀이에서 ‘오답’ 필터로 다시 선택할 수 있습니다.</p>`;
    els.result.classList.remove("is-hidden");
    els.result.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function updateBatchState() {
    els.batchState.textContent = `${answers.size} / ${activeQuestions.length}문제 응답`;
  }

  function toggleFavorite(question, button) {
    const record = progressData[question.id] || { attempts: 0, correct: 0, wrong: 0, favorite: false };
    record.favorite = !record.favorite;
    progressData[question.id] = record;
    button.classList.toggle("is-active", record.favorite);
    button.textContent = record.favorite ? "★ 즐겨찾기" : "☆ 즐겨찾기";
    saveProgress();
  }

  function toggleMetadata(id, card) {
    if (metadataVisible.has(id)) metadataVisible.delete(id); else metadataVisible.add(id);
    const visible = allMetadataVisible || metadataVisible.has(id);
    card.querySelector(".metadata").classList.toggle("is-hidden", !visible);
    card.querySelector(".metadata-toggle").textContent = visible ? "분류 가리기" : "분류 보기";
  }

  function toggleAllMetadata() {
    allMetadataVisible = !allMetadataVisible;
    els.toggleAllMeta.textContent = allMetadataVisible ? "전체 분류 가리기" : "전체 분류 표시";
    els.list.querySelectorAll(".question-card").forEach(card => {
      const visible = allMetadataVisible || metadataVisible.has(card.dataset.id);
      card.querySelector(".metadata").classList.toggle("is-hidden", !visible);
      card.querySelector(".metadata-toggle").textContent = visible ? "분류 가리기" : "분류 보기";
    });
  }

  async function imageBlobFromElement(image) {
    if (!image.complete) await image.decode();
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    canvas.getContext("2d").drawImage(image, 0, 0);
    return new Promise((resolve, reject) => canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error("PNG 변환 실패")), "image/png"));
  }

  async function copyQuestionImage(question, image, button) {
    const oldLabel = button.textContent;
    button.textContent = "복사 중…";
    try {
      if (!navigator.clipboard?.write || typeof ClipboardItem === "undefined") throw new Error("Clipboard API 미지원");
      const blobPromise = imageBlobFromElement(image);
      await navigator.clipboard.write([new ClipboardItem({ "image/png": blobPromise })]);
      toast("문제 이미지를 클립보드에 복사했습니다.");
    } catch (error) {
      const link = document.createElement("a");
      link.href = question.image.src;
      link.download = `${question.id}.png`;
      link.click();
      toast("브라우저가 이미지 복사를 차단해 PNG를 저장했습니다. 또는 문제 이미지를 우클릭해 복사하세요.");
    } finally {
      button.textContent = oldLabel;
    }
  }

  function categoryLabel(id) {
    return taxonomy.categories.find(category => category.id === id)?.label || id;
  }

  function topicLabel(categoryId, topicId) {
    const category = taxonomy.categories.find(item => item.id === categoryId);
    return category?.topics?.find(topic => topic.id === topicId)?.label || topicId;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
  }

  function toast(message) {
    els.toast.textContent = message;
    els.toast.classList.add("is-visible");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => els.toast.classList.remove("is-visible"), 4200);
  }

  function exportProgress() {
    const blob = new Blob([JSON.stringify({ version: 1, exportedAt: new Date().toISOString(), progress: progressData }, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "전자공학개론-풀이기록.json";
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function importProgress(file) {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(reader.result);
        progressData = parsed.progress || parsed;
        saveProgress();
        updateFilterCount();
        toast("풀이 기록을 가져왔습니다.");
      } catch { toast("올바른 풀이 기록 JSON이 아닙니다."); }
    };
    reader.readAsText(file);
  }

  function handleCheckGroupChange(event, selected, onChange = updateFilterCount) {
    if (!event.target.matches("input[type='checkbox']")) return;
    if (event.target.checked) selected.add(event.target.value); else selected.delete(event.target.value);
    event.target.closest(".topic-check")?.classList.toggle("is-selected", event.target.checked);
    onChange();
  }

  function resetFilters() {
    [selectedAgencies, selectedYears, selectedCategories, selectedTopics, selectedHistories].forEach(selected => selected.clear());
    initializeFilters();
    toast("필터를 초기화했습니다.");
  }

  els.agency.addEventListener("change", event => handleCheckGroupChange(event, selectedAgencies));
  els.year.addEventListener("change", event => handleCheckGroupChange(event, selectedYears));
  els.category.addEventListener("change", event => handleCheckGroupChange(event, selectedCategories, updateDependentFilters));
  els.topic.addEventListener("change", event => handleCheckGroupChange(event, selectedTopics));
  els.history.addEventListener("change", event => handleCheckGroupChange(event, selectedHistories));
  els.resetFilters.addEventListener("click", resetFilters);
  els.modeInputs.forEach(input => input.addEventListener("change", () => els.batchWrap.classList.toggle("is-hidden", input.value === "single" && input.checked)));
  els.start.addEventListener("click", startPractice);
  els.back.addEventListener("click", () => { els.practice.classList.add("is-hidden"); els.setup.classList.remove("is-hidden"); window.scrollTo({ top: 0, behavior: "smooth" }); });
  els.toggleAllMeta.addEventListener("click", toggleAllMetadata);
  els.gradeBatch.addEventListener("click", gradeBatch);
  els.exportProgress.addEventListener("click", exportProgress);
  els.importProgress.addEventListener("change", event => event.target.files[0] && importProgress(event.target.files[0]));

  initializeFilters();
  updateDashboard();
  updateFilterCount();
  els.batchWrap.classList.add("is-hidden");
})();
