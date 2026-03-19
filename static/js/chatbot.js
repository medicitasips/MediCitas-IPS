/**
 * chatbot.js – Widget de agendamiento de citas MediCitas EPS
 *
 * Flujo de pasos:
 *   0  → Bienvenida
 *   1  → Autenticación (usuario)
 *   2  → Autenticación (contraseña)
 *   3  → Seleccionar especialidad
 *   4  → Seleccionar médico
 *   5  → Seleccionar EPS
 *   6  → Elegir fecha
 *   7  → Elegir hora
 *   8  → Confirmar resumen
 *   9  → Resultado final
 */

"use strict";

document.addEventListener("DOMContentLoaded", function () {

  // ── Estado global del chatbot ─────────────────────────────
  const state = {
    step:           0,
    paciente:       null,   // { id_paciente, nombre, apellido, id_eps, eps_nombre }
    especialidad:   null,   // { id, nombre, duracion_min }
    medico:         null,   // { id, nombre }
    eps:            null,   // { id, nombre }
    fecha:          null,
    hora_inicio:    null,
    hora_fin:       null,
    motivo:         "",
  };

  // Número total de pasos para la barra de progreso
  const TOTAL_STEPS = 8;

  // ── Referencias DOM ───────────────────────────────────────
  const fab       = document.getElementById("cb-fab");
  if (!fab) return;   // el widget no está en esta página

  const win       = document.getElementById("cb-window");
  const closeBtn  = document.getElementById("cb-close");
  const messages  = document.getElementById("cb-messages");
  const footer    = document.getElementById("cb-footer");
  const progLabel = document.getElementById("cb-progress-label");
  const stepDots  = document.querySelectorAll(".cb-step-dot");

  // ── Abrir / cerrar ventana ────────────────────────────────
  fab.addEventListener("click", () => {
    const isOpen = win.classList.contains("cb-open");
    if (isOpen) {
      closeChatbot();
    } else {
      openChatbot();
    }
  });
  closeBtn.addEventListener("click", closeChatbot);

  function openChatbot() {
    win.classList.add("cb-open");
    fab.innerHTML = '<i class="bi bi-x-lg"></i><span class="cb-fab-badge"></span>';
    // Primera apertura: iniciar flujo
    if (state.step === 0 && messages.children.length === 0) {
      setTimeout(() => startFlow(), 300);
    }
  }

  function closeChatbot() {
    win.classList.remove("cb-open");
    fab.innerHTML = '<i class="bi bi-chat-heart-fill"></i><span class="cb-fab-badge"></span>';
  }

  // ── Barra de progreso ─────────────────────────────────────
  function updateProgress(currentStep) {
    stepDots.forEach((dot, i) => {
      dot.classList.remove("active", "done");
      if (i < currentStep)      dot.classList.add("done");
      else if (i === currentStep) dot.classList.add("active");
    });
    const labels = ["Inicio","Usuario","Contraseña","Especialidad","Médico","EPS","Fecha","Hora","Confirmar"];
    progLabel.textContent = labels[currentStep] || "";
  }

  // ── Helpers de mensajes ───────────────────────────────────

  function botMsg(html, isError = false) {
    const wrap   = document.createElement("div");
    wrap.className = `cb-msg-bot ${isError ? "cb-msg-error" : ""}`;
    wrap.innerHTML = `
      <div class="cb-bot-icon"><i class="bi bi-robot"></i></div>
      <div class="cb-bubble">${html}</div>`;
    messages.appendChild(wrap);
    scrollBottom();
    return wrap;
  }

  function userMsg(text) {
    const wrap   = document.createElement("div");
    wrap.className = "cb-msg-user";
    wrap.innerHTML = `<div class="cb-bubble">${escHtml(text)}</div>`;
    messages.appendChild(wrap);
    scrollBottom();
  }

  function typing() {
    const wrap = document.createElement("div");
    wrap.className = "cb-msg-bot cb-typing";
    wrap.id = "cb-typing-indicator";
    wrap.innerHTML = `
      <div class="cb-bot-icon"><i class="bi bi-robot"></i></div>
      <div class="cb-bubble">
        <span class="cb-dot"></span>
        <span class="cb-dot"></span>
        <span class="cb-dot"></span>
      </div>`;
    messages.appendChild(wrap);
    scrollBottom();
  }

  function removeTyping() {
    const el = document.getElementById("cb-typing-indicator");
    if (el) el.remove();
  }

  function showOptions(options) {
    // options: [{ label, value, data }]
    const wrap = document.createElement("div");
    wrap.className = "cb-options";
    options.forEach(opt => {
      const btn = document.createElement("button");
      btn.className    = "cb-opt-btn";
      btn.textContent  = opt.label;
      btn.dataset.value = JSON.stringify(opt.data || opt.value);
      btn.addEventListener("click", () => {
        // Deshabilitar todos los botones del grupo
        wrap.querySelectorAll(".cb-opt-btn").forEach(b => b.disabled = true);
        btn.classList.add("selected");
        opt.onSelect(opt.value, opt.data);
      });
      wrap.appendChild(btn);
    });
    messages.appendChild(wrap);
    scrollBottom();
  }

  function showSummary() {
    const hFin = calcHoraFin(state.hora_inicio, state.especialidad.duracion_min);
    state.hora_fin = hFin;
    const el = document.createElement("div");
    el.className = "cb-summary";
    el.innerHTML = `
      <strong>📋 Resumen de tu cita</strong><br>
      👤 <strong>Paciente:</strong> ${escHtml(state.paciente.nombre)} ${escHtml(state.paciente.apellido)}<br>
      🩺 <strong>Especialidad:</strong> ${escHtml(state.especialidad.nombre)}<br>
      👨‍⚕️ <strong>Médico:</strong> ${escHtml(state.medico.nombre)}<br>
      🏥 <strong>EPS:</strong> ${escHtml(state.eps.nombre)}<br>
      📅 <strong>Fecha:</strong> ${formatFecha(state.fecha)}<br>
      🕐 <strong>Horario:</strong> ${state.hora_inicio} – ${hFin}
      ${state.motivo ? `<br>💬 <strong>Motivo:</strong> ${escHtml(state.motivo)}` : ""}
    `;
    messages.appendChild(el);
    scrollBottom();
  }

  function showSuccess(id_cita) {
    const el = document.createElement("div");
    el.className = "cb-success-box";
    el.innerHTML = `
      <span class="cb-check">✅</span>
      <strong>¡Cita agendada!</strong><br>
      Tu cita #${id_cita} fue registrada exitosamente.<br>
      <small>${formatFecha(state.fecha)} · ${state.hora_inicio} – ${state.hora_fin}</small>
    `;
    messages.appendChild(el);
    scrollBottom();
  }

  function clearFooter() {
    footer.innerHTML = "";
  }

  function scrollBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  // ── Utilidades ────────────────────────────────────────────

  function escHtml(str) {
    return String(str)
      .replace(/&/g,"&amp;")
      .replace(/</g,"&lt;")
      .replace(/>/g,"&gt;")
      .replace(/"/g,"&quot;");
  }

  function calcHoraFin(inicio, duracionMin) {
    const [h, m] = inicio.split(":").map(Number);
    const total  = h * 60 + m + duracionMin;
    return `${String(Math.floor(total/60)%24).padStart(2,"0")}:${String(total%60).padStart(2,"0")}`;
  }

  function formatFecha(iso) {
    if (!iso) return "";
    const [y, m, d] = iso.split("-");
    const meses = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
    return `${d} ${meses[parseInt(m)-1]} ${y}`;
  }

  function todayISO() {
    return new Date().toISOString().split("T")[0];
  }

  async function apiFetch(url, options = {}) {
    const res  = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    return res.json();
  }

  // ── FLUJO PRINCIPAL ───────────────────────────────────────

  function startFlow() {
    state.step = 1;
    updateProgress(0);
    typing();
    setTimeout(() => {
      removeTyping();
      botMsg("¡Hola! 👋 Soy el asistente de <strong>MediCitas EPS</strong>.<br>Te ayudo a agendar tu cita médica en pocos pasos.");
      setTimeout(() => askUsername(), 700);
    }, 900);
  }

  // PASO 1 – Pedir usuario
  function askUsername() {
    updateProgress(1);
    botMsg("Para empezar, escribe tu <strong>nombre de usuario</strong>:");
    footer.innerHTML = `
      <div class="cb-input-row">
        <input id="cb-inp-user" class="cb-input" type="text"
               placeholder="Tu usuario..." autocomplete="username" />
        <button class="cb-send-btn" id="cb-btn-user">
          <i class="bi bi-arrow-right"></i>
        </button>
      </div>`;
    const inp = document.getElementById("cb-inp-user");
    const btn = document.getElementById("cb-btn-user");
    inp.focus();

    const submit = () => {
      const val = inp.value.trim();
      if (!val) return;
      state._username = val;
      userMsg(val);
      clearFooter();
      askPassword();
    };
    btn.addEventListener("click", submit);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") submit(); });
  }

  // PASO 2 – Pedir contraseña
  function askPassword() {
    updateProgress(2);
    botMsg(`Hola <strong>${escHtml(state._username)}</strong> 👤<br>Ahora ingresa tu <strong>contraseña</strong>:`);
    footer.innerHTML = `
      <div class="cb-input-row">
        <div class="cb-pw-wrap">
          <input id="cb-inp-pw" class="cb-input" type="password"
                 placeholder="Tu contraseña..." autocomplete="current-password" />
          <button class="cb-pw-toggle" id="cb-pw-toggle" tabindex="-1">
            <i class="bi bi-eye" id="cb-eye-icon"></i>
          </button>
        </div>
        <button class="cb-send-btn" id="cb-btn-pw">
          <i class="bi bi-arrow-right"></i>
        </button>
      </div>`;
    const inp    = document.getElementById("cb-inp-pw");
    const btn    = document.getElementById("cb-btn-pw");
    const toggle = document.getElementById("cb-pw-toggle");
    const icon   = document.getElementById("cb-eye-icon");
    inp.focus();

    toggle.addEventListener("click", () => {
      inp.type = inp.type === "password" ? "text" : "password";
      icon.className = inp.type === "password" ? "bi bi-eye" : "bi bi-eye-slash";
    });

    const submit = async () => {
      const pass = inp.value;
      if (!pass) return;
      btn.disabled = true;
      userMsg("••••••••");
      clearFooter();
      typing();

      const data = await apiFetch("/chatbot/auth", {
        method: "POST",
        body: JSON.stringify({ username: state._username, password: pass }),
      });

      removeTyping();
      if (!data.ok) {
        botMsg(`❌ ${escHtml(data.error)}`, true);
        setTimeout(() => askUsername(), 800);
        return;
      }
      state.paciente = data;
      botMsg(`¡Bienvenido/a, <strong>${escHtml(data.nombre)} ${escHtml(data.apellido)}</strong>! 🎉`);
      setTimeout(() => askEspecialidad(), 600);
    };

    btn.addEventListener("click", submit);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") submit(); });
  }

  // PASO 3 – Seleccionar especialidad
  async function askEspecialidad() {
    updateProgress(3);
    typing();
    const data = await apiFetch("/chatbot/especialidades");
    removeTyping();

    if (!data.ok || !data.especialidades.length) {
      botMsg("⚠️ No hay especialidades disponibles en este momento. Contacta al administrador.", true);
      return;
    }

    botMsg("¿Para qué <strong>especialidad</strong> necesitas la cita?");
    showOptions(data.especialidades.map(e => ({
      label: `${e.nombre} (${e.duracion_min} min)`,
      value: e.id,
      data:  e,
      onSelect: (id, esp) => {
        state.especialidad = { id: esp.id, nombre: esp.nombre, duracion_min: esp.duracion_min };
        userMsg(esp.nombre);
        askMedico();
      },
    })));
  }

  // PASO 4 – Seleccionar médico
  async function askMedico() {
    updateProgress(4);
    typing();
    const data = await apiFetch(`/chatbot/medicos/${state.especialidad.id}`);
    removeTyping();

    if (!data.ok || !data.medicos.length) {
      botMsg("⚠️ No hay médicos disponibles para esa especialidad. Por favor elige otra.", true);
      setTimeout(() => askEspecialidad(), 600);
      return;
    }

    botMsg(`¿Con qué <strong>médico</strong> deseas atenderte?`);
    showOptions(data.medicos.map(m => ({
      label: m.nombre,
      value: m.id,
      data:  m,
      onSelect: (id, med) => {
        state.medico = { id: med.id, nombre: med.nombre };
        userMsg(med.nombre);
        askEps();
      },
    })));
  }

  // PASO 5 – Seleccionar EPS
  async function askEps() {
    updateProgress(5);
    typing();
    const data = await apiFetch("/chatbot/eps");
    removeTyping();

    if (!data.ok || !data.eps.length) {
      botMsg("⚠️ No hay EPS disponibles. Contacta al administrador.", true);
      return;
    }

    // Pre-seleccionar la EPS del paciente si existe
    const epsDefault = data.eps.find(e => e.id === state.paciente.id_eps);
    botMsg(`¿A través de qué <strong>EPS</strong> se realizará la consulta?`);

    if (epsDefault) {
      botMsg(`Tu EPS registrada es <strong>${escHtml(epsDefault.nombre)}</strong>. ¿Usamos esa o prefieres otra?`);
    }

    showOptions(data.eps.map(e => ({
      label: e.nombre,
      value: e.id,
      data:  e,
      onSelect: (id, eps) => {
        state.eps = { id: eps.id, nombre: eps.nombre };
        userMsg(eps.nombre);
        askFecha();
      },
    })));
  }

  // PASO 6 – Calendario de disponibilidad mensual
  function askFecha() {
    updateProgress(6);
    botMsg("📅 Selecciona la <strong>fecha</strong> de tu cita en el calendario:");
    clearFooter();

    // Estado del calendario
    const hoy      = new Date(); hoy.setHours(0,0,0,0);
    const hoyISO2  = hoy.toISOString().split("T")[0];
    let mesVista   = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    let dispCache  = {};

    // ── Construir el widget de calendario en el área de mensajes ──
    const calDiv = document.createElement("div");
    calDiv.id = "cb-calendario";
    calDiv.style.cssText = `
      margin: 4px 4px 4px 36px;
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      padding: 12px;
      animation: cb-slide-in .25s ease;
      max-width: 310px;
    `;
    calDiv.innerHTML = buildCalHTML();
    messages.appendChild(calDiv);
    scrollBottom();

    // Renderizar primer mes
    renderMes();

    // ── Helpers del calendario ────────────────────────────────────

    function buildCalHTML() {
      return `
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
          <button id="cb-cal-prev" style="${btnNavStyle()}" title="Mes anterior">&#8249;</button>
          <span id="cb-cal-title" style="font-family:'DM Serif Display',serif;font-size:1rem;color:#111827"></span>
          <button id="cb-cal-next" style="${btnNavStyle()}" title="Mes siguiente">&#8250;</button>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px;font-size:.7rem;color:#9ca3af">
          <span>🟢 Disponible</span>
          <span>🔴 Sin horarios</span>
          <span>⚫ Pasado</span>
        </div>
        <div id="cb-cal-grid" style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px"></div>
        <div id="cb-slots-area" style="margin-top:10px"></div>
      `;
    }

    function btnNavStyle() {
      return `width:28px;height:28px;border-radius:7px;border:1.5px solid #e5e7eb;
              background:#fff;color:#4b5563;cursor:pointer;font-size:1.1rem;
              display:inline-flex;align-items:center;justify-content:center;
              font-family:sans-serif;line-height:1;`;
    }

    // Adjuntar eventos de navegación
    setTimeout(() => {
      document.getElementById("cb-cal-prev")?.addEventListener("click", () => {
        const ant = new Date(mesVista.getFullYear(), mesVista.getMonth() - 1, 1);
        if (ant < new Date(hoy.getFullYear(), hoy.getMonth(), 1)) return;
        mesVista = ant;
        renderMes();
      });
      document.getElementById("cb-cal-next")?.addEventListener("click", () => {
        mesVista = new Date(mesVista.getFullYear(), mesVista.getMonth() + 1, 1);
        renderMes();
      });
    }, 50);

    async function renderMes() {
      const anio  = mesVista.getFullYear();
      const mes   = mesVista.getMonth() + 1;
      const clave = `${anio}-${String(mes).padStart(2,"0")}`;

      // Título
      const tit = document.getElementById("cb-cal-title");
      if (tit) {
        tit.textContent = mesVista.toLocaleDateString("es-CO", { month:"long", year:"numeric" });
        tit.style.textTransform = "capitalize";
      }

      // Deshabilitar prev si es mes actual
      const prev = document.getElementById("cb-cal-prev");
      if (prev) prev.disabled = mesVista <= new Date(hoy.getFullYear(), hoy.getMonth(), 1);

      const grid = document.getElementById("cb-cal-grid");
      if (!grid) return;

      // Encabezados días
      const dias = ["D","L","M","M","J","V","S"];
      let html = dias.map(d =>
        `<div style="text-align:center;font-size:.65rem;font-weight:700;color:#9ca3af;padding:2px 0">${d}</div>`
      ).join("");

      const primerDia = new Date(anio, mes - 1, 1).getDay();
      const numDias   = new Date(anio, mes, 0).getDate();

      for (let i = 0; i < primerDia; i++) html += `<div></div>`;
      for (let d = 1; d <= numDias; d++) {
        const fecha = `${anio}-${String(mes).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
        const esHoy = fecha === hoyISO2;
        html += `<div class="cb-cal-day" data-fecha="${fecha}"
                  style="${skeletonStyle(esHoy)}">${d}</div>`;
      }
      grid.innerHTML = html;

      // Limpiar slots al cambiar mes
      const slotsArea = document.getElementById("cb-slots-area");
      if (slotsArea) slotsArea.innerHTML = "";

      // Cargar disponibilidad
      if (!dispCache[clave]) {
        try {
          const url  = `/chatbot/disponibilidad/${state.medico.id}/${anio}/${mes}?duracion=${state.especialidad.duracion_min}`;
          const res  = await fetch(url);
          dispCache[clave] = await res.json();
        } catch { return; }
      }

      aplicarEstados(dispCache[clave]);
    }

    function skeletonStyle(esHoy) {
      return `aspect-ratio:1;border-radius:7px;display:flex;align-items:center;
              justify-content:center;font-size:.78rem;font-weight:600;
              font-family:'Plus Jakarta Sans',sans-serif;cursor:wait;
              background:linear-gradient(90deg,#f0f0f0 25%,#e8e8e8 50%,#f0f0f0 75%);
              background-size:200% 100%;animation:shimmerCal 1.2s infinite;color:transparent;
              ${esHoy ? "outline:2px solid #1a6cf6;outline-offset:1px;" : ""}`;
    }

    function aplicarEstados(data) {
      document.querySelectorAll(".cb-cal-day").forEach(el => {
        const fecha  = el.dataset.fecha;
        const estado = data[fecha] || "pasado";
        let style    = `aspect-ratio:1;border-radius:7px;display:flex;align-items:center;
                        justify-content:center;font-size:.78rem;font-weight:600;
                        font-family:'Plus Jakarta Sans',sans-serif;`;

        const esHoy = fecha === hoyISO2;
        if (esHoy) style += "outline:2px solid #1a6cf6;outline-offset:1px;font-weight:800;";

        if (estado === "disponible") {
          style += "background:#d1fae5;color:#065f46;border:1.5px solid #6ee7b7;cursor:pointer;";
          el.title = "Haz clic para ver horarios";
          el.addEventListener("click", () => seleccionarDia(el, fecha));
        } else if (estado === "lleno") {
          style += "background:#f9fafb;color:#9ca3af;text-decoration:line-through;cursor:not-allowed;opacity:.6;";
          el.title = "Sin horarios disponibles";
        } else if (estado === "bloqueado") {
          style += "background:#f9fafb;color:#e5e7eb;cursor:not-allowed;";
        } else {
          style += "background:transparent;color:#d1d5db;cursor:not-allowed;";
        }

        el.style.cssText = style;
      });
    }

    async function seleccionarDia(el, fecha) {
      // Marcar día seleccionado
      document.querySelectorAll(".cb-cal-day").forEach(d => {
        if (d.dataset.fecha && (data => data[d.dataset.fecha] === "disponible")(
          dispCache[`${mesVista.getFullYear()}-${String(mesVista.getMonth()+1).padStart(2,"0")}`] || {}
        )) {
          d.style.background = "#d1fae5";
          d.style.color = "#065f46";
          d.style.border = "1.5px solid #6ee7b7";
          d.style.transform = "";
          d.style.boxShadow = "";
        }
      });
      el.style.background  = "#1a6cf6";
      el.style.color       = "#fff";
      el.style.border      = "1.5px solid #1a6cf6";
      el.style.transform   = "scale(1.1)";
      el.style.boxShadow   = "0 4px 12px rgba(26,108,246,.4)";

      const slotsArea = document.getElementById("cb-slots-area");
      if (!slotsArea) return;

      const fechaFmt = new Date(fecha + "T12:00:00").toLocaleDateString("es-CO", {
        weekday:"long", day:"numeric", month:"long"
      });
      slotsArea.innerHTML = `
        <div style="font-size:.78rem;font-weight:600;color:#4b5563;margin-bottom:6px;
                    font-family:'Plus Jakarta Sans',sans-serif;">
          🕐 Horarios — <strong>${fechaFmt}</strong>
        </div>
        <div style="display:flex;align-items:center;gap:6px;color:#9ca3af;font-size:.78rem;
                    font-family:'Plus Jakarta Sans',sans-serif;">
          <div style="width:14px;height:14px;border:2px solid #e5e7eb;border-top-color:#1a6cf6;
                      border-radius:50%;animation:cbSpin .7s linear infinite"></div>
          Cargando horarios...
        </div>`;
      scrollBottom();

      try {
        const res   = await fetch(`/chatbot/slots/${state.medico.id}/${fecha}?duracion=${state.especialidad.duracion_min}`);
        const data  = await res.json();
        const slots = data.slots || [];

        if (!slots.length) {
          slotsArea.innerHTML += `<p style="font-size:.78rem;color:#9ca3af;font-style:italic;
                                             font-family:'Plus Jakarta Sans',sans-serif;margin:4px 0 0">
                                    Sin horarios disponibles este día.</p>`;
          return;
        }

        let slotsHtml = `<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">`;
        slots.forEach(hora => {
          const fin = calcHoraFin(hora, state.especialidad.duracion_min);
          slotsHtml += `<button class="cb-slot-hora" data-hora="${hora}" data-fecha="${fecha}"
            style="padding:4px 9px;border-radius:100px;border:1.5px solid #1a6cf6;
                   color:#1a6cf6;background:#fff;font-size:.75rem;font-weight:600;
                   font-family:'Plus Jakarta Sans',sans-serif;cursor:pointer;
                   transition:.15s;" title="${hora} – ${fin}">
            ${hora}
          </button>`;
        });
        slotsHtml += `</div>`;

        // Reemplazar spinner conservando el título
        const tituloSlots = slotsArea.querySelector("div:first-child");
        const tituloHtml  = tituloSlots ? tituloSlots.outerHTML : "";
        slotsArea.innerHTML = tituloHtml + slotsHtml;

        // Adjuntar eventos
        slotsArea.querySelectorAll(".cb-slot-hora").forEach(btn => {
          btn.addEventListener("mouseenter", () => {
            if (!btn.classList.contains("activo")) { btn.style.background="#e8f0fe"; }
          });
          btn.addEventListener("mouseleave", () => {
            if (!btn.classList.contains("activo")) { btn.style.background="#fff"; }
          });
          btn.addEventListener("click", () => elegirHora(btn, fecha, btn.dataset.hora));
        });
        scrollBottom();
      } catch {
        slotsArea.innerHTML += `<p style="font-size:.78rem;color:#ef4444;font-family:'Plus Jakarta Sans',sans-serif">
                                  Error al cargar horarios.</p>`;
      }
    }

    function elegirHora(btn, fecha, hora) {
      // Desmarcar anteriores
      document.querySelectorAll(".cb-slot-hora").forEach(b => {
        b.classList.remove("activo");
        b.style.background = "#fff";
        b.style.color      = "#1a6cf6";
        b.style.boxShadow  = "";
      });
      // Marcar seleccionado
      btn.classList.add("activo");
      btn.style.background = "#1a6cf6";
      btn.style.color      = "#fff";
      btn.style.boxShadow  = "0 3px 10px rgba(26,108,246,.35)";

      state.fecha       = fecha;
      state.hora_inicio = hora;
      state.hora_fin    = calcHoraFin(hora, state.especialidad.duracion_min);

      const horaFin  = state.hora_fin;
      const fechaFmt = new Date(fecha + "T12:00:00").toLocaleDateString("es-CO", {
        weekday:"long", day:"numeric", month:"long"
      });

      userMsg(`${formatFecha(fecha)} a las ${hora}`);

      // Deshabilitar el calendario para que no se pueda cambiar
      document.querySelectorAll(".cb-cal-day, .cb-slot-hora, #cb-cal-prev, #cb-cal-next")
        .forEach(el => { el.style.pointerEvents = "none"; el.style.opacity = "0.7"; });
      btn.style.opacity = "1";  // mantener hora seleccionada visible

      clearFooter();
      askMotivo();
    }
  }

  // PASO 7 – (eliminado: ahora el calendario maneja fecha + hora en un solo paso)

  // PASO 7b – Motivo (opcional)
  function askMotivo() {
    botMsg("💬 ¿Tienes algún <strong>motivo</strong> de consulta? <small style='color:#6b7280'>(Opcional)</small>");
    footer.innerHTML = `
      <div class="cb-input-row">
        <input id="cb-inp-motivo" class="cb-input" type="text"
               placeholder="Ej: Dolor de cabeza frecuente... (o déjalo vacío)" />
        <button class="cb-send-btn" id="cb-btn-motivo">
          <i class="bi bi-arrow-right"></i>
        </button>
      </div>`;
    const inp = document.getElementById("cb-inp-motivo");
    const btn = document.getElementById("cb-btn-motivo");
    inp.focus();

    const submit = () => {
      state.motivo = inp.value.trim();
      userMsg(state.motivo || "(Sin motivo especificado)");
      clearFooter();
      confirmStep();
    };
    btn.addEventListener("click", submit);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") submit(); });
  }

  // PASO 8 – Confirmación
  function confirmStep() {
    updateProgress(8);
    botMsg("¡Perfecto! Revisa el resumen de tu cita:");
    showSummary();
    setTimeout(() => {
      botMsg("¿Confirmas el agendamiento?");
      showOptions([
        {
          label: "✅ Confirmar cita",
          value: "confirm",
          onSelect: () => { userMsg("Confirmar cita"); submitCita(); },
        },
        {
          label: "✏️ Corregir",
          value: "edit",
          onSelect: () => { userMsg("Quiero corregir algo"); resetToStep3(); },
        },
      ]);
    }, 400);
  }

  // PASO 9 – Enviar cita a la API
  async function submitCita() {
    typing();
    const data = await apiFetch("/chatbot/agendar", {
      method: "POST",
      body: JSON.stringify({
        id_paciente:     state.paciente.id_paciente,
        id_medico:       state.medico.id,
        id_especialidad: state.especialidad.id,
        id_eps:          state.eps.id,
        fecha:           state.fecha,
        hora_inicio:     state.hora_inicio,
        motivo:          state.motivo,
      }),
    });
    removeTyping();

    if (!data.ok) {
      // Mostrar error y detalle de cruce si existe
      let msg = `❌ <strong>${escHtml(data.error)}</strong>`;
      if (data.cruce && data.cruce.length) {
        msg += "<br><small>Horarios ocupados:</small>";
        data.cruce.forEach(c => {
          msg += `<br><small>• ${c.hora_inicio || ""} – ${c.hora_fin || ""}</small>`;
        });
      }
      botMsg(msg, true);
      setTimeout(() => {
        botMsg("¿Deseas elegir otro horario?");
        showOptions([
          { label: "📅 Cambiar fecha u hora", value: "fecha",
            onSelect: () => { userMsg("Cambiar fecha u hora"); state.fecha = null; state.hora_inicio = null; askFecha(); } },
          { label: "🔄 Cambiar médico", value: "medico",
            onSelect: () => { userMsg("Cambiar médico"); resetToStep3(); } },
        ]);
      }, 400);
      return;
    }

    // Éxito
    state.hora_fin = data.hora_fin;
    showSuccess(data.id_cita);
    setTimeout(() => {
      botMsg("¿Deseas agendar otra cita?");
      showOptions([
        {
          label: "📅 Nueva cita",
          value: "new",
          onSelect: () => { userMsg("Nueva cita"); resetToStep3(); },
        },
        {
          label: "🚪 Finalizar",
          value: "bye",
          onSelect: () => { userMsg("Finalizar"); farewell(); },
        },
      ]);
    }, 600);
  }

  function farewell() {
    botMsg("¡Hasta luego! 👋 Que tengas una excelente atención médica. Puedes cerrar este chat cuando desees.");
    clearFooter();
  }

  // ── Helpers de navegación ─────────────────────────────────

  function resetToStep3() {
    state.especialidad = null;
    state.medico       = null;
    state.eps          = null;
    state.fecha        = null;
    state.hora_inicio  = null;
    state.hora_fin     = null;
    state.motivo       = "";
    askEspecialidad();
  }

}); // fin DOMContentLoaded
