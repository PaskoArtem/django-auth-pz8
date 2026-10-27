(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const config = window.WORKFLOW_CONFIG || {isMethodist:false};
  const csrf = document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
  const statusLabels = {pending:"Ожидает согласования", approved:"Согласована", issued:"Выдано", returned:"Возвращено", cancelled:"Отменена"};
  const categoryLabels = {computer:"Компьютерная техника", lab:"Лабораторное оборудование", presentation:"Презентационное оборудование", other:"Другое"};
  let equipment = [], requests = [], editingId = null;

  function message(text, error=false) {
    const el=$("workflow-message"); el.textContent=text;
    el.className=`alert ${error?"alert-danger":"alert-success"}`; el.classList.remove("d-none");
  }
  function errText(data) {
    if (!data) return "Сервер не вернул описание ошибки.";
    if (data.detail) return data.detail;
    return Object.entries(data).map(([k,v])=>`${k}: ${Array.isArray(v)?v.join(" "):v}`).join(" ") || "Запрос отклонён сервером.";
  }
  async function api(url, options={}) {
    const headers={"Accept":"application/json",...(options.headers||{})};
    if(options.body) headers["Content-Type"]="application/json";
    if(options.method && !["GET","HEAD","OPTIONS"].includes(options.method.toUpperCase())) headers["X-CSRFToken"]=csrf;
    const response=await fetch(url,{...options,headers,credentials:"same-origin"});
    const data=response.status===204?null:await response.json().catch(()=>null);
    if(!response.ok) throw new Error(errText(data)||`HTTP ${response.status}`);
    return data;
  }
  function addCell(row, value) { const td=document.createElement("td"); td.textContent=value ?? "—"; row.append(td); return td; }
  async function loadEquipment() {
    equipment=await api("/api/equipment/");
    const select=$("equipment"); select.replaceChildren();
    equipment.forEach(e=>{
      const o=document.createElement("option"); o.value=e.id;
      o.textContent=`${e.name} — доступно ${e.available_quantity} из ${e.total_quantity}`;
      o.disabled=e.available_quantity<1; select.append(o);
    });
    $("stock-total").textContent=equipment.reduce((sum,e)=>sum+Number(e.available_quantity),0);
  }
  async function loadRequests() {
    const params=new URLSearchParams();
    if($("status-filter").value) params.set("status",$("status-filter").value);
    if($("category-filter").value) params.set("category",$("category-filter").value);
    requests=await api(`/api/equipment-requests/${params.toString()?`?${params}`:""}`);
    $("request-total").textContent=requests.length;
    renderRequests();
  }
  function button(text, cls, handler) { const b=document.createElement("button"); b.type="button"; b.className=`btn btn-sm ${cls} me-1 mb-1`; b.textContent=text; b.addEventListener("click",handler); return b; }
  function renderRequests() {
    const body=$("request-rows"); body.replaceChildren();
    requests.forEach(r=>{
      const tr=document.createElement("tr");
      addCell(tr,r.id); addCell(tr,r.equipment_name); addCell(tr,r.requester_name); addCell(tr,r.quantity);
      const badge=document.createElement("span"); badge.className="badge bg-blue-lt"; badge.textContent=r.status_display; const statusTd=addCell(tr,""); statusTd.append(badge);
      addCell(tr,r.purpose);
      const historyTd=addCell(tr,"");
      historyTd.append(button("История","btn-outline-secondary",()=>showHistory(r)));
      const actions=addCell(tr,"");
      if(config.isMethodist && r.status==="pending") actions.append(button("Согласовать","btn-outline-primary",()=>transition(r,"approved")));
      if(config.isMethodist && r.status==="approved") actions.append(button("Выдать","btn-outline-primary",()=>transition(r,"issued")));
      if(config.isMethodist && r.status==="issued") actions.append(button("Вернуть","btn-outline-success",()=>transition(r,"returned")));
      if(r.status==="pending") actions.append(button("Изменить","btn-outline-primary",()=>beginEdit(r)));
      if((r.status==="pending" || (config.isMethodist && r.status==="approved"))) actions.append(button("Отменить","btn-outline-warning",()=>transition(r,"cancelled")));
      if(r.status==="pending") actions.append(button("Удалить","btn-outline-danger",()=>deleteRequest(r)));
      body.append(tr);
    });
    $("no-requests").classList.toggle("d-none",requests.length>0);
  }
  async function refreshAll() {
    const refreshButton = $("refresh");
    if (refreshButton) refreshButton.disabled = true;
    try {
      await loadEquipment();
      await loadRequests();
    } catch (e) {
      message(e.message || "Не удалось обновить данные.", true);
      console.error("Ошибка обновления заявок/оборудования:", e);
    } finally {
      if (refreshButton) refreshButton.disabled = false;
    }
  }
  function resetRequestForm() {
    editingId=null; $("request-form").reset(); $("quantity").value=1;
    $("request-save").textContent="Отправить заявку";
    $("request-cancel-edit").classList.add("d-none");
  }
  function beginEdit(r) {
    editingId=r.id; $("equipment").value=String(r.equipment);
    $("quantity").value=r.quantity; $("purpose").value=r.purpose;
    $("request-save").textContent="Сохранить изменения";
    $("request-cancel-edit").classList.remove("d-none");
    $("request-form").scrollIntoView({behavior:"smooth",block:"center"});
  }
  $("request-form").addEventListener("submit",async e=>{
    e.preventDefault();
    const payload={equipment:Number($("equipment").value),quantity:Number($("quantity").value),purpose:$("purpose").value.trim()};
    try {
      if(editingId) {
        await api(`/api/equipment-requests/${editingId}/`,{method:"PATCH",body:JSON.stringify(payload)});
        resetRequestForm(); message("Изменения сохранены по ответу API.");
      } else {
        await api("/api/equipment-requests/",{method:"POST",body:JSON.stringify(payload)});
        resetRequestForm(); message("Заявка создана. Статус подтверждён ответом API.");
      }
      await refreshAll();
    } catch(ex) { message(ex.message,true); }
  });
  $("request-cancel-edit").addEventListener("click",resetRequestForm);
  async function transition(r,status) {
    const label=statusLabels[status]||status;
    if(!window.confirm(`Изменить статус заявки №${r.id} на «${label}»?`)) return;
    try { await api(`/api/equipment-requests/${r.id}/transition/`,{method:"POST",body:JSON.stringify({status})}); message("Изменение сохранено."); await refreshAll(); }
    catch(e) { message(e.message,true); }
  }
  async function deleteRequest(r) {
    if(!window.confirm(`Удалить заявку №${r.id}? Это действие нельзя отменить.`)) return;
    try { await api(`/api/equipment-requests/${r.id}/`,{method:"DELETE"}); message("Заявка удалена."); await refreshAll(); }
    catch(e) { message(e.message,true); }
  }
  async function showHistory(r) {
    const content = $("history-content");
    const modal = $("history-modal");
    if (!content || !modal) {
      message("Не найдена область отображения истории заявки.", true);
      return;
    }

    content.replaceChildren();
    const loading = document.createElement("div");
    loading.className = "text-secondary";
    loading.textContent = "Загрузка истории…";
    content.append(loading);

    // Загружаем историю отдельным запросом, чтобы не зависеть от того,
    // содержит ли ответ списка заявок вложенные events.
    try {
      const events = await api(`/api/equipment-requests/${r.id}/history/`);
      content.replaceChildren();

      if (!Array.isArray(events) || events.length === 0) {
        content.textContent = "История пока пуста.";
      } else {
        const list = document.createElement("div");
        list.className = "list-group";
        events.forEach(ev => {
          const item = document.createElement("div");
          item.className = "list-group-item";
          const title = document.createElement("div");
          title.className = "fw-bold";
          title.textContent = `${ev.event_type} — ${ev.actor_name || "система"}`;
          const detail = document.createElement("div");
          detail.textContent = ev.details || "";
          const date = document.createElement("small");
          date.className = "text-secondary";
          date.textContent = ev.created_at ? new Date(ev.created_at).toLocaleString() : "";
          item.append(title, detail, date);
          list.append(item);
        });
        content.append(list);
      }
    } catch (e) {
      content.replaceChildren();
      const error = document.createElement("div");
      error.className = "alert alert-danger";
      error.textContent = `Не удалось загрузить историю: ${e.message}`;
      content.append(error);
      console.error("Ошибка загрузки истории заявки:", e);
    }

    // Tabler may not expose Bootstrap's Modal API on every build; provide a fallback.
    if (window.bootstrap?.Modal) {
      window.bootstrap.Modal.getOrCreateInstance(modal).show();
    } else {
      modal.classList.add("show");
      modal.style.display = "block";
      modal.removeAttribute("aria-hidden");
      modal.setAttribute("aria-modal", "true");
      modal.setAttribute("role", "dialog");
      document.body.classList.add("modal-open");

      let backdrop = document.getElementById("history-modal-backdrop");
      if (!backdrop) {
        backdrop = document.createElement("div");
        backdrop.id = "history-modal-backdrop";
        backdrop.className = "modal-backdrop fade show";
        backdrop.addEventListener("click", closeHistory);
        document.body.append(backdrop);
      }
    }
  }

  function closeHistory() {
    const modal = $("history-modal");
    if (!modal) return;
    if (window.bootstrap?.Modal) {
      window.bootstrap.Modal.getOrCreateInstance(modal).hide();
      return;
    }
    modal.classList.remove("show");
    modal.style.display = "none";
    modal.setAttribute("aria-hidden", "true");
    modal.removeAttribute("aria-modal");
    document.body.classList.remove("modal-open");
    $("history-modal-backdrop")?.remove();
  }
  $("status-filter").addEventListener("change", () => loadRequests().catch(e => message(e.message, true)));
  $("category-filter").addEventListener("change", () => loadRequests().catch(e => message(e.message, true)));
  $("refresh").addEventListener("click", () => refreshAll());
  $("history-modal").querySelectorAll('[data-bs-dismiss="modal"], .btn-close').forEach(el => {
    el.addEventListener("click", closeHistory);
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && $("history-modal").classList.contains("show")) closeHistory();
  });
  refreshAll();
})();
