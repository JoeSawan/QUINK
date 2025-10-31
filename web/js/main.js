import { SerialManager } from "./serial/SerialManager.js";
import { PinManager } from "./pins/PinManager.js";

document.addEventListener("DOMContentLoaded", () => {
  const themeManager = new ThemeManager();
  const serialManager = new SerialManager();
  serialManager.init();

  // تهيئة مدير الـ Pins
  const pinManager = new PinManager("container");
  pinManager.render();
});

class ThemeManager {
  constructor() {
    this.darkModeBtn = document.getElementById("darkModeBtn");
    this.body = document.body;
    this.init();
  }

  init() {
    this.loadSavedTheme();
    this.darkModeBtn.addEventListener("click", () => this.toggleTheme());
  }

  toggleTheme() {
    const isDark = this.body.getAttribute("data-theme") === "dark";
    this.body.setAttribute("data-theme", isDark ? "light" : "dark");
    this.darkModeBtn.textContent = isDark ? "الوضع الداكن" : "الوضع الفاتح";
    localStorage.setItem("theme", isDark ? "light" : "dark");
  }

  loadSavedTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    this.body.setAttribute("data-theme", savedTheme);
    this.darkModeBtn.textContent =
      savedTheme === "dark" ? "الوضع الفاتح" : "الوضع الداكن";
  }
}
