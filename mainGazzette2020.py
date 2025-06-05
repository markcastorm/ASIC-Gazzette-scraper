import csv
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ScraperConfig:
    """Configuration for the ASIC Gazette scraper"""
    target_url: str
    csv_filename: str = "asic_gazettes.csv"
    base_url: str = "https://asic.gov.au"
    headless: bool = True
    page_load_timeout: int = 30
    element_wait_timeout: int = 10
    delay_between_years: float = 1.0

class ASICGazetteScraper:
    """Scraper for ASIC Gazette data with dynamic column structure"""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.driver = None
        self.all_data = []
        self.max_links = {
            'ASIC Gazette': 1,
            'Business Gazette': 1,
            'Other / Notes': 1
        }
        
    def __enter__(self):
        self._setup_driver()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()
        
    def _setup_driver(self):
        """Initialize the Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            if self.config.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.config.page_load_timeout)
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
            
    def _cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
            
    def _resolve_url(self, url: str) -> str:
        """Convert relative URLs to absolute URLs"""
        if not url:
            return ""
        if url.startswith('http'):
            return url
        return urljoin(self.config.base_url, url)
        
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        # Replace non-breaking spaces and clean whitespace
        cleaned = text.replace('\u00a0', ' ').replace('&nbsp;', ' ')
        return ' '.join(cleaned.split()).strip()
        
    def _extract_cell_content(self, cell) -> Tuple[str, List[str]]:
        """Extract both text content and link URLs from a cell"""
        try:
            # Get all text content from the cell
            full_text = self._clean_text(cell.text)
            
            # Extract all links
            links = cell.find_elements(By.TAG_NAME, "a")
            urls = []
            
            for link in links:
                url = link.get_attribute("href")
                if url:
                    resolved_url = self._resolve_url(url.strip())
                    urls.append(resolved_url)
            
            return full_text, urls
            
        except Exception as e:
            logger.warning(f"Error extracting cell content: {e}")
            return "", []
            
    def _extract_multiple_links_data(self, cell) -> Tuple[List[str], List[str]]:
        """Extract titles and URLs from a cell that may contain multiple links"""
        try:
            links = cell.find_elements(By.TAG_NAME, "a")
            
            if not links:
                return [], []
            
            titles = []
            urls = []
            
            for link in links:
                title = self._clean_text(link.text)
                url = link.get_attribute("href")
                
                if title:
                    titles.append(title)
                if url:
                    resolved_url = self._resolve_url(url.strip())
                    urls.append(resolved_url)
            
            return titles, urls
            
        except Exception as e:
            logger.warning(f"Error extracting multiple links data: {e}")
            return [], []
            
    def _extract_row_data(self, row, year: str) -> Optional[Dict]:
        """Extract data from a single table row - handles both 4 and 5 column layouts"""
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            
            if len(cells) < 4:
                logger.warning(f"Row has fewer than 4 cells ({len(cells)}), skipping")
                return None
            
            # Extract date (column 1)
            date = self._clean_text(cells[0].text)
            
            # Initialize result dictionary
            result = {
                'Year': year,
                'Date': date
            }
            
            # Extract ASIC Gazette data (column 2)
            asic_text, asic_urls = self._extract_cell_content(cells[1])
            asic_titles, asic_link_urls = self._extract_multiple_links_data(cells[1])
            
            # If no links but has text, use text as title
            if not asic_titles and asic_text:
                asic_titles = [asic_text]
                asic_link_urls = [""]
            elif not asic_titles:
                asic_titles = [""]
                asic_link_urls = [""]
            
            # Store ASIC data
            for i, (title, url) in enumerate(zip(asic_titles, asic_link_urls)):
                if i == 0:
                    result['ASIC Gazette_title'] = title
                    result['ASIC Gazette_Url'] = url
                else:
                    result[f'ASIC Gazette_{i}'] = title
                    result[f'ASIC Gazette_Url_{i}'] = url
            
            # Update max links tracking
            self.max_links['ASIC Gazette'] = max(self.max_links['ASIC Gazette'], len(asic_titles))
            
            # Extract Business Gazette data (column 3)
            business_text, business_urls = self._extract_cell_content(cells[2])
            business_titles, business_link_urls = self._extract_multiple_links_data(cells[2])
            
            # If no links but has text, use text as title
            if not business_titles and business_text:
                business_titles = [business_text]
                business_link_urls = [""]
            elif not business_titles:
                business_titles = [""]
                business_link_urls = [""]
            
            # Store Business data
            for i, (title, url) in enumerate(zip(business_titles, business_link_urls)):
                if i == 0:
                    result['Business Gazette_title'] = title
                    result['Business Gazette_Url'] = url
                else:
                    result[f'Business Gazette_{i}'] = title
                    result[f'Business Gazette_Url_{i}'] = url
            
            # Update max links tracking
            self.max_links['Business Gazette'] = max(self.max_links['Business Gazette'], len(business_titles))
            
            # Handle different column layouts for Other/Notes
            other_notes_texts = []
            other_notes_urls = []
            
            if len(cells) == 4:
                # 4-column layout: Date, ASIC Gazette, Business Gazette, Notes
                notes_text, notes_urls = self._extract_cell_content(cells[3])
                notes_titles, notes_link_urls = self._extract_multiple_links_data(cells[3])
                
                # Use full text content for notes
                if notes_text:
                    other_notes_texts.append(notes_text)
                    other_notes_urls.extend(notes_link_urls if notes_link_urls else [""])
                
            elif len(cells) >= 5:
                # 5-column layout: Date, ASIC Gazette, Business Gazette, Other, Notes
                other_text, other_urls = self._extract_cell_content(cells[3])
                other_titles, other_link_urls = self._extract_multiple_links_data(cells[3])
                
                notes_text, notes_urls = self._extract_cell_content(cells[4])
                notes_titles, notes_link_urls = self._extract_multiple_links_data(cells[4])
                
                # Combine Other and Notes content
                combined_texts = []
                combined_urls = []
                
                if other_text:
                    combined_texts.append(other_text)
                if notes_text:
                    combined_texts.append(notes_text)
                
                combined_urls.extend(other_link_urls if other_link_urls else [])
                combined_urls.extend(notes_link_urls if notes_link_urls else [])
                
                if combined_texts:
                    # Join texts with ". " if multiple
                    full_combined_text = ". ".join(combined_texts)
                    other_notes_texts.append(full_combined_text)
                    other_notes_urls = combined_urls
            
            # Store Other/Notes data
            if other_notes_texts:
                for i, text in enumerate(other_notes_texts):
                    if i == 0:
                        result['Other / Notes'] = text
                        result['Other / Notes_URL'] = other_notes_urls[i] if i < len(other_notes_urls) else ""
                    else:
                        result[f'Other / Notes_{i}'] = text
                        result[f'Other / Notes_URL_{i}'] = other_notes_urls[i] if i < len(other_notes_urls) else ""
                
                # Add remaining URLs if more URLs than texts
                for i in range(len(other_notes_texts), len(other_notes_urls)):
                    result[f'Other / Notes_URL_{i}'] = other_notes_urls[i]
            else:
                result['Other / Notes'] = ""
                result['Other / Notes_URL'] = ""
            
            # Update max links tracking
            max_other_items = max(len(other_notes_texts), len(other_notes_urls))
            self.max_links['Other / Notes'] = max(self.max_links['Other / Notes'], max_other_items)
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting row data: {e}")
            return None
            
    def _extract_table_data(self, table, year: str) -> List[Dict]:
        """Extract data from a single table - handles different table structures"""
        try:
            data_rows = []
            
            # Find tbody and all data rows
            try:
                tbody = table.find_element(By.TAG_NAME, "tbody")
                rows = tbody.find_elements(By.TAG_NAME, "tr")
            except NoSuchElementException:
                # Some tables might not have tbody, try direct tr elements
                rows = table.find_elements(By.TAG_NAME, "tr")
                # Filter out header rows (those with th elements)
                rows = [row for row in rows if not row.find_elements(By.TAG_NAME, "th")]
            
            for row in rows:
                row_data = self._extract_row_data(row, year)
                if row_data:
                    data_rows.append(row_data)
            
            return data_rows
            
        except Exception as e:
            logger.error(f"Error extracting table data for year {year}: {e}")
            return []
            
    def _extract_year_data(self, year_element, year: str) -> List[Dict]:
        """Extract data from a single year section"""
        try:
            logger.info(f"Processing year: {year}")
            
            # Find the table associated with this year element
            table = None
            
            # Strategy 1: Look for table in the same parent container
            try:
                parent = year_element.find_element(By.XPATH, "./..")
                table = parent.find_element(By.TAG_NAME, "table")
            except:
                pass
            
            # Strategy 2: Look for table as next sibling
            if not table:
                try:
                    current_element = year_element
                    for _ in range(5):  # Check next 5 siblings
                        current_element = self.driver.execute_script(
                            "return arguments[0].nextElementSibling;", current_element
                        )
                        if current_element and current_element.tag_name == 'table':
                            table = current_element
                            break
                except:
                    pass
            
            # Strategy 3: Look for table in expanded content area
            if not table:
                try:
                    # Look for common accordion content selectors
                    content_selectors = [
                        "[id*='collapse']",
                        "[class*='collapse']", 
                        "[class*='accordion-content']",
                        "[class*='content']"
                    ]
                    
                    for selector in content_selectors:
                        try:
                            content_area = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if content_area.is_displayed():
                                table = content_area.find_element(By.TAG_NAME, "table")
                                break
                        except:
                            continue
                except:
                    pass
            
            # Strategy 4: Look for any visible table on the page after clicking
            if not table:
                try:
                    all_tables = self.driver.find_elements(By.TAG_NAME, "table")
                    for t in all_tables:
                        if t.is_displayed():
                            table = t
                            break
                except:
                    pass
                    
            if not table:
                logger.warning(f"No table found for year {year}")
                return []
                
            # Extract data from the table
            table_data = self._extract_table_data(table, year)
            logger.info(f"Extracted {len(table_data)} rows for year {year}")
            
            return table_data
            
        except Exception as e:
            logger.error(f"Error extracting data for year {year}: {e}")
            return []
            
    def _generate_csv_headers(self) -> List[str]:
        """Generate CSV headers based on maximum number of links found"""
        headers = ['Year', 'Date']
        
        # Add ASIC Gazette columns
        headers.extend(['ASIC Gazette_title', 'ASIC Gazette_Url'])
        for i in range(1, self.max_links['ASIC Gazette']):
            headers.extend([f'ASIC Gazette_{i}', f'ASIC Gazette_Url_{i}'])
            
        # Add Business Gazette columns
        headers.extend(['Business Gazette_title', 'Business Gazette_Url'])
        for i in range(1, self.max_links['Business Gazette']):
            headers.extend([f'Business Gazette_{i}', f'Business Gazette_Url_{i}'])
            
        # Add Other/Notes columns
        headers.extend(['Other / Notes', 'Other / Notes_URL'])
        for i in range(1, self.max_links['Other / Notes']):
            headers.extend([f'Other / Notes_{i}', f'Other / Notes_URL_{i}'])
            
        return headers
        
    def _normalize_row_data(self, row_data: Dict, headers: List[str]) -> Dict:
        """Ensure row data has all required columns"""
        normalized = {}
        for header in headers:
            normalized[header] = row_data.get(header, "")
        return normalized
        
    def scrape_data(self) -> List[Dict]:
        """Main scraping method"""
        try:
            logger.info(f"Starting scrape of {self.config.target_url}")
            
            # Load the page
            self.driver.get(self.config.target_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.config.element_wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for accordion sections or year headers that might be clickable
            # Try multiple approaches to find year sections
            year_elements = []
            
            # Approach 1: Look for clickable year headers (buttons, links, etc.)
            selectors_to_try = [
                "button[aria-expanded]",  # Accordion buttons
                ".accordion-button",      # Bootstrap accordion
                ".year-header",          # Custom year headers
                "h2 button",             # Buttons inside h2
                "h3 button",             # Buttons inside h3
                "[data-bs-toggle='collapse']",  # Bootstrap collapse
                "[data-toggle='collapse']",     # Bootstrap 4 collapse
                "a[href*='#']",          # Links that might expand sections
            ]
            
            for selector in selectors_to_try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = self._clean_text(elem.text)
                    # Check if text contains a 4-digit year
                    if any(year_str in text for year_str in ['2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011']):
                        year_elements.append(elem)
                        
                if year_elements:
                    logger.info(f"Found {len(year_elements)} year elements using selector: {selector}")
                    break
            
            # Approach 2: If no clickable elements found, look for any elements with year text
            if not year_elements:
                logger.info("No clickable year elements found, looking for year text...")
                all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
                for elem in all_elements:
                    text = self._clean_text(elem.text)
                    if text.isdigit() and len(text) == 4 and 2011 <= int(text) <= 2025:
                        year_elements.append(elem)
                        
                logger.info(f"Found {len(year_elements)} elements with year text")
            
            # Approach 3: Look for specific patterns in the page source
            if not year_elements:
                logger.info("Trying to find accordion structure in page source...")
                page_source = self.driver.page_source
                
                # Look for common accordion patterns
                if 'accordion' in page_source.lower():
                    # Try to find accordion containers
                    accordion_containers = self.driver.find_elements(By.CSS_SELECTOR, "[class*='accordion']")
                    for container in accordion_containers:
                        # Look for year elements within accordion containers
                        year_buttons = container.find_elements(By.XPATH, ".//*[contains(text(), '20')]")
                        year_elements.extend(year_buttons)
                        
                logger.info(f"Found {len(year_elements)} elements in accordion containers")
            
            if not year_elements:
                logger.warning("No year elements found. Dumping page structure for debugging...")
                # Log some page structure for debugging
                body = self.driver.find_element(By.TAG_NAME, "body")
                logger.info(f"Page title: {self.driver.title}")
                logger.info(f"Body classes: {body.get_attribute('class')}")
                
                # Try to find any tables anyway
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                logger.info(f"Found {len(tables)} tables on page")
                
                if tables:
                    logger.info("Processing tables without year association...")
                    for i, table in enumerate(tables[:3]):  # Process first 3 tables as test
                        try:
                            table_data = self._extract_table_data(table, f"Table_{i}")
                            self.all_data.extend(table_data)
                        except Exception as e:
                            logger.error(f"Error processing table {i}: {e}")
                
                return self.all_data
            
            # Process each year element
            for i, year_elem in enumerate(year_elements):
                try:
                    year_text = self._clean_text(year_elem.text)
                    logger.info(f"Processing year element {i}: '{year_text}'")
                    
                    # Try to click/expand the year section
                    try:
                        # Check if element is clickable and not already expanded
                        is_expanded = year_elem.get_attribute("aria-expanded")
                        if is_expanded == "false":
                            logger.info(f"Expanding year section: {year_text}")
                            self.driver.execute_script("arguments[0].click();", year_elem)
                            time.sleep(2)  # Wait for expansion
                    except Exception as e:
                        logger.warning(f"Could not click year element: {e}")
                    
                    # Extract year from text
                    year = "Unknown"
                    for potential_year in ['2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011']:
                        if potential_year in year_text:
                            year = potential_year
                            break
                    
                    # Look for associated table
                    year_data = self._extract_year_data(year_elem, year)
                    self.all_data.extend(year_data)
                    
                    # Add delay between years
                    if i < len(year_elements) - 1:
                        time.sleep(self.config.delay_between_years)
                        
                except Exception as e:
                    logger.error(f"Error processing year element {i}: {e}")
                    continue
                    
            logger.info(f"Total rows extracted: {len(self.all_data)}")
            logger.info(f"Max links found - ASIC: {self.max_links['ASIC Gazette']}, Business: {self.max_links['Business Gazette']}, Other: {self.max_links['Other / Notes']}")
            
            return self.all_data
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise
            
    def save_to_csv(self, data: List[Dict]):
        """Save scraped data to CSV file with dynamic headers"""
        try:
            if not data:
                logger.warning("No data to save")
                return
                
            # Generate headers based on maximum links found
            headers = self._generate_csv_headers()
            
            # Normalize all row data to have consistent columns
            normalized_data = [self._normalize_row_data(row, headers) for row in data]
            
            with open(self.config.csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(normalized_data)
                
            logger.info(f"Data saved to {self.config.csv_filename}")
            logger.info(f"CSV contains {len(headers)} columns and {len(normalized_data)} rows")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            raise

def main():
    """Main execution function"""
    # Configuration for the scraper
    config = ScraperConfig(
        target_url="https://asic.gov.au/about-asic/corporate-publications/asic-gazette/asic-gazettes-2011-2020/",
        csv_filename="asic_gazettes_2011_2020.csv",
        base_url="https://asic.gov.au",
        headless=True,
        page_load_timeout=30,
        element_wait_timeout=10,
        delay_between_years=1.0
    )
    
    try:
        # Use context manager for proper cleanup
        with ASICGazetteScraper(config) as scraper:
            # Scrape the data
            data = scraper.scrape_data()
            
            # Save to CSV
            scraper.save_to_csv(data)
            
        logger.info("Scraping completed successfully!")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()