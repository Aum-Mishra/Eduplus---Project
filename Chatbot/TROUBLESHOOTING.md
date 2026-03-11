# Troubleshooting Guide - EduPlus PlaceMate AI

## Quick Diagnostic

Run this to check your setup:
```cmd
python validate_setup.py
```

---

## Common Issues & Solutions

### 1. **Python Version Error**

**Error Message:**
```
[ERROR] Python version 3.8, 3.9, or 3.10 required!
Current version: Python 3.11 (or 3.12, 3.13, etc.)
```

**Cause:** Rasa 3.6.13 only supports Python 3.8-3.10

**Solution:**
1. Download Python 3.10.0+ from https://www.python.org/downloads/release/python-3100/
2. During installation, ✅ CHECK: "Add Python 3.10 to PATH"
3. Restart terminal
4. Verify: `python3.10 --version`
5. Run setup: `setup_improved.bat`

**Alternative:** If multiple Python versions are installed:
```cmd
python3.10 -m venv venv_rasa
venv_rasa\Scripts\activate.bat
pip install -r requirements.txt
```

---

### 2. **"Virtual environment not found"**

**Error Message:**
```
[ERROR] Virtual environment not found!
Please run setup_improved.bat first
```

**Cause:** venv_rasa directory doesn't exist or isn't properly created

**Solution:**
```cmd
REM Delete and recreate venv
rmdir /s /q venv_rasa
python -m venv venv_rasa
venv_rasa\Scripts\activate.bat
pip install -r requirements.txt
```

---

### 3. **"No module named rasa"**

**Error Message:**
```
python -m rasa: No module named rasa
```

**Cause:** Rasa not installed in the virtual environment

**Solutions:**

**Option A - Full reinstall:**
```cmd
venv_rasa\Scripts\activate.bat
pip uninstall -y rasa rasa-sdk
pip install -r requirements.txt
```

**Option B - Install specific version:**
```cmd
venv_rasa\Scripts\activate.bat
pip install rasa==3.6.13 rasa-sdk==3.6.1
```

**Option C - Check venv activation:**
```cmd
REM Should show path with venv_rasa:
where python

REM Should show (venv_rasa) in prompt:
echo %PROMPT%
```

---

### 4. **"Models directory not found"**

**Error Message:**
```
[ERROR] Model directory not found
Models directory should exist after rasa train
```

**Cause:** Rasa model hasn't been trained

**Solution:**
```cmd
venv_rasa\Scripts\activate.bat
rasa train
```

**Expected Output:**
```
Training NLU (step 1/2)...
Training Core (step 2/2)...
Models directory created.
Model stored in '.\models\XXXXXXXX.tar.gz'
```

If this fails, see **Common Rasa Train Errors** below.

---

### 5. **"Connection refused" when starting shell**

**Error Message:**
```
HTTPConnectionPool: Max retries exceeded
ConnectionRefusedError: [Errno 111] Connection refused
```

**Cause:** Action server not running or port 5055 not accessible

**Solution:**

**Terminal 1 (Action Server):**
```cmd
venv_rasa\Scripts\activate.bat
python -m rasa run actions
```

Wait for message: `action server is running` on port 5055

**Terminal 2 (Chatbot Shell):**
```cmd
venv_rasa\Scripts\activate.bat
rasa shell
```

---

### 6. **"CSV file not found"**

**Error Message:**
```
[ERROR] data/company_placement_db.csv not found
```

**Cause:** CSV data file is missing or in wrong location

**Solution:**
```cmd
REM Check file exists
dir data\company_placement_db.csv

REM If missing, restore from backup or re-download
REM File should be ~500KB and contain company data
```

**Check CSV integrity:**
```python
python -c "import pandas; df=pd.read_csv('data/company_placement_db.csv'); print(f'Rows: {len(df)}, Cols: {df.shape[1]}')"
```

Expected: "Rows: 50, Cols: 12" (or similar)

---

## Common Rasa Train Errors

### **Error: "No NLU training examples"**

**Cause:** NLU data not properly formatted

**Solution:**
```cmd
rasa data validate
rasa train --debug
```

Fix issues in `data/nlu.yml` and retry.

---

### **Error: "Invalid YAML syntax"**

**Cause:** YAML indentation or syntax error

**Solution:**
1. Check specific file: `rasa data validate --fail-on-warnings`
2. Use online YAML validator: https://www.yamllint.com/
3. Ensure:
   - No tabs (only spaces)
   - Consistent indentation (usually 2 or 4 spaces)
   - No trailing whitespace

---

### **Error: "Low precision on intent XYZ"**

**Cause:** Not enough training examples for intent

**Solution:**
1. Add more training examples to `data/nlu.yml`:
```yaml
- intent: ask_avg_package
  examples: |
    - what is the average package for google
    - average salary at amazon
    - package details microsoft
    - salary range accenture
```

2. Retrain: `rasa train`

---

## Performance Issues

### **Training Takes Too Long**

**Normal timing:** 2-5 minutes for full training

**If longer than 10 minutes:**
1. Check CPU usage (should be 80-100%)
2. Close other applications
3. Check disk space (need 1GB+ free)

**Speed up training:**
```yaml
# In config.yml, reduce epochs:
- name: DIETClassifier
  epochs: 20  # Reduced from 100
```

---

### **Chatbot Responses are Slow**

**Cause:** Action server or model issues

**Solution:**
1. Restart action server
2. Check server logs for errors
3. Check CSV file size (should be < 10MB)

---

## Installation Issues

### **Permission Denied Error**

**Error:**
```
PermissionError: Access is denied
```

**Solution:**
1. Run CMD as Administrator
2. Or use `pip install --user` instead of system-wide

---

### **SSL Certificate Error**

**Error:**
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solution:**
```cmd
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

Or upgrade certificates:
```cmd
pip install --upgrade certifi
```

---

### **Disk Space Error**

**Error:**
```
OSError: No space left on device
```

**Solution:**
1. Check available disk space: `dir C:\`
2. Free up space (need 2GB for Rasa and models)
3. Clear pip cache: `pip cache purge`
4. Retry installation

---

## Chatbot Issues

### **Chatbot Doesn't Respond to Question**

**Possible Causes:**

1. **Intent not trained:**
   - Add example to `data/nlu.yml`
   - Add response to `domain.yml`
   - Retrain: `rasa train`

2. **Action not implemented:**
   - Check `actions/actions.py` has the action
   - Action name must match in domain.yml
   - Restart action server

3. **Action server not running:**
   - Start in separate terminal: `rasa run actions`

---

### **Chatbot Always Says "I didn't understand"**

**Cause:** Classifier confidence too low

**Solutions:**

1. Improve NLU data (add more examples)
2. Lower confidence threshold in `config.yml`:
```yaml
- name: FallbackClassifier
  threshold: 0.5  # Reduced from 0.6
```

3. Retrain: `rasa train`

---

### **Custom Actions Return Errors**

**Error Example:**
```
[ERROR] Failed to run action 'action_get_avg_package'
```

**Debugging:**

1. Check action server logs for error message
2. Verify CSV is readable:
```python
python -c "import pandas; df=pd.read_csv('data/company_placement_db.csv'); print(df.head())"
```

3. Check action code:
```cmd
python -c "from actions.actions import ActionGetAvgPackage; print(ActionGetAvgPackage)"
```

4. Restart action server with verbose logging:
```cmd
rasa run actions --debug
```

---

## Validation Tips

### **Validate Before Training**
```cmd
rasa data validate
```
Fixes issues before they cause training failures.

### **Validate Stories**
```cmd
rasa data validate --fail-on-warnings
```
Strict validation shows all potential issues.

### **Test Specific Intent**
```cmd
rasa shell --debug
> hi
> what is google package?
```
The --debug flag shows intent matching confidence scores.

---

## Environment Issues

### **"(venv_rasa)" not showing in prompt**

**Indicates:** Virtual environment not properly activated

**Solution:**
```cmd
del venv_rasa\Scripts\activate.bat  # Sometimes corrupted
python -m venv venv_rasa  # Recreate
venv_rasa\Scripts\activate.bat
```

---

### **Packages installed but not found**

**Indicates:** Wrong Python used

**Debug:**
```cmd
where python          # Check Python path
pip show rasa        # Verify Rasa location
python -m pip show rasa  # Alternative check
```

---

## Getting Help

If issue persists:

1. **Run diagnostics:**
   ```cmd
   python validate_setup.py > validation_report.txt
   ```

2. **Collect logs:**
   ```cmd
   rasa train --debug > train_log.txt 2>&1
   ```

3. **Check Rasa docs:**
   - Issue tracker: https://github.com/RasaHQ/rasa/issues
   - Documentation: https://rasa.com/docs/rasa/troubleshooting

4. **Try from scratch:**
   ```cmd
   rmdir /s /q venv_rasa models __pycache__
   setup_improved.bat
   ```

---

## Quick Fixes (Copy-Paste)

### Reset Everything
```cmd
rmdir /s /q venv_rasa models __pycache__ .rasa
python -m venv venv_rasa
venv_rasa\Scripts\activate.bat
pip install -r requirements.txt
rasa train
rasa shell
```

### Just Retrain
```cmd
venv_rasa\Scripts\activate.bat
rasa train
```

### Just Run
```cmd
venv_rasa\Scripts\activate.bat
rasa run actions  (Term 1)
rasa shell        (Term 2)
```

---

**Last Updated:** February 25, 2026
**Version:** Troubleshooting v1.0
