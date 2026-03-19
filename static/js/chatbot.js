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

  // PASO 6 – Elegir fecha
  function askFecha() {
    updateProgress(6);
    botMsg("📅 ¿Qué <strong>fecha</strong> prefieres para la cita?");
    footer.innerHTML = `
      <div class="cb-input-row">
        <input id="cb-inp-fecha" class="cb-input" type="date"
               min="${todayISO()}" value="${todayISO()}" />
        <button class="cb-send-btn" id="cb-btn-fecha">
          <i class="bi bi-arrow-right"></i>
        </button>
      </div>`;
    const inp = document.getElementById("cb-inp-fecha");
    const btn = document.getElementById("cb-btn-fecha");

    const submit = () => {
      const val = inp.value;
      if (!val) return;
      state.fecha = val;
      userMsg(formatFecha(val));
      clearFooter();
      askHora();
    };
    btn.addEventListener("click", submit);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") submit(); });
  }

  // PASO 7 – Elegir hora
  function askHora() {
    updateProgress(7);
    const hFin = calcHoraFin("__:__", state.especialidad.duracion_min);
    botMsg(`🕐 ¿A qué <strong>hora</strong> deseas la cita?<br><small style="color:#6b7280">La consulta dura <strong>${state.especialidad.duracion_min} minutos</strong>. La hora de fin se calcula automáticamente.</small>`);
    footer.innerHTML = `
      <div class="cb-input-row">
        <input id="cb-inp-hora" class="cb-input" type="time"
               step="900" value="08:00" />
        <button class="cb-send-btn" id="cb-btn-hora">
          <i class="bi bi-arrow-right"></i>
        </button>
      </div>
      <div id="cb-hora-fin-preview" style="font-size:.75rem;color:#6b7280;margin-top:4px;text-align:right;padding-right:4px"></div>`;
    const inp     = document.getElementById("cb-inp-hora");
    const btn     = document.getElementById("cb-btn-hora");
    const preview = document.getElementById("cb-hora-fin-preview");

    const updatePreview = () => {
      if (inp.value) {
        const fin = calcHoraFin(inp.value, state.especialidad.duracion_min);
        preview.textContent = `Hora de fin estimada: ${fin}`;
      }
    };
    inp.addEventListener("change", updatePreview);
    inp.addEventListener("input",  updatePreview);
    updatePreview();

    const submit = () => {
      const val = inp.value;
      if (!val) return;
      state.hora_inicio = val;
      state.hora_fin    = calcHoraFin(val, state.especialidad.duracion_min);
      userMsg(`${val} (fin: ${state.hora_fin})`);
      clearFooter();
      askMotivo();
    };
    btn.addEventListener("click", submit);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") submit(); });
  }

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
          { label: "🕐 Cambiar hora", value: "hora",
            onSelect: () => { userMsg("Cambiar hora"); state.hora_inicio = null; askHora(); } },
          { label: "📅 Cambiar fecha", value: "fecha",
            onSelect: () => { userMsg("Cambiar fecha"); state.fecha = null; askFecha(); } },
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
