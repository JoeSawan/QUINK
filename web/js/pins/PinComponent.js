export class PinComponent {
  constructor(config) {
    this.config = config;
    this.element = this.createTemplate();
    this.initEventListeners();
  }

  createTemplate() {
    const div = document.createElement("div");
    div.className = "element-row";
    div.innerHTML = `
      <div class="pin-id">${this.config.id}</div>
      <div class="controls">
        ${this.getControlMarkup()}  
      </div>
      <div class="status-led ${this.config.value ? "active" : ""}"></div>
      <button class="mode-btn">${this.config.modes[this.config.mode]}</button>
    `;
    return div;
  }

  getControlMarkup() {
    switch (this.config.modes[this.config.mode]) {
      case "🌓":
        return '<input type="range" min="0" max="255">';
      case "📈":
        return '<progress value="0" max="1024"></progress>';
      case "🔌":
        return '<label class="switch"><input type="checkbox"><div class="slider"></div></label>';
      default:
        return "";
    }
  }

  initEventListeners() {
    this.element.querySelector(".mode-btn").addEventListener("click", () => {
      this.config.mode = (this.config.mode + 1) % this.config.modes.length;
      this.updateView();
    });
  }

  updateView() {
    this.element.querySelector(".mode-btn").textContent =
      this.config.modes[this.config.mode];
    this.element.querySelector(".controls").innerHTML = this.getControlMarkup();
  }
}
