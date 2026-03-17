/**
 * main.js – MediCitas EPS v2
 * Funcionalidades:
 *   • Validación de formularios Bootstrap
 *   • Fecha mínima en inputs date (no permite fechas pasadas)
 *   • Auto-cierre de alertas flash (5 s)
 *   • Solo dígitos en campos de documento
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
  initBootstrapValidation();
  setMinDate();
  autoCloseAlerts();
  soloDigitosEnDocumento();
  activarTooltips();
});

/* ── Validación Bootstrap ─────────────────────────────────── */
function initBootstrapValidation() {
  document.querySelectorAll("form[novalidate]").forEach(form => {
    form.addEventListener("submit", e => {
      if (!form.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });
}

/* ── Fecha mínima = hoy (solo en formularios de reserva/edición) */
function setMinDate() {
  const hoy = new Date().toISOString().split("T")[0];
  document.querySelectorAll('input[type="date"]').forEach(input => {
    if (!input.value) input.setAttribute("min", hoy);
  });
}

/* ── Auto-cerrar alertas flash ───────────────────────────── */
function autoCloseAlerts() {
  document.querySelectorAll(".alert.alert-dismissible").forEach(alert => {
    setTimeout(() => {
      const inst = bootstrap.Alert.getOrCreateInstance(alert);
      inst?.close();
    }, 6000);
  });
}

/* ── Solo dígitos en campos de documento ─────────────────── */
function soloDigitosEnDocumento() {
  document.querySelectorAll('input[name="documento"]').forEach(input => {
    input.addEventListener("keypress", e => {
      if (!/[0-9]/.test(e.key)) e.preventDefault();
    });
    input.addEventListener("paste", e => {
      const txt = (e.clipboardData || window.clipboardData).getData("text");
      if (!/^\d+$/.test(txt)) e.preventDefault();
    });
  });
}

/* ── Tooltips Bootstrap ──────────────────────────────────── */
function activarTooltips() {
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el, { trigger: "hover" });
  });
}
