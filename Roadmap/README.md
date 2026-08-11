# LeetCode Company-wise Interview Questions Analyzer

A simple system to analyze LeetCode interview questions for different companies and time ranges, built without ML, LLM, APIs, or web scraping.

## 🏗️ Architecture

```
User Query → On-Demand Git Clone → Local CSV Loader → CSV Filter & Aggregator → Response Formatter → Auto Cleanup
```

## 🚀 Key Features

- **On-Demand Cloning**: Repository cloned only when needed
- **Auto Cleanup**: Temporary files deleted after each query
- **667+ Companies**: Comprehensive coverage of top tech companies
- **5 Time Ranges**: 30 days, 3 months, 6 months, >6 months, all time
- **Multiple Output Formats**: JSON, chatbot-friendly text, CSV export
- **Zero Storage**: No permanent local storage required
- **Fast Processing**: Local CSV loading during query

## 📦 Installation

```bash
# Install dependencies
pip install pandas

# Git must be installed for repository cloning
# (comes pre-installed on most systems)
```

## 🎯 Usage

### Command Line Interface

```bash
# List all available companies
python main.py --list-companies

# Analyze Amazon for last 30 days (chatbot format)
python main.py --company amazon --time-range 30_days --format chatbot

# Analyze Google for 3 months (JSON format)
python main.py --company google --time-range 3_months

# Export Microsoft questions to CSV
python main.py --company microsoft --time-range 6_months --export

# Keep temporary files for debugging
python main.py --company amazon --time-range 30_days --no-cleanup
```

## 📊 Sample Output

### Query Process
```
📥 Cloning LeetCode repository...
✅ Repository cloned to: /tmp/leetcode_xyz123/leetcode-companywise-interview-questions
Analyzing amazon for 30 Days...

amazon - Last 30 Days

Total Questions: 71

Difficulty Breakdown:
- Medium: 41
- Easy: 20
- Hard: 10

Questions:
1. Two Sum (Easy)
2. Longest Substring Without Repeating Characters (Medium)
3. Best Time to Buy and Sell Stock (Easy)
... and 68 more questions

🧹 Cleaning up temporary files...
✅ Cleanup complete
```

## 🔧 How It Works

### 1. **On-Demand Cloning**
- Creates temporary directory using `tempfile.mkdtemp()`
- Clones repository using `git clone`
- Repository stored in temp location only

### 2. **Context Manager Pattern**
```python
with LeetCodeAnalyzer(cleanup_after=True) as analyzer:
    result = analyzer.analyze_company("amazon", "30_days")
    # Auto cleanup happens here
```

### 3. **Automatic Cleanup**
- Removes temporary directory after query completion
- No leftover files on local machine
- Optional `--no-cleanup` flag for debugging

### 4. **Data Processing**
- Loads CSV from temporary location
- Processes data with pandas
- Formats output as requested
- Exports CSV if requested (saved permanently)

## 📋 Time Ranges

| Value | Label |
|-------|-------|
| `30_days` | Last 30 Days |
| `3_months` | Last 3 Months |
| `6_months` | Last 6 Months |
| `more_than_6_months` | More Than 6 Months |
| `all_time` | All Time |

## 🎨 Integration Examples

### Python SDK Usage
```python
from leetcode_analyzer import LeetCodeAnalyzer

# Auto cleanup
with LeetCodeAnalyzer() as analyzer:
    result = analyzer.analyze_company("amazon", "30_days")
    print(result["total_questions"])  # 71

# Keep files for debugging
with LeetCodeAnalyzer(cleanup_after=False) as analyzer:
    companies = analyzer.get_available_companies()
    print(len(companies))  # 667
```

### Chatbot Integration
```python
with LeetCodeAnalyzer() as analyzer:
    result = analyzer.analyze_company("google", "3_months")
    response = analyzer.format_for_chatbot(result)
    print(response)  # Formatted chatbot response
```

## 🚀 Performance

- **Clone Time**: ~10-30 seconds (one-time per query)
- **Processing Time**: ~50ms after clone
- **Memory Usage**: Temporary during query only
- **Disk Usage**: Zero permanent storage
- **Network**: Only for git clone operation

## 📝 Command Line Options

| Option | Description |
|--------|-------------|
| `--list-companies` | List all available companies |
| `--company` | Company name (required for analysis) |
| `--time-range` | Time range for analysis |
| `--format` | Output format: json, chatbot |
| `--export` | Export results to CSV file |
| `--output` | Custom output file path |
| `--no-cleanup` | Keep temporary files for debugging |

## 📝 Data Source

All data sourced from: https://github.com/snehasishroy/leetcode-companywise-interview-questions

No scraping, no APIs, no ML - just clean, on-demand local data processing with automatic cleanup.
