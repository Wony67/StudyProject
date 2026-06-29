const DATA_URL = "data/processed/past_questions.json";
const EXPECTED_DATA_URL = "data/processed/expected_questions.json";

const state = {
  mode: "past",
  pastQuestions: [],
  expectedQuestions: [],
  questions: [],
  filtered: [],
  currentIndex: 0,
  answerVisible: false,
  answerDefaultVisible: false,
  expectedView: "fixed",
  randomSeed: "",
  randomQuestions: [],
};

const elements = {
  pastMode: document.querySelector("#past-mode-button"),
  expectedMode: document.querySelector("#expected-mode-button"),
  pageTitle: document.querySelector("#page-title"),
  count: document.querySelector("#question-count"),
  status: document.querySelector("#load-status"),
  year: document.querySelector("#year-select"),
  round: document.querySelector("#round-select"),
  number: document.querySelector("#number-select"),
  category: document.querySelector("#category-select"),
  mix: document.querySelector("#mix-select"),
  shuffle: document.querySelector("#shuffle-button"),
  prev: document.querySelector("#prev-button"),
  next: document.querySelector("#next-button"),
  examTitle: document.querySelector("#exam-title"),
  progress: document.querySelector("#exam-progress"),
  list: document.querySelector("#question-list"),
  badge: document.querySelector("#question-badge"),
  source: document.querySelector("#source-link"),
  title: document.querySelector("#question-title"),
  question: document.querySelector("#question-text"),
  tableArea: document.querySelector("#table-area"),
  descriptionArea: document.querySelector("#description-area"),
  detailArea: document.querySelector("#detail-area"),
  optionArea: document.querySelector("#option-area"),
  choiceArea: document.querySelector("#choice-area"),
  targetArea: document.querySelector("#target-area"),
  codeArea: document.querySelector("#code-area"),
  imageArea: document.querySelector("#image-area"),
  toggleAnswer: document.querySelector("#toggle-answer"),
  answerPanel: document.querySelector("#answer-panel"),
  answer: document.querySelector("#answer-text"),
  explanation: document.querySelector("#explanation-text"),
  basisSection: document.querySelector("#basis-section"),
  basis: document.querySelector("#basis-text"),
};

function unique(values) {
  return [...new Set(values)].sort((a, b) => Number(a) - Number(b));
}

function option(select, value, label = value) {
  const item = document.createElement("option");
  item.value = String(value);
  item.textContent = label;
  select.appendChild(item);
}

function normalizeImagePath(path) {
  return path.replaceAll("\\", "/");
}

function cleanText(text) {
  return String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function formatExplanation(text) {
  return cleanText(text)
    .replace(/([.!?。！？]|다\.|요\.)\s+/g, "$1\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function cleanList(values) {
  return Array.isArray(values) ? values.map(cleanText).filter(Boolean) : [];
}

function cleanDisplayBlock(value) {
  if (Array.isArray(value)) return cleanList(value).join("\n");
  return cleanText(value);
}

function cleanTables(tables) {
  if (!Array.isArray(tables)) return [];

  return tables
    .map((table) => ({
      title: cleanText(table?.title),
      headers: cleanList(table?.headers),
      rows: Array.isArray(table?.rows) ? table.rows.map((row) => cleanList(row)) : [],
    }))
    .filter((table) => table.headers.length || table.rows.length);
}

function parseDisplayContent(display) {
  const source = display || {};
  const language = source.code_language ? String(source.code_language).toLowerCase() : "code";
  return {
    prompt: cleanText(source.prompt),
    description: cleanList(source.description),
    items: cleanList(source.items),
    conditions: cleanList(source.conditions),
    choices: cleanList(source.choices),
    targets: cleanList(source.targets),
    tables: cleanTables(source.tables),
    codeLines: source.code ? String(source.code).split("\n") : [],
    input: cleanText(source.input),
    output: cleanDisplayBlock(source.output),
    language,
    languageLabel: language === "code" ? "Code" : language.toUpperCase(),
  };
}

function renderTextList(container, titleText, items, className) {
  container.replaceChildren();
  if (!items.length) return;

  const panel = document.createElement("section");
  panel.className = `${className}-panel`;
  const title = document.createElement("strong");
  title.textContent = titleText;
  const list = document.createElement("div");
  list.className = `${className}-list`;

  items.forEach((item) => {
    const row = document.createElement("div");
    row.textContent = item;
    list.appendChild(row);
  });

  panel.append(title, list);
  container.appendChild(panel);
}

function renderChoiceArea(choices) {
  elements.choiceArea.replaceChildren();
  if (!choices.length) return;

  const panel = document.createElement("section");
  panel.className = "choice-panel";
  const title = document.createElement("strong");
  title.textContent = "보기";
  const list = document.createElement("div");
  list.className = "choice-list";

  choices.forEach((choice) => {
    const chip = document.createElement("span");
    chip.className = "choice-chip";
    chip.textContent = choice;
    list.appendChild(chip);
  });

  panel.append(title, list);
  elements.choiceArea.appendChild(panel);
}

function renderTables(tables) {
  elements.tableArea.replaceChildren();
  if (!tables.length) return;

  tables.forEach((table) => {
    const panel = document.createElement("section");
    panel.className = "table-panel";

    if (table.title) {
      const title = document.createElement("strong");
      title.className = "table-title";
      title.textContent = table.title;
      panel.appendChild(title);
    }

    const wrap = document.createElement("div");
    wrap.className = "table-scroll";
    const tableElement = document.createElement("table");

    if (table.headers.length) {
      const thead = document.createElement("thead");
      const row = document.createElement("tr");
      table.headers.forEach((header) => {
        const cell = document.createElement("th");
        cell.textContent = header;
        row.appendChild(cell);
      });
      thead.appendChild(row);
      tableElement.appendChild(thead);
    }

    const tbody = document.createElement("tbody");
    table.rows.forEach((row) => {
      const tr = document.createElement("tr");
      row.forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        tr.appendChild(cell);
      });
      tbody.appendChild(tr);
    });
    tableElement.appendChild(tbody);
    wrap.appendChild(tableElement);
    panel.appendChild(wrap);
    elements.tableArea.appendChild(panel);
  });
}

const HIGHLIGHT_KEYWORDS = {
  c: new Set([
    "auto",
    "break",
    "case",
    "char",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extern",
    "float",
    "for",
    "goto",
    "if",
    "include",
    "int",
    "long",
    "return",
    "short",
    "signed",
    "sizeof",
    "static",
    "struct",
    "switch",
    "typedef",
    "union",
    "unsigned",
    "void",
    "while",
  ]),
  java: new Set([
    "abstract",
    "boolean",
    "break",
    "byte",
    "case",
    "catch",
    "char",
    "class",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "extends",
    "final",
    "finally",
    "float",
    "for",
    "if",
    "implements",
    "import",
    "instanceof",
    "int",
    "interface",
    "long",
    "new",
    "null",
    "private",
    "protected",
    "public",
    "return",
    "short",
    "static",
    "super",
    "switch",
    "this",
    "throw",
    "throws",
    "try",
    "void",
    "while",
  ]),
  python: new Set([
    "and",
    "as",
    "assert",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "False",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "None",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "True",
    "try",
    "while",
    "with",
    "yield",
  ]),
  sql: new Set([
    "all",
    "and",
    "as",
    "asc",
    "between",
    "by",
    "case",
    "count",
    "create",
    "delete",
    "desc",
    "distinct",
    "drop",
    "else",
    "end",
    "from",
    "group",
    "having",
    "in",
    "insert",
    "into",
    "is",
    "join",
    "left",
    "like",
    "not",
    "null",
    "on",
    "or",
    "order",
    "right",
    "select",
    "set",
    "table",
    "then",
    "union",
    "update",
    "values",
    "when",
    "where",
  ]),
};

function tokenClass(token, language) {
  const lower = token.toLowerCase();
  if ((language === "c" || language === "java") && /^(\/\/|\/\*|\*\/)/.test(token)) return "token-comment";
  if (language === "python" && /^#/.test(token)) return "token-comment";
  if (language === "sql" && /^--/.test(token)) return "token-comment";
  if (/^(['"`]).*\1$/.test(token)) return "token-string";
  if (/^\d/.test(token)) return "token-number";
  if (HIGHLIGHT_KEYWORDS[language]?.has(language === "sql" ? lower : token) || HIGHLIGHT_KEYWORDS[language]?.has(lower)) {
    return "token-keyword";
  }
  if (/^[+\-*/%=!<>&|^~?:.;,()[\]{}]+$/.test(token)) return "token-operator";
  return "";
}

function appendHighlightedCode(container, line, language) {
  if (!line) {
    container.textContent = " ";
    return;
  }

  const commentPattern = {
    c: "\\/\\/.*|\\/\\*.*?\\*\\/",
    java: "\\/\\/.*|\\/\\*.*?\\*\\/",
    python: "#.*",
    sql: "--.*",
  }[language];
  const parts = [
    commentPattern,
    '"(?:\\\\.|[^"\\\\])*"',
    "'(?:\\\\.|[^'\\\\])*'",
    "`(?:\\\\.|[^`\\\\])*`",
    "\\b\\d+(?:\\.\\d+)?\\b",
    "\\b[A-Za-z_][A-Za-z0-9_]*\\b",
    "[+\\-*/%=!<>&|^~?:.;,()[\\]{}#]+",
    "\\s+",
    ".",
  ].filter(Boolean);
  const tokenPattern = new RegExp(`(${parts.join("|")})`, "g");
  const tokens = line.match(tokenPattern) || [line];
  tokens.forEach((token) => {
    const className = tokenClass(token, language);
    if (!className) {
      container.appendChild(document.createTextNode(token));
      return;
    }

    const span = document.createElement("span");
    span.className = className;
    span.textContent = token;
    container.appendChild(span);
  });
}

function appendCodeMetaPanel(title, text, className) {
  if (!text) return;

  const panel = document.createElement("section");
  panel.className = className;
  panel.innerHTML = `<strong>${title}</strong><pre></pre>`;
  panel.querySelector("pre").textContent = text;
  elements.codeArea.appendChild(panel);
}

function renderCodeArea(parsed) {
  elements.codeArea.replaceChildren();

  if (parsed.codeLines.length) {
    const editor = document.createElement("section");
    editor.className = "code-editor";

    const toolbar = document.createElement("div");
    toolbar.className = "code-toolbar";
    toolbar.innerHTML = `<span>${parsed.languageLabel}</span><span>${parsed.codeLines.length} lines</span>`;
    editor.appendChild(toolbar);

    const pre = document.createElement("pre");
    pre.className = "code-table";
    parsed.codeLines.forEach((line, index) => {
      const row = document.createElement("div");
      row.className = "code-line";
      const number = document.createElement("span");
      number.className = "line-number";
      number.textContent = String(index + 1);
      const code = document.createElement("code");
      code.className = "code-text";
      appendHighlightedCode(code, line, parsed.language);
      row.append(number, code);
      pre.appendChild(row);
    });

    editor.appendChild(pre);
    elements.codeArea.appendChild(editor);
  }

  appendCodeMetaPanel("입력", parsed.input, "input-panel");
  appendCodeMetaPanel("출력", parsed.output, "output-panel");
}

function renderImages(question) {
  elements.imageArea.replaceChildren();
  const refs = question.image_refs || [];
  refs.forEach((ref, index) => {
    if (!ref.local_path) return;
    const image = document.createElement("img");
    image.className = "question-image";
    image.src = normalizeImagePath(ref.local_path);
    image.alt = `${questionBadge(question)} 문제 이미지 ${index + 1}`;
    elements.imageArea.appendChild(image);
  });
}

function selectedNumber() {
  return Number(elements.number.value);
}

function selectedYear() {
  return Number(elements.year.value);
}

function selectedRound() {
  return Number(elements.round.value);
}

function shouldOpenAnswerByDefault() {
  return new URLSearchParams(window.location.search).get("type") === "2";
}

function shouldShowBasis() {
  return new URLSearchParams(window.location.search).get("type") === "2";
}

function isExpectedMode() {
  return state.mode === "expected";
}

function selectedCategory() {
  return elements.category.value || "전체 카테고리";
}

function isCategoryFiltered() {
  return isExpectedMode() && selectedCategory() !== "전체 카테고리";
}

function examTitle(question) {
  if (isExpectedMode() && state.expectedView === "random" && isCategoryFiltered()) {
    return `랜덤 ${selectedCategory()} 예상문제`;
  }
  if (isExpectedMode() && state.expectedView === "random") return `랜덤 예상문제 ${question.round}회`;
  if (isExpectedMode() && isCategoryFiltered()) return `${selectedCategory()} 예상문제`;
  if (isExpectedMode()) return `예상문제 ${question.round}회`;
  return `${question.year}년 ${question.round}회`;
}

function questionBadge(question) {
  if (isExpectedMode() && state.expectedView === "random" && isCategoryFiltered()) {
    return `랜덤 ${selectedCategory()} 예상문제 ${question.number}번`;
  }
  if (isExpectedMode() && state.expectedView === "random") return `랜덤 예상문제 ${question.round}회 ${question.number}번`;
  if (isExpectedMode() && isCategoryFiltered()) return `${selectedCategory()} 예상문제 ${question.number}번`;
  if (isExpectedMode()) return `예상문제 ${question.round}회 ${question.number}번`;
  return `${question.year}년 ${question.round}회 ${question.number}번`;
}

function questionsForExam(year = selectedYear(), round = selectedRound()) {
  return state.questions
    .filter((item) => item.year === year && item.round === round)
    .sort((a, b) => a.number - b.number);
}

function roundsForYear(year) {
  return unique(state.questions.filter((item) => item.year === year).map((item) => item.round));
}

function setOptions(select, values, labeler = (value) => value) {
  select.replaceChildren();
  values.forEach((value) => option(select, value, labeler(value)));
}

function setFilterVisibility() {
  document.querySelectorAll(".past-filter").forEach((element) => {
    element.hidden = isExpectedMode();
  });
  document.querySelectorAll(".expected-filter").forEach((element) => {
    element.hidden = !isExpectedMode();
  });
  elements.shuffle.hidden = !isExpectedMode() || state.expectedView !== "random";
}

function setupExpectedSelectors() {
  const categories = ["전체 카테고리", ...new Set(state.expectedQuestions.map((item) => item.category).filter(Boolean))];
  setOptions(elements.category, categories);
}

function expectedQuestionPool() {
  const category = selectedCategory();
  if (category === "전체 카테고리") return state.expectedQuestions;
  return state.expectedQuestions.filter((question) => question.category === category);
}

function hashSeed(seed) {
  return [...String(seed)].reduce((hash, char) => Math.imul(31, hash) + char.charCodeAt(0) || 0, 7) >>> 0;
}

function seededRandom(seed) {
  let value = hashSeed(seed);
  return () => {
    value += 0x6d2b79f5;
    let next = value;
    next = Math.imul(next ^ (next >>> 15), next | 1);
    next ^= next + Math.imul(next ^ (next >>> 7), next | 61);
    return ((next ^ (next >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffled(values, random) {
  const items = [...values];
  for (let index = items.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(random() * (index + 1));
    [items[index], items[swapIndex]] = [items[swapIndex], items[index]];
  }
  return items;
}

function typeGroup(question) {
  const type = question.question_type || "";
  if (type === "code_output") return "code";
  if (type === "sql" || type === "table_sql") return "sql";
  if (type === "choice") return "choice";
  return "concept";
}

function buildRandomExpectedQuestions(seed = String(Date.now())) {
  const random = seededRandom(seed);
  const pool = shuffled(expectedQuestionPool(), random);
  const quotas = { code: 7, concept: 8, sql: 3, choice: 2 };
  const selected = [];
  const selectedIds = new Set();

  Object.entries(quotas).forEach(([group, count]) => {
    pool
      .filter((question) => typeGroup(question) === group)
      .slice(0, count)
      .forEach((question) => {
        selected.push(question);
        selectedIds.add(question.id);
      });
  });

  pool.forEach((question) => {
    if (selected.length >= 20 || selectedIds.has(question.id)) return;
    selected.push(question);
    selectedIds.add(question.id);
  });

  return shuffled(selected, random).slice(0, 20).map((question, index) => ({
    ...question,
    round: 1,
    number: index + 1,
    random_source_id: question.id,
  }));
}

function expectedQuestionsForCurrentView() {
  const pool = expectedQuestionPool();
  if (state.expectedView !== "random") {
    if (!isCategoryFiltered()) return pool;
    return pool.map((question, index) => ({
      ...question,
      round: 1,
      number: index + 1,
      category_source_id: question.id,
    }));
  }
  if (!state.randomQuestions.length) {
    state.randomSeed = new URLSearchParams(window.location.search).get("seed") || String(Date.now());
    state.randomQuestions = buildRandomExpectedQuestions(state.randomSeed);
  }
  return state.randomQuestions;
}

function setMode(mode) {
  state.mode = mode;
  state.questions = mode === "expected" ? expectedQuestionsForCurrentView() : state.pastQuestions;
  state.answerVisible = state.answerDefaultVisible;

  elements.pastMode.classList.toggle("active", mode === "past");
  elements.expectedMode.classList.toggle("active", mode === "expected");
  elements.pastMode.setAttribute("aria-current", mode === "past" ? "page" : "false");
  elements.expectedMode.setAttribute("aria-current", mode === "expected" ? "page" : "false");
  elements.pageTitle.textContent = mode === "expected" ? "기출 예상문제 풀기" : "기출문제 풀기";
  elements.count.textContent =
    mode === "expected"
      ? `총 ${state.questions.length.toLocaleString("ko-KR")}개 예상문제`
      : `총 ${state.questions.length.toLocaleString("ko-KR")}문제`;

  setFilterVisibility();
  setupFilters();
}

function refreshExpectedView(resetSeed = false) {
  state.expectedView = elements.mix.value;
  if (resetSeed || state.expectedView !== "random") {
    state.randomSeed = "";
    state.randomQuestions = [];
  }
  if (state.expectedView === "random") {
    state.randomSeed = String(Date.now());
    state.randomQuestions = buildRandomExpectedQuestions(state.randomSeed);
  }
  if (isExpectedMode()) setMode("expected");
}

function setupFilters() {
  const years = unique(state.questions.map((item) => item.year));
  setOptions(elements.year, years, (year) => `${year}년`);
  elements.year.value = String(years[years.length - 1]);
  refreshRounds();
}

function refreshRounds() {
  const rounds = roundsForYear(selectedYear());
  setOptions(elements.round, rounds, (round) => `${round}회`);
  elements.round.value = String(rounds[0]);
  refreshNumbers();
}

function refreshNumbers() {
  state.filtered = questionsForExam();
  const numbers = state.filtered.map((item) => item.number);
  setOptions(elements.number, numbers, (number) => `${number}번`);
  state.currentIndex = 0;
  if (numbers.length) {
    elements.number.value = String(numbers[0]);
  }
  renderAll();
}

function currentQuestion() {
  return state.filtered[state.currentIndex] || null;
}

function setCurrentByNumber(number) {
  const index = state.filtered.findIndex((item) => item.number === number);
  state.currentIndex = Math.max(0, index);
  state.answerVisible = state.answerDefaultVisible;
  renderAll();
}

function moveQuestion(delta) {
  const nextIndex = state.currentIndex + delta;
  if (nextIndex < 0 || nextIndex >= state.filtered.length) return;
  state.currentIndex = nextIndex;
  state.answerVisible = state.answerDefaultVisible;
  renderAll();
}

function setExamPosition(year, round) {
  elements.year.value = String(year);

  const rounds = roundsForYear(year);
  setOptions(elements.round, rounds, (value) => `${value}회`);
  elements.round.value = String(round);

  state.filtered = questionsForExam(year, round);
  const numbers = state.filtered.map((item) => item.number);
  setOptions(elements.number, numbers, (number) => `${number}번`);
  state.currentIndex = 0;
  if (numbers.length) {
    elements.number.value = String(numbers[0]);
  }
  state.answerVisible = state.answerDefaultVisible;
  renderAll();
}

function setExamPositionToLastQuestion(year, round) {
  setExamPosition(year, round);
  if (!state.filtered.length) return;
  state.currentIndex = state.filtered.length - 1;
  elements.number.value = String(state.filtered[state.currentIndex].number);
  state.answerVisible = state.answerDefaultVisible;
  renderAll();
}

function moveToNextExam() {
  const year = selectedYear();
  const rounds = roundsForYear(year);
  const roundIndex = rounds.indexOf(selectedRound());

  if (roundIndex >= 0 && roundIndex < rounds.length - 1) {
    setExamPosition(year, rounds[roundIndex + 1]);
    return;
  }

  const years = unique(state.questions.map((item) => item.year));
  const previousYears = years.filter((item) => item < year);
  if (!previousYears.length) return;

  const previousYear = previousYears[previousYears.length - 1];
  const previousYearRounds = roundsForYear(previousYear);
  if (!previousYearRounds.length) return;
  setExamPosition(previousYear, previousYearRounds[0]);
}

function moveToPreviousExam() {
  const year = selectedYear();
  const rounds = roundsForYear(year);
  const roundIndex = rounds.indexOf(selectedRound());

  if (roundIndex > 0) {
    setExamPositionToLastQuestion(year, rounds[roundIndex - 1]);
    return;
  }

  const years = unique(state.questions.map((item) => item.year));
  const nextYears = years.filter((item) => item > year);
  if (!nextYears.length) return;

  const nextYear = nextYears[0];
  const nextYearRounds = roundsForYear(nextYear);
  if (!nextYearRounds.length) return;
  setExamPositionToLastQuestion(nextYear, nextYearRounds[nextYearRounds.length - 1]);
}

function moveForwardByKeyboard() {
  if (state.currentIndex < state.filtered.length - 1) {
    moveQuestion(1);
    return;
  }
  moveToNextExam();
}

function moveBackwardByKeyboard() {
  if (state.currentIndex > 0) {
    moveQuestion(-1);
    return;
  }
  moveToPreviousExam();
}

function renderList() {
  elements.list.replaceChildren();
  if (!state.filtered.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "선택한 회차에 문제가 없습니다.";
    elements.list.appendChild(empty);
    return;
  }

  state.filtered.forEach((question, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `list-item${index === state.currentIndex ? " active" : ""}`;
    const detail = isExpectedMode() ? question.category || "예상" : question.image_refs?.length ? "이미지" : "텍스트";
    button.innerHTML = `<span>${question.number}번</span><small>${detail}</small>`;
    button.addEventListener("click", () => {
      state.currentIndex = index;
      state.answerVisible = state.answerDefaultVisible;
      renderAll();
    });
    elements.list.appendChild(button);
  });
}

function clearQuestionAreas() {
  elements.detailArea.replaceChildren();
  elements.descriptionArea.replaceChildren();
  elements.optionArea.replaceChildren();
  elements.choiceArea.replaceChildren();
  elements.targetArea.replaceChildren();
  elements.tableArea.replaceChildren();
  elements.codeArea.replaceChildren();
  elements.imageArea.replaceChildren();
}

function renderQuestion() {
  const question = currentQuestion();
  if (!question) {
    elements.badge.textContent = "-";
    elements.title.textContent = "문제를 선택하세요";
    elements.question.textContent = "";
    elements.answer.textContent = "";
    elements.explanation.textContent = "";
    elements.basis.textContent = "";
    elements.basisSection.hidden = true;
    clearQuestionAreas();
    return;
  }

  const parsed = parseDisplayContent(question.display);
  elements.examTitle.textContent = examTitle(question);
  elements.progress.textContent = `${state.currentIndex + 1} / ${state.filtered.length}`;
  elements.badge.textContent = questionBadge(question);
  elements.source.href = question.source_url || "#";
  elements.source.hidden = !question.source_url;
  elements.title.textContent = "문제";
  elements.question.textContent = parsed.prompt || question.question || "";
  renderImages(question);
  renderCodeArea(parsed);
  renderTables(parsed.tables);
  renderTextList(elements.descriptionArea, "설명", parsed.description, "description");
  renderTextList(elements.optionArea, "조건", parsed.conditions, "option");
  renderTextList(elements.detailArea, "항목", parsed.items, "detail");
  renderChoiceArea(parsed.choices);
  renderTextList(elements.targetArea, "구하는 것", parsed.targets, "target");
  const answerText = cleanText(question.answer);
  const explanationText = formatExplanation(question.explanation);
  elements.answer.textContent = answerText || "등록된 정답이 없습니다.";
  elements.explanation.textContent =
    explanationText && explanationText !== answerText ? explanationText : "등록된 해설이 없습니다.";
  const basis = cleanList(question.basis);
  elements.basis.textContent = basis.join("\n");
  elements.basisSection.hidden = !basis.length || !shouldShowBasis();
  elements.number.value = String(question.number);
  elements.answerPanel.hidden = !state.answerVisible;
  elements.toggleAnswer.textContent = state.answerVisible ? "해설닫기" : "해설보기";
}

function renderButtons() {
  elements.prev.disabled = state.currentIndex <= 0;
  elements.next.disabled = state.currentIndex >= state.filtered.length - 1;
}

function renderAll() {
  renderList();
  renderQuestion();
  renderButtons();
}

function bindEvents() {
  elements.pastMode.addEventListener("click", () => setMode("past"));
  elements.expectedMode.addEventListener("click", () => setMode("expected"));
  elements.category.addEventListener("change", () => refreshExpectedView(true));
  elements.mix.addEventListener("change", () => refreshExpectedView(true));
  elements.shuffle.addEventListener("click", () => refreshExpectedView(true));
  elements.year.addEventListener("change", refreshRounds);
  elements.round.addEventListener("change", refreshNumbers);
  elements.number.addEventListener("change", () => setCurrentByNumber(selectedNumber()));
  elements.prev.addEventListener("click", () => moveQuestion(-1));
  elements.next.addEventListener("click", () => moveQuestion(1));
  elements.toggleAnswer.addEventListener("click", () => {
    state.answerVisible = !state.answerVisible;
    renderQuestion();
  });
  document.addEventListener("keydown", (event) => {
    const tagName = event.target?.tagName;
    const isInteractive = ["A", "BUTTON", "INPUT", "SELECT", "TEXTAREA"].includes(tagName);
    if (isInteractive) return;

    if (event.key === "ArrowRight") {
      event.preventDefault();
      moveForwardByKeyboard();
      return;
    }

    if (event.key === "ArrowLeft") {
      event.preventDefault();
      moveBackwardByKeyboard();
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      state.answerVisible = !state.answerVisible;
      renderQuestion();
    }
  });
}

async function loadQuestions() {
  try {
    if (Array.isArray(window.PAST_QUESTIONS)) {
      state.pastQuestions = window.PAST_QUESTIONS;
    } else {
      const response = await fetch(DATA_URL);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      state.pastQuestions = await response.json();
    }
    if (Array.isArray(window.EXPECTED_QUESTIONS)) {
      state.expectedQuestions = window.EXPECTED_QUESTIONS;
    } else {
      const response = await fetch(EXPECTED_DATA_URL);
      state.expectedQuestions = response.ok ? await response.json() : [];
    }
    state.pastQuestions.sort((a, b) => a.year - b.year || a.round - b.round || a.number - b.number);
    state.expectedQuestions.sort((a, b) => a.round - b.round || a.number - b.number);
    state.answerDefaultVisible = shouldOpenAnswerByDefault();
    state.answerVisible = state.answerDefaultVisible;
    elements.status.textContent = "Ready";
    setupExpectedSelectors();
    setMode("past");
  } catch (error) {
    elements.status.textContent = "Error";
    elements.count.textContent = "문제 데이터를 불러오지 못했습니다.";
    elements.list.innerHTML = '<div class="error-state">로컬 서버로 실행하면 데이터 파일을 읽을 수 있습니다.</div>';
    elements.question.textContent = String(error.message || error);
  }
}

bindEvents();
loadQuestions();
