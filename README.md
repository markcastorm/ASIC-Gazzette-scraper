# ASIC Gazette Scraper

A robust Python web scraper designed to extract historical ASIC (Australian Securities and Investments Commission) Gazette data from the official ASIC website. This tool automatically navigates accordion-style interfaces and handles dynamic table structures to collect comprehensive gazette publication data.

## 🚀 Features

- **Dynamic Table Handling**: Automatically adapts to different table structures (4-column and 5-column layouts)
- **Multi-Link Cell Processing**: Extracts multiple documents/links from single table cells
- **Intelligent Year Detection**: Uses multiple strategies to find and expand year sections
- **Robust Error Handling**: Comprehensive logging and graceful error recovery
- **Flexible Output**: Dynamic CSV generation with columns based on actual data structure
- **Resource Management**: Proper cleanup using context managers
- **Headless Operation**: Runs without GUI for server deployment

## 📋 Requirements

- Python 3.7+
- Chrome/Chromium browser
- ChromeDriver

### Python Dependencies

```bash
pip install selenium
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/asic-gazette-scraper.git
   cd asic-gazette-scraper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install ChromeDriver**
   
   **Option 1: Using webdriver-manager (Recommended)**
   ```bash
   pip install webdriver-manager
   ```
   
   **Option 2: Manual Installation**
   - Download ChromeDriver from [here](https://chromedriver.chromium.org/)
   - Add ChromeDriver to your system PATH

## 🚦 Usage

### Basic Usage

```python
from asic_scraper import ASICGazetteScraper, ScraperConfig

# Create configuration
config = ScraperConfig(
    target_url="https://asic.gov.au/about-asic/corporate-publications/asic-gazette/asic-gazettes-2011-2020/",
    csv_filename="asic_gazettes_2011_2020.csv"
)

# Run scraper
with ASICGazetteScraper(config) as scraper:
    data = scraper.scrape_data()
    scraper.save_to_csv(data)
```

### Command Line Usage

```bash
python asic_scraper.py
```

### Configuration Options

```python
config = ScraperConfig(
    target_url="https://asic.gov.au/path/to/gazettes/",
    csv_filename="output.csv",              # Output CSV filename
    base_url="https://asic.gov.au",         # Base URL for relative links
    headless=True,                          # Run browser in headless mode
    page_load_timeout=30,                   # Page load timeout (seconds)
    element_wait_timeout=10,                # Element wait timeout (seconds)
    delay_between_years=1.0                 # Delay between year processing (seconds)
)
```

## 📊 Output Format

The scraper generates a CSV file with the following structure:

| Column | Description |
|--------|-------------|
| Year | Publication year |
| Date | Publication date |
| ASIC Gazette_title | Title of ASIC Gazette document |
| ASIC Gazette_Url | URL to ASIC Gazette document |
| Business Gazette_title | Title of Business Gazette document |
| Business Gazette_Url | URL to Business Gazette document |
| Other / Notes | Additional notes or other documents |
| Other / Notes_URL | URLs for additional documents |

**Note**: Additional columns are dynamically created when cells contain multiple links (e.g., `ASIC Gazette_1`, `ASIC Gazette_Url_1`, etc.)

### Sample Output

```csv
Year,Date,ASIC Gazette_title,ASIC Gazette_Url,Business Gazette_title,Business Gazette_Url,Other / Notes,Other / Notes_URL
2020,01 Jan 2020,ASIC Gazette 01/20,https://asic.gov.au/...,Business Gazette 01/20,https://asic.gov.au/...,Notice of...,https://asic.gov.au/...
2020,08 Jan 2020,ASIC Gazette 02/20,https://asic.gov.au/...,Business Gazette 02/20,https://asic.gov.au/...,,
```

## 🔧 Advanced Features

### Multi-Strategy Year Detection

The scraper uses multiple approaches to find year sections:

1. **Accordion Buttons**: Detects Bootstrap and custom accordion interfaces
2. **Clickable Elements**: Finds buttons and links with year references
3. **Text-based Detection**: Searches for 4-digit year patterns in text
4. **Fallback Processing**: Processes visible tables when year sections aren't found

### Flexible Table Processing

Handles various table structures:
- **4-column layout**: Date | ASIC Gazette | Business Gazette | Notes
- **5-column layout**: Date | ASIC Gazette | Business Gazette | Other | Notes
- **Mixed layouts**: Automatically detects and adapts to different structures

### Error Recovery

- Graceful handling of missing elements
- Comprehensive logging for debugging
- Automatic retry mechanisms for network issues
- Proper resource cleanup on errors

## 📝 Logging

The scraper provides detailed logging information:

```
2024-01-01 10:00:00 - INFO - Chrome WebDriver initialized successfully
2024-01-01 10:00:01 - INFO - Starting scrape of https://asic.gov.au/...
2024-01-01 10:00:02 - INFO - Found 10 year elements using selector: button[aria-expanded]
2024-01-01 10:00:03 - INFO - Processing year: 2020
2024-01-01 10:00:04 - INFO - Extracted 52 rows for year 2020
2024-01-01 10:00:15 - INFO - Total rows extracted: 520
2024-01-01 10:00:16 - INFO - Data saved to asic_gazettes_2011_2020.csv
```

## 🛡️ Error Handling

The scraper includes comprehensive error handling for:

- **Network timeouts**: Configurable timeout settings
- **Missing elements**: Graceful degradation when elements aren't found
- **Dynamic content**: Multiple strategies for content detection
- **Resource cleanup**: Automatic WebDriver cleanup on exit

## ⚡ Performance Considerations

- **Headless mode**: Faster execution without GUI overhead
- **Smart delays**: Configurable delays between operations
- **Memory efficiency**: Streaming data processing for large datasets
- **Resource management**: Proper cleanup prevents memory leaks

## 🔍 Troubleshooting

### Common Issues

**ChromeDriver not found**
```bash
# Install webdriver-manager
pip install webdriver-manager

# Or download manually and add to PATH
```

**Timeout errors**
```python
# Increase timeout values in configuration
config = ScraperConfig(
    page_load_timeout=60,
    element_wait_timeout=20
)
```

**No data extracted**
```python
# Enable debugging by setting headless=False
config = ScraperConfig(headless=False)
```

### Debug Mode

For troubleshooting, run with visible browser:

```python
config = ScraperConfig(
    target_url="your_url_here",
    headless=False  # Shows browser window
)
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/yourusername/asic-gazette-scraper.git
cd asic-gazette-scraper

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/asic-gazette-scraper/issues) page
2. Create a new issue with detailed information
3. Include log output and error messages

## 🙏 Acknowledgments

- ASIC for providing public access to gazette data
- Selenium WebDriver team for the automation framework
- Python community for excellent libraries and tools

## ⚠️ Disclaimer

This tool is designed for legitimate data collection purposes. Please ensure you comply with ASIC's terms of service and robots.txt when using this scraper. Be respectful of server resources and implement appropriate delays between requests.

---

**Built with ❤️ for the Australian financial data community**
