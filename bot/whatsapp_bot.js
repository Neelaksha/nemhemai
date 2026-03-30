const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion
} = require("@whiskeysockets/baileys");

const qrcode = require("qrcode-terminal");

const PREFIX = "!";
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const BOT_JWT_TOKEN = process.env.BOT_JWT_TOKEN;

if (!BOT_JWT_TOKEN) {
  console.error("❌ BOT_JWT_TOKEN not set in .env");
}

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

      // Handle image OCR (auto)
      if (msg.message.imageMessage && !msg.key.fromMe) {
        await handleOCR(sock, msg, from);
        return;
      }

      const text =
        msg.message.conversation ||
        msg.message.extendedTextMessage?.text ||
        msg.message.imageMessage?.caption ||
        "";

      if (!text.startsWith(PREFIX)) return;

      const args = text.slice(PREFIX.length).trim().split(" ");
      const command = args.shift().toLowerCase();

      console.log("NemhemAI Command:", command);


      // NemhemAI COMMANDS
      switch (command) {
        case "chat":
          if (!args.length) {
            await sock.sendMessage(from, { text: "Usage: !chat <your prompt>" });
            return;
          }
          await handleChat(sock, from, args.join(" "));
          break;

        case "health":
          await handleHealth(sock, from);
          break;

        case "models":
          await handleModels(sock, from);
          break;

        case "menu":
        case "start":
          await sock.sendMessage(from, {
            text: `🤖 *NemhemAI WhatsApp Bot* 

📜 Commands:
!chat <prompt> → AI Chat (streaming)
!health → Backend status  
!models → List LLMs
!menu / !start → This help

📸 *Send photo → Auto OCR (Hindi+Eng)*

Backend: ${BACKEND_URL}`
          });
          break;

        default:
          await sock.sendMessage(from, { text: "❌ Unknown command. Type !menu for help." });
      }

    } catch (err) {
      console.error("NemhemAI Error:", err);
    }
  });

  // OCR Handler Function
  async function handleOCR(sock, msg, from) {
    try {
      console.log("Processing OCR...");
      await sock.sendMessage(from, { text: "🔍 Processing OCR (Hindi+Eng)..." });

      const imageMsg = msg.message.imageMessage;
      const imageUrl = imageMsg.url;
      
      // Download image buffer
      const imageResponse = await fetch(imageUrl);
      const arrayBuffer = await imageResponse.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);

      // Create Blob for Node FormData compatibility
      const imageBlob = new Blob([buffer], { type: 'image/jpeg' });

      // Prepare multipart form
      const form = new FormData();
      form.append('file', imageBlob, 'image.jpg');
      form.append('languages', 'hin+eng');
      form.append('enhance', 'true');

      const ocrResp = await fetch(`${BACKEND_URL}/ocr`, {
        method: 'POST',
        body: form
      });
      
      if (ocrResp.ok) {
        const result = await ocrResp.json();
        const text = result.text || 'No text detected';
        const confidence = result.confidence || 0;
        await sock.sendMessage(from, { 
          text: `**OCR Result** (Confidence: ${Math.round(confidence * 100)}%)\n\n${text.substring(0, 4000)}` 
        });
      } else {
        await sock.sendMessage(from, { text: `❌ OCR failed: ${ocrResp.status}` });
      }
    } catch (err) {
      console.error("OCR Error:", err);
      await sock.sendMessage(from, { text: "❌ OCR error. Try again." });
    }
  }

  // Chat Handler (streaming /ask)
  async function handleChat(sock, from, prompt) {
    try {
      await sock.sendMessage(from, { text: "🤖 Thinking..." });

      const resp = await fetch(`${BACKEND_URL}/ask`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${BOT_JWT_TOKEN}`
        },
        body: JSON.stringify({
          prompt,
          model: 'llama3.1:latest',
          session_id: from,
          use_web_search: true
        })

      });

      if (!resp.ok) {
        await sock.sendMessage(from, { text: `❌ Backend error: ${resp.status}` });
        return;
      }

      let fullResponse = '';
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line);
                if (data.response) {
                  fullResponse += data.response;
                  // Send partial if too long
                  if (fullResponse.length > 2000) {
                    await sock.sendMessage(from, { text: fullResponse });
                    fullResponse = '';
                  }
                }
              } catch (e) {
                // Ignore parse errors
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      if (fullResponse) {
        await sock.sendMessage(from, { text: fullResponse });
      }
    } catch (err) {
      console.error("Chat Error:", err);
      await sock.sendMessage(from, { text: "❌ Chat error. Check backend?" });
    }
  }

  // Health Check
  async function handleHealth(sock, from) {
    try {
      const resp = await fetch(`${BACKEND_URL}/health`, {
        headers: { 'Authorization': `Bearer ${BOT_JWT_TOKEN}` }
      });
      if (resp.ok) {
        const data = await resp.json();
        await sock.sendMessage(from, { text: `✅ Backend: ${data.status || 'healthy'}` });
      } else {
        await sock.sendMessage(from, { text: `❌ Backend down (${resp.status})` });
      }
    } catch (err) {
      await sock.sendMessage(from, { text: `❌ Cannot reach backend: ${err.message}` });
    }
  }

  // Models List
  async function handleModels(sock, from) {
    try {
      const resp = await fetch(`${BACKEND_URL}/models/enabled`, {
        headers: { 'Authorization': `Bearer ${BOT_JWT_TOKEN}` }
      });
      if (resp.ok) {
        const data = await resp.json();
        const modelList = data.map(m => `• ${m.name}`).join('\n');
        await sock.sendMessage(from, { text: `**Available Models:**\n${modelList}` });
      } else {
        await sock.sendMessage(from, { text: '❌ Cannot fetch models' });
      }
    } catch (err) {
      await sock.sendMessage(from, { text: `❌ Error: ${err.message}` });
    }
  }
}

startBot();

