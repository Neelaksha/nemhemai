const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion
} = require("@whiskeysockets/baileys");

const qrcode = require("qrcode-terminal");

const PREFIX = "!";

async function startBot() {
  const { state, saveCreds } = await useMultiFileAuthState("auth");
  const { version } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    version,
    auth: state,
    browser: ["Ubuntu", "Chrome", "20.0.04"],
    printQRInTerminal: false
  });

  // CONNECTION
  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log("Scan QR:");
      qrcode.generate(qr, { small: true });
    }

    if (connection === "close") {
      const reason = lastDisconnect?.error?.output?.statusCode;
      if (reason !== DisconnectReason.loggedOut) startBot();
    } else if (connection === "open") {
      console.log("✅ Connected");
    }
  });

  sock.ev.on("creds.update", saveCreds);

  // MESSAGE HANDLER
  sock.ev.on("messages.upsert", async ({ messages }) => {
    try {
      const msg = messages[0];
      if (!msg.message ) return;

      const from = msg.key.remoteJid;

      const text =
        msg.message.conversation ||
        msg.message.extendedTextMessage?.text ||
        msg.message.imageMessage?.caption ||
        "";

      if (!text.startsWith(PREFIX)) return;

      const args = text.slice(PREFIX.length).trim().split(" ");
      const command = args.shift().toLowerCase();

      console.log("Command:", command);

      // COMMANDS
      switch (command) {
        case "hi":
          await sock.sendMessage(from, { text: "Hello 👋" });
          break;

        case "ping":
          await sock.sendMessage(from, { text: "🏓 Pong!" });
          break;

        case "echo":
          await sock.sendMessage(from, { text: args.join(" ") || "Nothing to echo" });
          break;

        case "menu":
          await sock.sendMessage(from, {
            text: `📜 Commands:
!hi
!ping
!echo <text>
!menu`
          });
          break;

        default:
          await sock.sendMessage(from, { text: "Unknown command ❌" });
      }
    } catch (err) {
      console.error("Error:", err);
    }
  });
}

startBot();