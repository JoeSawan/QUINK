import { SerialService } from "./SerialService.js";

export class SerialManager {
  constructor() {
    this.service = new SerialService();
    this.connectBtn = document.getElementById("connectBtn");
  }

  init() {
    this.connectBtn.addEventListener("click", () => this.toggleConnection());
  }

  async toggleConnection() {
    try {
      if (!this.service.isConnected) {
        await this.service.connect();
        this.connectBtn.textContent = "قطع الاتصال";
      } else {
        await this.service.disconnect();
        this.connectBtn.textContent = "الاتصال";
      }
    } catch (error) {
      console.error("خطأ في الاتصال:", error);
      this.connectBtn.textContent = "الاتصال"; // إعادة الزر لحالته الأصلية
    }
  }
}
