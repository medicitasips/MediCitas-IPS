/**
 * session_manager.js – Cierre automático de sesión
 *
 * Dos mecanismos:
 *   1. Inactividad: si el usuario no interactúa durante INACTIVITY_MS,
 *      muestra un modal de advertencia con cuenta regresiva.
 *      Si no reacciona en WARNING_MS, cierra la sesión.
 *
 *   2. Cierre de pestaña/navegador: usa sendBeacon() + visibilitychange
 *      para enviar POST /auth/logout/silencioso al servidor.
 *      Un flag en sessionStorage distingue recarga de cierre real.
 */

"use strict";

(function () {

  // ── Configuración ─────────────────────────────────────────────
  const INACTIVITY_MS = 15 * 60 * 1000;   // 15 minutos sin actividad
  const WARNING_MS    =  1 * 60 * 1000;   // 60 segundos de advertencia
  const LOGOUT_URL    = "/auth/logout/silencioso";
  const LOGIN_URL     = "/auth/login";

  // ── No ejecutar en la página de login/registro (sin sesión) ──
  // El servidor inyecta este atributo solo cuando hay sesión activa
  const bodyEl = document.body;
  if (!bodyEl.dataset.usuarioActivo) return;

  // ── Estado interno ────────────────────────────────────────────
  let inactivityTimer = null;
  let warningTimer    = null;
  let warningInterval = null;
  let modalEl         = null;
  let countdown       = Math.floor(WARNING_MS / 1000);

  // ── 1. CIERRE DE PESTAÑA / NAVEGADOR ─────────────────────────

  /**
   * Marca que la página se está descargando.
   * beforeunload se dispara tanto en cierre como en recarga/navegación.
   * sessionStorage (que persiste entre recargas de la misma pestaña)
   * nos permite distinguir: si el flag existe al cargar → fue recarga.
   */
  window.addEventListener("beforeunload", () => {
    sessionStorage.setItem("mc_reloading", "1");
  });

  /**
   * visibilitychange se dispara cuando la pestaña se oculta (cambio de
   * pestaña, minimizar, cerrar). Si el documento queda "hidden" y el
   * flag de recarga NO está en sessionStorage, es un cierre real.
   */
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      // Si hay flag de recarga, no hacer nada (se limpia en la carga)
      if (sessionStorage.getItem("mc_reloading")) return;

      // Cerrar sesión con sendBeacon (funciona aunque el tab se cierre)
      const blob = new Blob([], { type: "application/json" });
      navigator.sendBeacon(LOGOUT_URL, blob);
    }
  });

  // Al cargar la página, limpiar el flag de recarga
  window.addEventListener("load", () => {
    sessionStorage.removeItem("mc_reloading");
  });

  // ── 2. CIERRE POR INACTIVIDAD ─────────────────────────────────

  // Eventos que se consideran "actividad del usuario"
  const ACTIVITY_EVENTS = [
    "mousemove", "mousedown", "keydown",
    "touchstart", "scroll", "click",
  ];

  function resetTimer() {
    clearTimeout(inactivityTimer);
    clearTimeout(warningTimer);
    clearInterval(warningInterval);
    hideWarningModal();
    countdown = Math.floor(WARNING_MS / 1000);

    inactivityTimer = setTimeout(showWarningModal, INACTIVITY_MS);
  }

  // Registrar eventos de actividad con passive:true para no afectar scroll
  ACTIVITY_EVENTS.forEach(ev => {
    document.addEventListener(ev, resetTimer, { passive: true });
  });

  // Iniciar el temporizador al cargar la página
  resetTimer();

  // ── Modal de advertencia ──────────────────────────────────────

  function showWarningModal() {
    if (!modalEl) createModal();

    // Actualizar contador inicial
    updateCountdown();

    // Mostrar el modal
    modalEl.style.display = "flex";
    requestAnimationFrame(() => {
      modalEl.classList.add("mc-modal-visible");
    });

    // Cuenta regresiva cada segundo
    warningInterval = setInterval(() => {
      countdown--;
      updateCountdown();
      if (countdown <= 0) {
        clearInterval(warningInterval);
        doLogout();
      }
    }, 1000);

    // Logout automático al acabar el tiempo de advertencia
    warningTimer = setTimeout(doLogout, WARNING_MS);
  }

  function hideWarningModal() {
    if (!modalEl) return;
    modalEl.classList.remove("mc-modal-visible");
    setTimeout(() => {
      if (modalEl) modalEl.style.display = "none";
    }, 300);
  }

  function updateCountdown() {
    const el = document.getElementById("mc-countdown");
    if (el) el.textContent = countdown;
  }

  function createModal() {
    // Estilos inline para no depender de archivos CSS externos
    const style = document.createElement("style");
    style.textContent = `
      #mc-overlay {
        position: fixed; inset: 0; z-index: 99999;
        background: rgba(15,23,42,.65);
        backdrop-filter: blur(4px);
        display: none;
        align-items: center; justify-content: center;
        opacity: 0; transition: opacity .3s ease;
      }
      #mc-overlay.mc-modal-visible { opacity: 1; }
      #mc-modal {
        background: #fff;
        border-radius: 18px;
        padding: 36px 40px;
        max-width: 420px; width: 90%;
        box-shadow: 0 24px 60px rgba(0,0,0,.25);
        text-align: center;
        transform: translateY(12px) scale(.97);
        transition: transform .3s ease;
        font-family: 'Plus Jakarta Sans', Arial, sans-serif;
      }
      #mc-overlay.mc-modal-visible #mc-modal {
        transform: translateY(0) scale(1);
      }
      #mc-modal .mc-icon {
        font-size: 2.8rem; margin-bottom: 12px; display: block;
      }
      #mc-modal h5 {
        font-size: 1.15rem; font-weight: 700;
        color: #0f172a; margin: 0 0 8px;
      }
      #mc-modal p {
        font-size: .9rem; color: #4b5563;
        margin: 0 0 6px; line-height: 1.5;
      }
      #mc-countdown-wrap {
        font-size: 2.5rem; font-weight: 800;
        color: #ef4444; margin: 16px 0;
        line-height: 1;
      }
      #mc-countdown-wrap small {
        display: block; font-size: .78rem;
        font-weight: 500; color: #9ca3af; margin-top: 2px;
      }
      #mc-btn-continuar {
        background: #1a6cf6; color: #fff; border: none;
        border-radius: 10px; padding: 11px 28px;
        font-size: .9rem; font-weight: 700; cursor: pointer;
        width: 100%; margin-top: 8px;
        font-family: 'Plus Jakarta Sans', Arial, sans-serif;
        transition: background .2s;
      }
      #mc-btn-continuar:hover { background: #1250c4; }
      #mc-btn-cerrar {
        background: none; border: none; color: #6b7280;
        font-size: .82rem; cursor: pointer; margin-top: 10px;
        width: 100%; font-family: 'Plus Jakarta Sans', Arial, sans-serif;
      }
      #mc-btn-cerrar:hover { color: #ef4444; }
    `;
    document.head.appendChild(style);

    // HTML del modal
    modalEl = document.createElement("div");
    modalEl.id = "mc-overlay";
    modalEl.setAttribute("role", "alertdialog");
    modalEl.setAttribute("aria-modal", "true");
    modalEl.setAttribute("aria-labelledby", "mc-modal-title");
    modalEl.innerHTML = `
      <div id="mc-modal">
        <span class="mc-icon">⏱️</span>
        <h5 id="mc-modal-title">¿Sigues ahí?</h5>
        <p>Por seguridad, tu sesión se cerrará automáticamente<br>debido a inactividad.</p>
        <div id="mc-countdown-wrap">
          <span id="mc-countdown">${countdown}</span>
          <small>segundos restantes</small>
        </div>
        <button id="mc-btn-continuar">Continuar sesión</button>
        <button id="mc-btn-cerrar">Cerrar sesión ahora</button>
      </div>
    `;
    document.body.appendChild(modalEl);

    // Eventos de los botones
    document.getElementById("mc-btn-continuar").addEventListener("click", () => {
      resetTimer();
    });
    document.getElementById("mc-btn-cerrar").addEventListener("click", () => {
      doLogout();
    });
  }

  // ── Ejecutar el logout ────────────────────────────────────────

  function doLogout() {
    // Limpiar todos los timers
    clearTimeout(inactivityTimer);
    clearTimeout(warningTimer);
    clearInterval(warningInterval);

    // Llamada al servidor y redirección
    fetch(LOGOUT_URL, { method: "POST" })
      .finally(() => {
        window.location.href = LOGIN_URL + "?timeout=1";
      });
  }

})();
