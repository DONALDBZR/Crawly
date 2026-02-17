# Crawly

**A focused web scraping service for corporate data extraction workflows.**

Extract, normalize, and export data from web sources using pluggable strategies. Built with Python, BeautifulSoup4, and MySQL support.

---

## 🚀 Quick Start

**Install and run in 30 seconds:**

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Test with a real site
python3 main.py --url https://onlinesearch.mns.mu/ --dry-run

# 3. Run actual scrape
python3 main.py --url https://onlinesearch.mns.mu/ --output-format pretty
```

**First scrape successful?** Continue to [Basic Usage](#basic-usage).

**Having issues?** Jump to [Troubleshooting](#troubleshooting).

---

## ✨ Key Features

**Core Capabilities:**
- 🔌 **Pluggable strategies** - Strategy Pattern for different data sources
- 🔄 **Full scraping pipeline** - Fetch → Extract → Normalize
- 🌐 **HTML scraping** - BeautifulSoup4 with custom CSS selectors
- 🔁 **Smart retries** - Exponential backoff for failed requests
- 🗄️ **MySQL integration** - Connection pooling (programmatic API only)
- 🛡️ **SQL injection prevention** - Input sanitization built-in
- ✅ **Startup validation** - Environment variables validated before execution
- 📊 **Multiple outputs** - JSON, pretty JSON, CSV
- 📝 **Structured logging** - Debug, info, warn, error levels

---

## 📋 Prerequisites

**Required:**
- Python 3.7+
- pip

**Optional:**
- MySQL database (for programmatic API with DB features)

---

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/DONALDBZR/Crawly
cd Crawly

# Install dependencies
pip3 install -r requirements.txt

# Verify installation
python3 main.py --help
```

**Executable script:**
```bash
chmod +x main.py  # If needed
./main.py --help
```

---

## ⚙️ Configuration

### CLI Configuration (Main Usage)

**No configuration file needed.** The CLI is self-contained.

Control everything with command-line flags:

| Flag | Purpose | Default |
|------|---------|---------|
| `--url` | Target URL (required) | - |
| `--timeout` | Request timeout (seconds) | 10 |
| `--max-attempts` | Retry attempts | 3 |
| `--log-level` | DEBUG, INFO, WARN, ERROR | INFO |
| `--output` | File path or `-` for stdout | stdout |
| `--output-format` | json, pretty, csv | json |
| `--headers` | Custom HTTP headers (JSON) | - |
| `--selectors` | Custom CSS selectors (JSON) | - |

See full list: `python3 main.py --help`

### Database Configuration (Optional)

**Only needed for programmatic API with database features.**

The CLI does not use database features.

Create `.env` file:

```bash
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
DB_POOL_NAME=crawly_pool
DB_POOL_SIZE=5
```

⚠️ **Note:** `.env.example` contains variables for planned features (proxies, rate limiting) not yet implemented. Only `DB_*` and `LOG_*` variables work currently.

---

## 🔐 Environment Variables

### Overview

Crawly validates environment variables at startup before any side effects occur. **CLI mode** requires only logger configuration (with safe defaults). **Programmatic API with database features** requires database credentials.

### Required Variables (Database API Only)

These variables are **required only when using database features** (programmatic API). The CLI does not need them.

| Variable | Format | Description | Example |
|----------|--------|-------------|---------|
| `DB_HOST` | String (hostname/IP) | Database server address | `localhost`, `192.168.1.100` |
| `DB_USER` | String | Database username | `crawly_user` |
| `DB_PASSWORD` | String | Database password | `secure_password` |
| `DB_NAME` | String | Database name | `crawly_db` |

### Optional Variables

These variables have safe defaults and are not required.

#### Database Pool Configuration

| Variable | Format | Default | Description |
|----------|--------|---------|-------------|
| `DB_POOL_NAME` | String | `crawly_pool` | Connection pool identifier |
| `DB_POOL_SIZE` | Integer (≥1) | `5` | Number of connections in pool |
| `DB_POOL_RESET_SESSION` | Boolean | `true` | Reset session on pool return |
| `DB_USE_PURE` | Boolean | `true` | Use pure Python MySQL driver |

**Boolean values:** `true`/`false`, `1`/`0`, `yes`/`no` (case-insensitive)

#### Logger Configuration

| Variable | Format | Default | Description |
|----------|--------|---------|-------------|
| `LOG_DIRECTORY` | String (path) | `./Logs` | Directory for log files |
| `LOG_FILE_NAME` | String (filename) | `Crawly.log` | Log file name |

### Local Development Setup

**1. Create `.env` file for CLI-only usage:**

```bash
# Optional: Override default log location
LOG_DIRECTORY=./logs
LOG_FILE_NAME=development.log
```

**2. Create `.env` file for programmatic API with database:**

```bash
# Required database credentials
DB_HOST=localhost
DB_USER=crawly_dev
DB_PASSWORD=dev_password
DB_NAME=crawly_development

# Optional: Pool configuration
DB_POOL_SIZE=3
DB_POOL_RESET_SESSION=true

# Optional: Custom logging
LOG_DIRECTORY=./logs
LOG_FILE_NAME=crawly_dev.log
```

**3. Load custom `.env` file:**

```bash
# CLI: Use --config flag
python3 main.py --url https://example.com --config .env.production

# Programmatic API: Load before validation
from dotenv import load_dotenv
load_dotenv('.env.production')
```

### Startup Validation

Crawly validates all environment variables at startup **before** initializing logging, database connections, or scraping operations. This ensures fast failure with clear error messages.

**Validation workflow:**
```
1. Load .env file (if present)
2. ✅ Validate environment variables
3. Initialize logger
4. Execute scraping/database operations
```

If validation fails, the application **exits immediately** with:
- **Exit Code:** `1` (validation error)
- **Error Output:** Precise diagnostic messages

### Common Configuration Errors

#### ❌ Empty Required Variable

```bash
DB_HOST=
```

**Error:**
```
❌ Configuration Error: DB_HOST cannot be empty
```

**Fix:** Provide a non-empty value:
```bash
DB_HOST=localhost
```

---

#### ❌ Invalid Integer Format

```bash
DB_POOL_SIZE=not_a_number
```

**Error:**
```
❌ Configuration Error: DB_POOL_SIZE must be an integer, got: 'not_a_number'
```

**Fix:** Use a valid integer:
```bash
DB_POOL_SIZE=5
```

---

#### ❌ Integer Below Minimum

```bash
DB_POOL_SIZE=0
```

**Error:**
```
❌ Configuration Error: DB_POOL_SIZE must be >= 1, got: 0
```

**Fix:** Use a positive value:
```bash
DB_POOL_SIZE=5
```

---

#### ❌ Invalid Boolean Format

```bash
DB_USE_PURE=maybe
```

**Error:**
```
❌ Configuration Error: DB_USE_PURE must be 'true' or 'false' (or '1'/'0'), got: 'maybe'
```

**Fix:** Use a valid boolean:
```bash
DB_USE_PURE=true
```

---

#### ❌ Missing Database Credentials (API Only)

**Error:**
```
❌ Configuration Error: Missing required environment variable: DB_HOST
❌ Configuration Error: Missing required environment variable: DB_USER
❌ Configuration Error: Missing required environment variable: DB_PASSWORD
❌ Configuration Error: Missing required environment variable: DB_NAME
```

**Fix:** Create `.env` with all required variables:
```bash
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
```

**Note:** The CLI does **not** require database credentials. Only programmatic API usage with database features needs them.

### Programmatic Validation

For programmatic API usage, call validation explicitly:

```python
from Models.EnvValidator import Environment_Validator
import sys

# Validate with database required
result = Environment_Validator.validate_environment(require_database=True)

if not result.success:
    for error in result.errors:
        print(f"❌ Configuration Error: {error}", file=sys.stderr)
    sys.exit(1)

# Warnings indicate default values used
for warning in result.warnings:
    print(f"⚠️  {warning}")

# Proceed with validated configuration
print(f"✅ Configuration valid")
```

---

## 💻 Usage

### Basic Usage

**1. Simple scrape to stdout:**
```bash
python3 main.py --url https://onlinesearch.mns.mu/
```

**2. Save to file with formatting:**
```bash
python3 main.py --url https://onlinesearch.mns.mu/ \
  --output scraped.json \
  --output-format pretty
```

**3. Dry-run (validate without scraping):**
```bash
python3 main.py --url https://onlinesearch.mns.mu/ --dry-run
```

**4. Using executable:**
```bash
./main.py --url https://onlinesearch.mns.mu/
```

### Real-World Examples

**Scrape with custom User-Agent:**
```bash
python3 main.py \
  --url https://onlinesearch.mns.mu/ \
  --headers '{"User-Agent": "Mozilla/5.0 (compatible; Crawly/1.0)"}' \
  --log-level DEBUG
```

**Target specific elements:**
```bash
python3 main.py \
  --url https://onlinesearch.mns.mu/ \
  --selectors '{"title": "h1", "content": "div p"}' \
  --output-format pretty
```

**Handle slow/unreliable sites:**
```bash
python3 main.py \
  --url https://onlinesearch.mns.mu/ \
  --timeout 30 \
  --max-attempts 5 \
  --strategy mns
```

**Export to CSV:**
```bash
python3 main.py \
  --url https://onlinesearch.mns.mu/ \
  --output-format csv \
  --output data.csv \
  --quiet
```

**Production scraping:**
```bash
python3 main.py \
  --url https://onlinesearch.mns.mu/ \
  --timeout 20 \
  --max-attempts 3 \
  --headers '{"User-Agent": "YourCompany Crawler (contact@example.com)"}' \
  --output results.json \
  --output-format json \
  --log-level INFO
```

### CLI Reference

**Required:**
- `--url URL, -u` - Target URL to scrape

**Common Options:**
- `--strategy STRATEGY, -s` - Strategy to use: `mns`, `mns_html` (default: mns)
- `--output PATH, -o` - Output file or `-` for stdout (default: stdout)
- `--output-format FMT, -f` - Format: `json`, `pretty`, `csv` (default: json)
- `--log-level LEVEL, -l` - Log level (default: INFO)
- `--timeout SEC, -t` - HTTP timeout in seconds (default: 10)
- `--max-attempts NUM, -m` - Max retries (default: 3)
- `--dry-run, -n` - Validate config without scraping
- `--quiet, -q` - Suppress non-error output

**Advanced:**
- `--headers JSON, -H` - Custom HTTP headers as JSON string
- `--selectors JSON, -S` - Custom CSS selectors as JSON string
- `--config PATH, -c` - Path to .env file (default: .env)
- `--version, -v` - Show version

### Programmatic API

**Embedding Crawly in your Python app:**

```python
from Models.ScraperOrchestrator import Scraper_Orchestrator
from Models.Logger import Crawly_Logger
from Models.LoggerConfigurator import Logger_Configurator
from Strategies.MnsHtmlScraperStrategy import Mns_Html_Scraper_Strategy

# Setup logging
logger = Crawly_Logger("my_app", Logger_Configurator())

# Create strategy
strategy = Mns_Html_Scraper_Strategy()

# Create orchestrator with retries
orchestrator = Scraper_Orchestrator(
    strategy=strategy,
    logger=logger,
    max_attempts=3,
    backoff_base_seconds=0.5
)

# Execute
context = {
    "url": "https://onlinesearch.mns.mu",
    "timeout": 10,
    "headers": {"User-Agent": "MyApp/1.0"}
}

result = orchestrator.run(context)
print(result)
```

**Database features** (`Database_Handler`, `Database_Connection_Pool`, `Table_Model`) require `.env` with database credentials.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation error (bad arguments) |
| 2 | Runtime error (network, parsing) |
| 3 | Internal error (unexpected exception) |

---

## 🧪 Testing

**Run all tests:**
```bash
python3 -m unittest discover tests
```

**Run specific tests:**
```bash
# CLI functionality
python3 -m unittest tests.test_cli

# Environment variable validation
python3 -m unittest tests.test_env_validator
python3 -m unittest tests.test_cli_startup_validation

# Scraping orchestration
python3 -m unittest tests.test_scraper_orchestrator

# HTML strategy
python3 -m unittest tests.test_mns_html_scraper_strategy

# Database handling
python3 -m unittest tests.test_database_handler

# Input sanitization
python3 -m unittest tests.test_data_sanitizer
```

**Check syntax:**
```bash
python3 -m compileall Models/
```

**Verbose output:**
```bash
python3 -m unittest discover tests -v
```

**Test coverage:**
- ✅ CLI argument parsing and validation
- ✅ Environment variable validation (startup)
- ✅ Orchestrator retry logic and backoff
- ✅ HTML scraping and extraction
- ✅ Database operations and pooling
- ✅ SQL injection prevention
- ✅ Exception handling

---

## 🔧 Troubleshooting

### Common Issues

**❌ `Command 'python' not found`**

Use `python3` instead:
```bash
python3 main.py --help
```

**❌ `ModuleNotFoundError: No module named 'bs4'`**

Install dependencies:
```bash
pip3 install -r requirements.txt
```

**❌ `No module named crawly` (when using `python3 -m crawly`)**

This command doesn't work. Use `python3 main.py` instead:
```bash
python3 main.py --url https://onlinesearch.mns.mu
```

**❌ Scraping fails with timeout**

Increase timeout and retries:
```bash
python3 main.py --url https://onlinesearch.mns.mu \
  --timeout 30 \
  --max-attempts 5
```

**❌ Empty or incorrect extraction**

Enable debug logging to see what's happening:
```bash
python3 main.py --url https://onlinesearch.mns.mu \
  --log-level DEBUG
```

Try custom selectors:
```bash
python3 main.py --url https://onlinesearch.mns.mu \
  --selectors '{"title": "h1.main-title", "content": "article.post"}' \
  --log-level DEBUG
```

**❌ `ValueError: The configuration is invalid for that database server`**

Database credentials missing or invalid. If not using database features, ignore this - **CLI doesn't need database**.

For programmatic API with database features:
1. Ensure all required variables are set (see [Environment Variables](#-environment-variables))
2. Check for typos in variable names
3. Verify no empty values

```bash
# Required in .env file
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_db
```

For detailed validation errors, see the [Common Configuration Errors](#common-configuration-errors) section.

**❌ Permission denied: `./main.py`**

Make script executable:
```bash
chmod +x main.py
./main.py --help
```

### Getting Help

**Check logs:**
```bash
# Logs written to Logs/crawly.log
tail -f Logs/crawly.log
```

**Enable debug output:**
```bash
python3 main.py --url https://onlinesearch.mns.mu \
  --log-level DEBUG \
  --output debug_output.json
```

**Test with dry-run:**
```bash
python3 main.py --url https://onlinesearch.mns.mu --dry-run
```

**Verify installation:**
```bash
# Check Python version
python3 --version  # Should be 3.7+

# Check dependencies
pip3 list | grep -E 'beautifulsoup4|mysql-connector|python-dotenv'

# Run syntax check
python3 -m compileall Models/
```

---

## 📁 Project Structure

```
Crawly/
├── main.py                         # CLI entrypoint
├── cli.py                          # CLI implementation (580 lines)
├── requirements.txt                # Dependencies: beautifulsoup4, mysql-connector-python, python-dotenv
│
├── Models/                         # Core business logic
│   ├── ScraperOrchestrator.py     # Orchestrates fetch-extract-normalize pipeline
│   ├── ScraperStrategy.py         # Abstract strategy interface
│   ├── EnvValidator.py            # Startup environment variable validation
│   ├── DatabaseHandler.py         # Database operations with connection pooling
│   ├── DatabaseConnectionPool.py  # MySQL connection pool manager
│   ├── DatabaseHandlerFactory.py  # Factory for creating database handlers
│   ├── DatabaseConfigurator.py    # Loads DB config from environment
│   ├── DataSanitizer.py           # SQL injection prevention
│   ├── Sanitizer.py               # Sanitizer interface
│   ├── TableModel.py              # Dynamic ORM-like table models
│   ├── Logger.py                  # Logging facade
│   └── LoggerConfigurator.py      # Logger setup
│
├── Strategies/                     # Scraping strategy implementations
│   ├── __init__.py                # Strategy registry: {name: class}
│   └── MnsHtmlScraperStrategy.py  # HTML scraping with BeautifulSoup4
│
├── Errors/
│   └── Scraper.py                 # Custom exception with traceback
│
├── tests/                          # Unit tests (12 test modules)
│   ├── test_cli.py
│   ├── test_env_validator.py
│   ├── test_cli_startup_validation.py
│   ├── test_scraper_orchestrator.py
│   ├── test_mns_html_scraper_strategy.py
│   └── ...
│
└── Logs/                           # Log output directory
    └── crawly.log                 # Application logs
```

### Architecture

**Design patterns:**
- **Strategy Pattern** - Pluggable scraping strategies for different sources
- **Factory Pattern** - Database handler creation with shared connection pools
- **Dependency Injection** - Constructor injection for logger, sanitizer, pools

**SOLID principles:**
- Single Responsibility - Each class has one purpose
- Interface Segregation - Abstract base classes define clear contracts
- Dependency Inversion - Depend on abstractions, not implementations

---

## 🔌 Creating Custom Strategies

**1. Implement the strategy interface:**

```python
from Models.ScraperStrategy import Scraper_Strategy
from typing import Dict, Any

class My_Custom_Strategy(Scraper_Strategy):
    def identifier(self) -> str:
        return "my_custom"
    
    def fetch(self, context: Dict[str, Any]) -> str:
        """Fetch raw content from source."""
        url = context["url"]
        # Your fetching logic here
        return raw_content
    
    def extract(self, raw: str) -> Dict[str, Any]:
        """Extract structured data from raw content."""
        # Your extraction logic here
        return {"field1": "value1", "field2": "value2"}
    
    def normalize(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize to standard schema."""
        return {
            "entity_type": "my_type",
            "entity_id": extracted.get("id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": extracted
        }
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if fetch should retry."""
        return attempt < 3 and isinstance(exception, TransientError)
```

**2. Register your strategy:**

```python
# In Strategies/__init__.py
from Strategies.MyCustomStrategy import My_Custom_Strategy

STRATEGY_REGISTRY = {
    "mns": Mns_Html_Scraper_Strategy,
    "mns_html": Mns_Html_Scraper_Strategy,
    "custom": My_Custom_Strategy,  # Add here
}
```

**3. Use it:**

```bash
python3 main.py --url https://onlinesearch.mns.mu --strategy custom
```

---

## ⚠️ Known Limitations

**Current status:**

| Feature | Status |
|---------|--------|
| HTML scraping | ✅ Implemented (MNS strategy) |
| Proxy support | ❌ Planned (see `.env.example`) |
| Rate limiting | ❌ Planned |
| Content caching | ❌ Planned |
| OAuth authentication | ❌ Planned |
| Concurrent scraping | ❌ Single-threaded only |
| CLI env variables | ❌ Use command-line args instead |

**Important notes:**
- `.env.example` includes variables for **planned features not yet implemented**
- Currently, only `DB_*` variables are functional (for programmatic DB API)
- CLI does not read scraping parameters from `.env` - use flags instead

---

## 🤝 Contributing

**Before contributing:**

1. **Code style:**
   - Use underscored class names: `Database_Handler`, `Scraper_Strategy`
   - Add detailed docstrings with procedural steps
   - Use type hints for all function signatures

2. **Architecture:**
   - Follow SOLID principles
   - Use dependency injection - no hardwired dependencies
   - Maintain backward compatibility unless required

3. **Security:**
   - Never log secrets (passwords, tokens, credentials)
   - Use parameterized queries for all database operations
   - Validate all user input through sanitizer

**Testing changes:**

```bash
# Verify syntax
python3 -m compileall Models/

# Run tests
python3 -m unittest discover tests

# Check specific module
python3 -m unittest tests.test_your_module
```

**Pull requests:**
- Include tests for new functionality
- Update documentation for new features
- Check `.env.example` if adding environment variables

---

## 📄 License

**CeCILL Free Software License v2.1**

French free software license compatible with GNU GPL.

**Key provisions:**
- ✅ Use, modify, and redistribute freely
- ✅ GPL-compatible for mixed projects
- ⚖️ Governed by French law
- ⚠️ Limited liability and warranty

See [LICENSE](LICENSE) for complete terms.

---

## 📌 Project Info

**Version:** 0.1.0

**Author:** Darkness4869

**Dependencies:**
- `beautifulsoup4==4.12.3` - HTML parsing
- `mysql-connector-python==9.5.0` - MySQL connectivity
- `python-dotenv==1.0.0` - Environment variables

**Status:** Active development

**Support:**
- 🧪 `tests/` - Usage examples in test files

---

**Note:** Crawly is an extraction and normalization service only. It does not provide storage, analytics, reporting, or orchestration. Send scraped data to downstream services for persistent storage and analysis.
