document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const toggle = document.getElementById("theme-toggle");
  const icon = toggle?.querySelector(".theme-icon");
  const label = toggle?.querySelector(".theme-label");
  const themeColor = document.getElementById("theme-color");

  if (!toggle) return;

  function applyTheme(theme, saveChoice = false) {
    const isDark = theme === "dark";
    root.dataset.theme = isDark ? "dark" : "light";
    toggle.setAttribute("aria-pressed", String(isDark));
    toggle.setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} theme`);
    toggle.title = `Switch to ${isDark ? "light" : "dark"} theme`;
    if (icon) icon.textContent = isDark ? "☀" : "☾";
    if (label) label.textContent = isDark ? "Light" : "Dark";
    if (themeColor) themeColor.content = isDark ? "#111a27" : "#0f2744";

    if (saveChoice) {
      try {
        localStorage.setItem("airforce-school-theme", isDark ? "dark" : "light");
      } catch (error) {
        // The selected theme still works for this page if storage is unavailable.
      }
    }
  }

  applyTheme(root.dataset.theme === "dark" ? "dark" : "light");
  toggle.addEventListener("click", () => {
    applyTheme(root.dataset.theme === "dark" ? "light" : "dark", true);
  });
});
