(() => {
  "use strict";

  const config = window.PZ7_CONFIG || { isMethodist: false };
  const $ = (id) => document.getElementById(id);
  const entitySelect = $("entity-select");
  const form = $("entity-form");
  const nameInput = $("object-name");
  const departmentSelect = $("department-select");
  const descriptionInput = $("object-description");
  const descriptionWrap = $("description-wrap");
  const table = $("entities-table");
  const message = $("api-message");
  const loading = $("loading");
  const emptyState = $("empty-state");
  const editor = $("editor");
  const csrf = document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";

  const state = { departments: [], courses: [], groups: [], editingId: null };
  const labels = {
    courses: { singular: "курс", plural: "курсы", name: "Название курса", extra: "Описание" },
    groups: { singular: "учебную группу", plural: "учебные группы", name: "Название группы", extra: "Студентов" }
  };

  function showMessage(text, isError = false) {
    message.textContent = text;
    message.className = `alert ${isError ? "alert-danger" : "alert-success"}`;
    message.classList.remove("d-none");
  }

  function hideMessage() {
    message.classList.add("d-none");
    message.textContent = "";
  }

  function readableError(data) {
    if (!data) return "Не удалось выполнить запрос. Проверьте соединение и авторизацию.";
    if (typeof data === "string") return data;
    if (data.detail) return data.detail;
    const parts = [];
    for (const [field, errors] of Object.entries(data)) {
      const text = Array.isArray(errors) ? errors.join(" ") : String(errors);
      parts.push(`${field}: ${text}`);
    }
    return parts.join(" ") || "Сервер отклонил запрос.";
  }

  async function apiRequest(url, options = {}) {
    const headers = { "Accept": "application/json", ...(options.headers || {}) };
    if (options.body) headers["Content-Type"] = "application/json";
    if (options.method && !["GET", "HEAD", "OPTIONS"].includes(options.method.toUpperCase())) {
      headers["X-CSRFToken"] = csrf;
    }
    const response = await fetch(url, {
      ...options, headers, credentials: "same-origin"
    });
    let data = null;
    if (response.status !== 204) data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(readableError(data) || `HTTP ${response.status}`);
    return data;
  }

  function currentEndpoint() { return `/api/${entitySelect.value}/`; }

  function fillDepartments(selected = "") {
    departmentSelect.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Выберите кафедру";
    departmentSelect.append(placeholder);
    for (const department of state.departments) {
      const option = document.createElement("option");
      option.value = department.id;
      option.textContent = department.name;
      option.selected = String(department.id) === String(selected);
      departmentSelect.append(option);
    }
  }

  function resetForm() {
    form.reset();
    state.editingId = null;
    $("object-id").value = "";
    $("form-heading").textContent = `Добавить ${labels[entitySelect.value].singular}`;
    $("save-button").textContent = "Сохранить";
    $("cancel-edit").classList.add("d-none");
    fillDepartments();
  }

  function setCount(id, count) { $(id).textContent = String(count); }

  async function loadDepartments() {
    state.departments = await apiRequest("/api/departments/");
    fillDepartments();
  }

  async function loadAll() {
    hideMessage();
    loading.classList.remove("d-none");
    try {
      const [departments, groups, courses] = await Promise.all([
        apiRequest("/api/departments/"),
        apiRequest("/api/groups/"),
        apiRequest("/api/courses/")
      ]);
      state.departments = departments;
      state.groups = groups;
      state.courses = courses;
      setCount("departments-count", departments.length);
      setCount("groups-count", groups.length);
      setCount("courses-count", courses.length);
      fillDepartments(state.editingId ? departmentSelect.value : "");
      renderTable();
    } catch (error) {
      showMessage(error.message, true);
    } finally {
      loading.classList.add("d-none");
    }
  }

  function appendCell(row, text) {
    const cell = document.createElement("td");
    cell.textContent = text == null || text === "" ? "—" : String(text);
    row.append(cell);
    return cell;
  }

  function renderTable() {
    const type = entitySelect.value;
    const items = state[type] || [];
    const query = $("search-input").value.trim().toLocaleLowerCase("ru");
    const filtered = items.filter(item => item.name ? item.name.toLocaleLowerCase("ru").includes(query) :
      (item.title || "").toLocaleLowerCase("ru").includes(query));
    table.replaceChildren();

    for (const item of filtered) {
      const row = document.createElement("tr");
      appendCell(row, item.id);
      appendCell(row, type === "courses" ? item.title : item.name);
      appendCell(row, item.department_name);
      if (type === "courses") {
        appendCell(row, item.description);
      } else {
        const cell = appendCell(row, "—");
        cell.classList.add("text-secondary");
        cell.textContent = "Учебная группа";
      }

      if (config.isMethodist) {
        const actions = document.createElement("td");
        actions.className = "text-end text-nowrap";
        const edit = document.createElement("button");
        edit.type = "button";
        edit.className = "btn btn-sm btn-outline-primary me-2";
        edit.textContent = "Изменить";
        edit.addEventListener("click", () => beginEdit(item));
        const del = document.createElement("button");
        del.type = "button";
        del.className = "btn btn-sm btn-outline-danger";
        del.textContent = "Удалить";
        del.addEventListener("click", () => deleteItem(item));
        actions.append(edit, del);
        row.append(actions);
      }
      table.append(row);
    }
    emptyState.classList.toggle("d-none", filtered.length > 0);
  }

  function beginEdit(item) {
    state.editingId = item.id;
    $("object-id").value = item.id;
    nameInput.value = entitySelect.value === "courses" ? item.title : item.name;
    descriptionInput.value = item.description || "";
    fillDepartments(item.department);
    $("form-heading").textContent = `Изменить ${labels[entitySelect.value].singular}`;
    $("save-button").textContent = "Сохранить изменения";
    $("cancel-edit").classList.remove("d-none");
    editor.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function deleteItem(item) {
    const type = entitySelect.value;
    const title = type === "courses" ? item.title : item.name;
    if (!window.confirm(`Удалить «${title}»? Это действие нельзя отменить.`)) return;
    try {
      await apiRequest(`${currentEndpoint()}${item.id}/`, { method: "DELETE" });
      resetForm();
      showMessage("Запись успешно удалена.");
      await loadAll();
    } catch (error) {
      showMessage(error.message, true);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideMessage();
    const type = entitySelect.value;
    const wasEditing = Boolean(state.editingId);
    const payload = {
      [type === "courses" ? "title" : "name"]: nameInput.value.trim(),
      department: Number(departmentSelect.value)
    };
    if (type === "courses") payload.description = descriptionInput.value.trim();
    const url = state.editingId ? `${currentEndpoint()}${state.editingId}/` : currentEndpoint();
    try {
      await apiRequest(url, {
        method: state.editingId ? "PATCH" : "POST",
        body: JSON.stringify(payload)
      });
      resetForm();
      showMessage(wasEditing ? "Изменения сохранены." : "Запись успешно создана.");
      await loadAll();
    } catch (error) {
      showMessage(error.message, true);
    }
  });

  entitySelect.addEventListener("change", () => {
    resetForm();
    $("name-label").textContent = labels[entitySelect.value].name;
    $("extra-heading").textContent = labels[entitySelect.value].extra;
    descriptionWrap.classList.toggle("d-none", entitySelect.value !== "courses");
    $("search-input").value = "";
    renderTable();
  });
  $("cancel-edit").addEventListener("click", resetForm);
  $("search-input").addEventListener("input", renderTable);
  $("refresh-button").addEventListener("click", loadAll);

  async function initialize() {
    $("name-label").textContent = labels[entitySelect.value].name;
    descriptionWrap.classList.toggle("d-none", entitySelect.value !== "courses");
    if (!config.isMethodist) editor.classList.add("d-none");
    await loadAll();
  }
  initialize();
})();