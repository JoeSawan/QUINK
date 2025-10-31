export class SerialService {
  constructor() {
    this.encoder = new TextEncoder();
    this.decoder = new TextDecoder();
    this.serialPort = null;
    this.reader = null;
    this.writer = null;
  }

  get isConnected() {
    return !!this.serialPort;
  }

  async connect() {
    try {
      this.serialPort = await navigator.serial.requestPort();
      await this.serialPort.open({ baudRate: 115200 });
      this.setupListeners();
    } catch (error) {
      console.error("فشل الاتصال:", error);
      throw error; // لإظهار الخطأ في SerialManager
    }
  }

  async disconnect() {
    await this.serialPort.close();
    if (this.reader) await this.reader.cancel();
    if (this.writer) await this.writer.close();
    if (this.serialPort) await this.serialPort.close();
    this.serialPort = null;
  }
  async setupListeners() {
    while (this.serialPort.readable) {
      this.reader = this.serialPort.readable.getReader();
      try {
        while (true) {
          const { value, done } = await this.reader.read();
          if (done) break;
          console.log("البيانات المستلمة:", this.decoder.decode(value));
        }
      } catch (error) {
        console.error("خطأ في القراءة:", error);
      } finally {
        this.reader.releaseLock();
      }
    }
  }
  async sendData(data) {
    if (!this.writer) {
      this.writer = this.serialPort.writable.getWriter();
    }
    await this.writer.write(this.encoder.encode(data));
  }
}
