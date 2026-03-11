# 🚀 Quick Setup Guide

**For programmers who want to clone and run immediately**

---

## ⚡ One-Command Setup

### Windows (PowerShell/CMD)
```cmd
setup.bat
```

### Linux/Mac or Git Bash
```bash
chmod +x setup.sh
./setup.sh
```

This will:
1. ✅ Check Python version (3.8-3.10 required)
2. ✅ Create virtual environment
3. ✅ Install all dependencies
4. ✅ Train the Rasa model

**Time:** ~5-10 minutes

---

## ▶️ Running the Chatbot

### Windows
```cmd
run.bat
```

### Linux/Mac or Git Bash
```bash
./run.sh
```

This will:
1. ✅ Start action server (port 5055)
2. ✅ Start Rasa server (port 5005)
3. ✅ Start web UI (port 8000)
4. ✅ Open browser automatically

**Access:** http://localhost:8000

---

## 📋 Requirements

- **Python 3.10** (Recommended)
- Python 3.8 or 3.9 also work
- **NOT compatible** with Python 3.11+

---

## 🐛 Troubleshooting

### "Python version not supported"
**Fix:** Install Python 3.10 from [python.org](https://www.python.org/downloads/release/python-31011/)

### "Virtual environment not found"
**Fix:** Run `setup.bat` (Windows) or `./setup.sh` (Linux/Mac) first

### Ports already in use
**Fix:** Stop existing Rasa servers or change ports in scripts

---

## 📞 Contact

**Maintainer:** Piyush Mishra  
**Phone:** 9975765965  
**Institute:** VIT Pune

---

**That's it! Two commands to get started:** `setup.bat` then `run.bat`
