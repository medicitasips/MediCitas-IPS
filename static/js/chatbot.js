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
