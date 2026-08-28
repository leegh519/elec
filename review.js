(() => {
  "use strict";
  const bank = window.QUESTION_BANK || { questions: [], exams: [], taxonomy: { categories: [] } };
  const questions = bank.questions || [];
  const exams = bank.exams || [];
  const taxonomy = bank.taxonomy || { categories: [] };
  const STORAGE_KEY = "electronics-question-bank-review-v1";
  const $ = selector => document.querySelector(selector);
  const els = {
    total: $("#review-total"), reviewed: $("#reviewed-crops"), unresolved: $("#unresolved-count"), classReview: $("#classification-review-count"),
    exam: $("#review-exam"), crop: $("#review-crop-filter"), answer: $("#review-answer-filter"), classification: $("#review-classification-filter"),
    search: $("#review-search"), grid: $("#review-grid"), countLine: $("#review-count-line"), export: $("#export-review"),
    markVisible: $("#mark-visible-ok"), sheetsButton: $("#show-contact-sheets"), sheets: $("#contact-sheet-list"), toast: $("#review-toast")
  };
  let review = loadReview();
  let visible = [];

  function loadReview() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
    catch { return {}; }
  }
  function saveReview() { localStorage.setItem(STORAGE_KEY, JSON.stringify(review)); updateStats(); }
  function option(select, value, label) { const node = document.createElement("option"); node.value = value; node.textContent = label; select.append(node); }
  function initialize() {
    exams.sort((a, b) => b.year - a.year || a.agency.localeCompare(b.agency, "ko")).forEach(exam => option(els.exam, exam.id, `${exam.year} ${exam.agency}`));
    renderSheets();
    render();
    updateStats();
  }
  function updateStats() {
    els.total.textContent = questions.length.toLocaleString("ko-KR");
    els.reviewed.textContent = Object.values(review).filter(item => item.crop === "ok").length.toLocaleString("ko-KR");
    els.unresolved.textContent = questions.filter(question => !question.answer?.choice || !["official", "cross-checked"].includes(question.answer?.status)).length.toLocaleString("ko-KR");
    els.classReview.textContent = questions.filter(question => question.classification?.status !== "approved").length.toLocaleString("ko-KR");
  }
  function filteredQuestions() {
    const query = els.search.value.trim().toLowerCase();
    return questions.filter(question => {
      const local = review[question.id] || {};
      const cropState = local.crop || "pending";
      const verified = Boolean(question.answer?.choice && ["official", "cross-checked"].includes(question.answer?.status));
      const category = taxonomy.categories.find(item => item.id === question.classification?.category);
      const topicIds = question.classification?.topics || (question.classification?.topic ? [question.classification.topic] : []);
      const topicLabels = topicIds.map(topicId => category?.topics?.find(item => item.id === topicId)?.label || topicId);
      const searchable = [question.id, question.ocrText, category?.label, ...topicLabels, ...(question.classification?.concepts || []), ...(question.classification?.auxiliaryTags || [])].join(" ").toLowerCase();
      if (els.exam.value && question.examId !== els.exam.value) return false;
      if (els.crop.value && cropState !== els.crop.value) return false;
      if (els.answer.value === "unresolved" && verified) return false;
      if (els.answer.value === "verified" && !verified) return false;
      if (els.classification.value && question.classification?.status !== els.classification.value) return false;
      if (query && !searchable.includes(query)) return false;
      return true;
    });
  }
  function render() {
    visible = filteredQuestions();
    els.countLine.textContent = `${visible.length.toLocaleString("ko-KR")}문제 표시 중`;
    els.grid.innerHTML = "";
    const fragment = document.createDocumentFragment();
    visible.forEach(question => fragment.append(renderCard(question)));
    els.grid.append(fragment);
  }
  function renderCard(question) {
    const local = review[question.id] || {};
    const category = taxonomy.categories.find(item => item.id === question.classification?.category);
    const topicIds = question.classification?.topics || (question.classification?.topic ? [question.classification.topic] : []);
    const topicLabels = topicIds.map(topicId => category?.topics?.find(item => item.id === topicId)?.label || topicId);
    const card = document.createElement("article");
    card.className = `review-card crop-${local.crop || "pending"}`;
    card.dataset.id = question.id;
    card.innerHTML = `
      <header><div><strong>${question.year} ${question.agency} · ${question.number}번</strong><code>${question.id}</code></div><span class="status-pill">${local.crop === "ok" ? "이미지 확인" : local.crop === "issue" ? "문제 있음" : "미검수"}</span></header>
      <a class="review-image-link" href="${question.image.src}" target="_blank"><img src="${question.image.src}" loading="lazy" alt="${question.id}"></a>
      <dl>
        <div><dt>원본</dt><dd>${question.source.page}쪽 ${question.source.column === "left" ? "왼쪽" : "오른쪽"} 열</dd></div>
        <div><dt>크기</dt><dd>${question.image.width} × ${question.image.height}</dd></div>
        <div><dt>분류</dt><dd>${category?.label || question.classification?.category} › ${topicLabels.join(" · ")}</dd></div>
        <div><dt>세부개념</dt><dd>${(question.classification?.concepts || []).join(", ")}</dd></div>
        <div><dt>정답</dt><dd>${question.answer?.choice ? `${question.answer.choice}번 (${question.answer.status})` : "미확정"}</dd></div>
      </dl>
      <div class="review-card-actions">
        <button class="button crop-ok ${local.crop === "ok" ? "button-primary" : "button-secondary"}" type="button">이미지 정상</button>
        <button class="button crop-issue ${local.crop === "issue" ? "danger-button" : "button-secondary"}" type="button">잘림 문제</button>
      </div>
      <label>검수 메모<textarea rows="2" placeholder="잘린 위치, 정답 출처 등">${escapeHtml(local.note || "")}</textarea></label>`;
    card.querySelector(".crop-ok").addEventListener("click", () => setCrop(question.id, "ok"));
    card.querySelector(".crop-issue").addEventListener("click", () => setCrop(question.id, "issue"));
    card.querySelector("textarea").addEventListener("change", event => { review[question.id] = { ...(review[question.id] || {}), note: event.target.value }; saveReview(); });
    return card;
  }
  function setCrop(id, state) {
    review[id] = { ...(review[id] || {}), crop: state, reviewedAt: new Date().toISOString() };
    saveReview();
    render();
  }
  function renderSheets() {
    els.sheets.innerHTML = exams.sort((a, b) => b.year - a.year || a.agency.localeCompare(b.agency, "ko")).map(exam => `
      <a class="contact-sheet-card" href="review/contact-sheets/${exam.id}.jpg" target="_blank">
        <img src="review/contact-sheets/${exam.id}.jpg" loading="lazy" alt="${exam.title} 접촉 시트">
        <strong>${exam.year}년 ${exam.agency}</strong>
      </a>`).join("");
  }
  function markVisibleOk() {
    if (!visible.length) return;
    if (!confirm(`현재 표시 중인 ${visible.length}문제를 모두 ‘이미지 정상’으로 처리할까요?`)) return;
    visible.forEach(question => { review[question.id] = { ...(review[question.id] || {}), crop: "ok", reviewedAt: new Date().toISOString() }; });
    saveReview(); render(); toast("현재 목록을 이미지 정상으로 처리했습니다.");
  }
  function exportReview() {
    const unresolvedAnswers = questions.filter(question => !question.answer?.choice || !["official", "cross-checked"].includes(question.answer?.status)).map(question => ({ id: question.id, year: question.year, agency: question.agency, number: question.number, image: question.image.src, answer: question.answer }));
    const payload = { version: 1, exportedAt: new Date().toISOString(), review, unresolvedAnswers };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "전자공학개론-검수결과.json"; link.click(); URL.revokeObjectURL(link.href);
  }
  function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]); }
  function toast(message) { els.toast.textContent = message; els.toast.classList.add("is-visible"); clearTimeout(toast.timer); toast.timer = setTimeout(() => els.toast.classList.remove("is-visible"), 3500); }
  [els.exam, els.crop, els.answer, els.classification].forEach(control => control.addEventListener("change", render));
  els.search.addEventListener("input", render);
  els.markVisible.addEventListener("click", markVisibleOk);
  els.export.addEventListener("click", exportReview);
  els.sheetsButton.addEventListener("click", () => { els.sheets.classList.toggle("is-hidden"); els.sheetsButton.textContent = els.sheets.classList.contains("is-hidden") ? "접촉 시트 보기" : "접촉 시트 닫기"; });
  initialize();
})();
