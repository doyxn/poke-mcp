# 🐾 poke-mcp

A lightweight **MCP server** for experimenting with **Poke Interaction Co. integrations**.

> Minimal, no-auth version of an MCP server — designed for **personal use, quick testing, and hacking**.

---

## ✨ Overview

This project is a simplified MCP server adapted from the Bookmark Manager MCP example.

* ⚡ Runs as a lightweight MCP server
* 🔌 Connects to MCP-compatible clients (like Poke)
* 🧪 Stripped down for experimentation
* 🔓 **No OAuth / authentication** (intentionally removed)

---

## 📦 Based On

Adapted from:
https://github.com/InteractionCo/poke-mcp-examples/tree/main/bookmark-manager

### Changes

* ❌ Removed OAuth + AuthKit + DCR
* 🧹 Simplified architecture
* 🧑‍💻 Tailored for personal/local workflows
* ⚡ Reduced setup complexity

---

## 🧠 What is MCP?

**Model Context Protocol (MCP)** allows tools and services to integrate with LLMs in a structured way.

This server acts as a bridge between:

* Your local service
* MCP-compatible clients

---

## 🚀 Getting Started

### 1. Clone the repo

```bash id="clone1"
git clone https://github.com/your-username/poke-mcp.git
cd poke-mcp
```

### 2. Install dependencies

```bash id="pip1"
pip install -r requirements.txt
```

### 3. Run locally

Use the MCP local development tooling:

```bash id="mcp1"
npx @modelcontextprotocol/inspector
```

Then connect to your server (typically something like):

```
http://localhost:8000/mcp
```

---

## 🔌 Connecting to Poke

1. Open Poke settings (Connections)
2. Add your MCP server URL
3. Start interacting with your tools

No authentication required.

---

## 🛠 Features

This project is intentionally minimal, but demonstrates:

* MCP server setup
* Tool registration and execution
* Request handling via MCP protocol

---

## 🧪 Use Cases

* Personal automation tools
* Learning how MCP servers work
* Rapid prototyping
* Testing integrations without auth overhead

---

## ⚠️ Notes

* This is **not production-ready**
* No authentication or user isolation
* Intended for **personal / local use only**
* Based on a more complete OAuth-enabled example

---

## 🔐 About Authentication

The original project included:

* OAuth 2.1 + PKCE
* Dynamic Client Registration (DCR)
* JWT-based user scoping

All of that has been **removed** here for simplicity.

If you need authentication, refer back to the original example.

---

## 🤝 Contributing

This is a personal project, but feel free to fork and experiment.

---

## Next Steps
 - Switching to Notion Database
 - Re-implementing OAuth :)
 - Metadata scraping
 
---

## 📄 License

MIT
