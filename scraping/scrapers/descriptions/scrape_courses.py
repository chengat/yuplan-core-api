"""
York University Course Catalog Scraper

This script scrapes course descriptions from the York University course catalog.
It navigates through all subjects, extracts course information, and saves it to a JSON file.
"""

import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class YorkCourseScraper:
    def __init__(self):
        self.base_url = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm"
        self.output_file = "courses_data.json"
        
        # Rate limiting settings (increased to avoid detection)
        self.min_delay = 4  # Minimum delay between requests (seconds)
        self.max_delay = 10  # Maximum delay between requests (seconds)
        self.page_load_delay = 5  # Delay after page loads
        self.subject_switch_delay = 7  # Delay after switching subjects
        
        # Threading settings
        self.max_workers = 2  # Maximum concurrent threads (reduced to avoid detection)
        self.file_lock = threading.Lock()  # Lock for thread-safe file I/O
        
        # Set up Chrome options to avoid bot detection
        self.chrome_options = webdriver.ChromeOptions()
        # Add arguments to appear more like a real user
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        # Uncomment the next line to run headless (without opening browser window)
        # self.chrome_options.add_argument('--headless')
        
        self.driver = None
    
    def setup_driver(self):
        """Initialize the Chrome WebDriver"""
        print("Setting up Chrome WebDriver...")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.maximize_window()
    
    def navigate_to_subject_search(self):
        """Navigate from main page to the subject search page"""
        print(f"Navigating to {self.base_url}...")
        self.driver.get(self.base_url)
        
        # Wait for page to load and click on "Subject" link
        try:
            wait = WebDriverWait(self.driver, 15)
            subject_link = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Subject"))
            )
            subject_link.click()
            print("Clicked on 'Subject' link")
            time.sleep(4)  # Wait for page to load
        except TimeoutException:
            print("Error: Could not find 'Subject' link")
            raise
    
    def get_all_subjects(self):
        """Extract all subjects from the dropdown"""
        try:
            wait = WebDriverWait(self.driver, 15)
            
            # Try different selectors for the subject dropdown
            subject_select = None
            selectors = [
                (By.NAME, "subjectPopUp"),  # Correct name
                (By.ID, "subjectSelect"),  # Correct ID
                (By.NAME, "subjectAreaCode"),
                (By.CSS_SELECTOR, "select[name='subjectPopUp']"),
                (By.XPATH, "//select[@name='subjectPopUp']"),
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    subject_select = wait.until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"Found subject dropdown using: {selector_type}, {selector_value}")
                    break
                except Exception as sel_error:
                    continue
            
            if not subject_select:
                print("Could not find subject dropdown with any selector")
                # Print page source for debugging
                try:
                    print("Page URL:", self.driver.current_url)
                    print("Saving page source to debug.html...")
                    with open('debug.html', 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                except:
                    pass
                return []
            
            select = Select(subject_select)
            subjects = []
            
            # Get all options except the first one (which is usually a placeholder)
            for option in select.options:
                value = option.get_attribute('value')
                text = option.text
                if value and value.strip():  # Skip empty values
                    subjects.append({'value': value, 'text': text})
            
            print(f"Found {len(subjects)} subjects")
            return subjects
        except Exception as e:
            print(f"Error getting subjects: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def random_delay(self, min_delay=None, max_delay=None):
        """Add a random delay to appear more like human behavior and avoid rate limiting"""
        if min_delay is None:
            min_delay = self.min_delay
        if max_delay is None:
            max_delay = self.max_delay
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def is_cloudflare_challenge(self, driver):
        """Detect if we hit a Cloudflare or bot detection page"""
        try:
            page_source = driver.page_source.lower()
            title = driver.title.lower()
            
            # Check for common bot detection indicators
            detection_phrases = [
                'verify you are human',
                'cloudflare',
                'checking your browser',
                'just a moment',
                'please wait',
                'ddos protection',
                'are you a robot'
            ]
            
            for phrase in detection_phrases:
                if phrase in page_source or phrase in title:
                    return True
            
            # Check if current URL is just the domain (redirect to challenge)
            current_url = driver.current_url.lower()
            if current_url == 'https://w2prod.sis.yorku.ca/' or current_url == 'http://w2prod.sis.yorku.ca/':
                return True
                
            return False
        except:
            return False
    
    def append_course_to_json(self, course_data):
        """Append a single course to the JSON file (thread-safe)"""
        with self.file_lock:
            try:
                # Try to read existing data
                try:
                    with open(self.output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    data = []
                
                # Append new course
                data.append(course_data)
                
                # Write updated data
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                print(f"Error appending to JSON: {e}")
    
    def search_by_subject(self, subject_value):
        """Select a subject and click the Search button"""
        try:
            # Select the subject from dropdown
            subject_select = Select(self.driver.find_element(By.NAME, "subjectPopUp"))
            subject_select.select_by_value(subject_value)
            print(f"Selected subject: {subject_value}")
            
            self.random_delay(1, 2)  # Small delay after selection
            
            # Click the Search button - try different selectors
            try:
                # Try finding by value
                search_button = self.driver.find_element(By.CSS_SELECTOR, "input[value='Search Courses']")
                search_button.click()
            except:
                # Try finding by name
                search_button = self.driver.find_element(By.NAME, "searchCourses")
                search_button.click()
            
            print("Clicked 'Search Courses' button")
            
            # Longer delay after search to let page load
            self.random_delay(self.subject_switch_delay, self.subject_switch_delay + 3)
            return True
        except Exception as e:
            print(f"Error searching for subject {subject_value}: {e}")
            return False
    
    def scrape_course_links(self):
        """Extract all course detail links from the search results page"""
        try:
            # Find all links with "Course Schedule" text
            course_links = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(text(), 'Course Schedule')]"
            )
            
            # Extract href attributes
            links = []
            for link in course_links:
                href = link.get_attribute('href')
                if href:
                    links.append(href)
            
            print(f"Found {len(links)} course links")
            return links
        except Exception as e:
            print(f"Error extracting course links: {e}")
            return []
    
    def scrape_course_details(self, course_url):
        """Navigate to a course detail page and scrape the description"""
        try:
            self.driver.get(course_url)
            self.random_delay(self.page_load_delay, self.page_load_delay + 2)
            
            # Get course ID from the h1 heading
            course_id = ""
            try:
                # Look for the red h1 heading
                heading = self.driver.find_element(
                    By.XPATH, 
                    "//h1[contains(@style, 'CC0000') or contains(@style, 'cc0000')]"
                )
                course_id = heading.text.strip()
            except NoSuchElementException:
                # Fallback: try any h1
                try:
                    heading = self.driver.find_element(By.TAG_NAME, "h1")
                    course_id = heading.text.strip()
                except:
                    course_id = "Unknown"
            
            # Get course description
            description = ""
            try:
                # The description is typically in a <p> tag after the heading
                # Look for paragraphs that contain substantial text
                paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
                
                for p in paragraphs:
                    text = p.text.strip()
                    # Look for substantial paragraphs (likely descriptions)
                    if len(text) > 100 and not text.startswith("Note:") and "Language of Instruction" not in text:
                        description = text
                        break
                
                # If no description found, try to get all paragraph text
                if not description:
                    for p in paragraphs:
                        text = p.text.strip()
                        if len(text) > 50:
                            description = text
                            break
                
                if not description:
                    description = "Description not found"
                    
            except Exception as e:
                description = f"Error extracting description: {e}"
            
            course_data = {
                "course_id": course_id,
                "description": description,
                "url": course_url
            }
            
            print(f"Scraped: {course_id[:50] if len(course_id) > 50 else course_id}")
            # Save immediately to avoid data loss
            self.append_course_to_json(course_data)
            return course_data
            
        except Exception as e:
            print(f"Error scraping course details from {course_url}: {e}")
            return None

    
    def scrape_subject(self, subject, retry_count=3):
        """Scrape all courses for a single subject (runs in a thread)"""
        driver = None
        for attempt in range(retry_count):
            try:
                # Create a new driver instance for this thread
                driver = webdriver.Chrome(options=self.chrome_options)
                driver.set_page_load_timeout(30)
                driver.maximize_window()
                
                subject_value = subject['value']
                subject_text = subject['text']
                
                # Navigate to subject search page
                driver.get(self.base_url)
                self.random_delay(2, 3)
                
                wait = WebDriverWait(driver, 15)
                subject_link = wait.until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Subject"))
                )
                subject_link.click()
                self.random_delay(2, 3)
                
                # Select this subject
                subject_select = Select(driver.find_element(By.NAME, "subjectPopUp"))
                subject_select.select_by_value(subject_value)
                self.random_delay(1, 2)
                
                # Click Search
                try:
                    search_button = driver.find_element(By.CSS_SELECTOR, "input[value='Search Courses']")
                    search_button.click()
                except:
                    search_button = driver.find_element(By.NAME, "searchCourses")
                    search_button.click()
                
                self.random_delay(self.subject_switch_delay, self.subject_switch_delay + 2)
                
                # Get all course links
                course_links = driver.find_elements(
                    By.XPATH, 
                    "//a[contains(text(), 'Course Schedule')]"
                )
                
                links = [link.get_attribute('href') for link in course_links if link.get_attribute('href')]
                print(f"[{subject_text}] Found {len(links)} course links")
                
                # Scrape each course
                for link_idx, link in enumerate(links, 1):
                    try:
                        driver.get(link)
                        self.random_delay(self.page_load_delay, self.page_load_delay + 2)
                        
                        # Check if we hit a Cloudflare challenge
                        if self.is_cloudflare_challenge(driver):
                            print(f"[{subject_text}] Cloudflare challenge detected, skipping course {link_idx}")
                            continue
                        
                        # Get course ID
                        course_id = ""
                        try:
                            heading = driver.find_element(
                                By.XPATH, 
                                "//h1[contains(@style, 'CC0000') or contains(@style, 'cc0000')]"
                            )
                            course_id = heading.text.strip()
                        except NoSuchElementException:
                            try:
                                heading = driver.find_element(By.TAG_NAME, "h1")
                                course_id = heading.text.strip()
                            except:
                                course_id = "Unknown"
                        
                        # Get description
                        description = ""
                        try:
                            paragraphs = driver.find_elements(By.TAG_NAME, "p")
                            
                            for p in paragraphs:
                                text = p.text.strip()
                                if len(text) > 100 and not text.startswith("Note:") and "Language of Instruction" not in text:
                                    description = text
                                    break
                            
                            if not description:
                                for p in paragraphs:
                                    text = p.text.strip()
                                    if len(text) > 50:
                                        description = text
                                        break
                            
                            if not description:
                                description = "Description not found"
                                
                        except Exception as e:
                            description = f"Error extracting description: {e}"
                        
                        # Validate data before saving - skip if it's a challenge page
                        if ('verify you are human' in description.lower() or 
                            'cloudflare' in course_id.lower() or 
                            'w2prod.sis.yorku.ca' == course_id.lower().strip() or
                            course_id == "Unknown"):
                            print(f"[{subject_text}] Skipping invalid/challenge page ({link_idx}/{len(links)})")
                            continue
                        
                        course_data = {
                            "course_id": course_id,
                            "description": description,
                            "url": link
                        }
                        
                        # Save immediately
                        self.append_course_to_json(course_data)
                        print(f"[{subject_text}] Scraped ({link_idx}/{len(links)}): {course_id[:40]}...")
                        
                    except Exception as e:
                        print(f"[{subject_text}] Error scraping course: {e}")
                
                # Success - break out of retry loop
                break
                    
            except Exception as e:
                print(f"[{subject['text']}] Attempt {attempt + 1}/{retry_count} failed: {e}")
                if attempt < retry_count - 1:
                    print(f"[{subject['text']}] Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"[{subject['text']}] Failed after {retry_count} attempts")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
    
    def run(self):
        """Main execution method using multithreading"""
        try:
            # Use the main driver just to get subjects
            self.setup_driver()
            
            # Navigate to subject search page
            self.navigate_to_subject_search()
            
            # Get all available subjects
            subjects = self.get_all_subjects()
            
            if not subjects:
                print("No subjects found. Exiting.")
                return
            
            print(f"\nFound {len(subjects)} subjects to process")
            print(f"Using {self.max_workers} concurrent threads\n")
            
            # Close the main driver - each thread will create its own
            self.driver.quit()
            self.driver = None
            
            # Use ThreadPoolExecutor to handle multiple subjects concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self.scrape_subject, subject) for subject in subjects]
                
                # Wait for all tasks to complete and handle any exceptions
                completed = 0
                for idx, future in enumerate(futures, 1):
                    try:
                        future.result()
                        completed += 1
                    except Exception as e:
                        print(f"Error in thread for subject {idx}: {e}")
            
            print(f"\n{'='*60}")
            print(f"Scraping complete! Processed {completed}/{len(subjects)} subjects")
            
            # Count final results
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    final_data = json.load(f)
                print(f"Total courses saved: {len(final_data)}")
            except:
                pass
            
            print(f"Data saved to {self.output_file}")
            print(f"{'='*60}\n")
            
        except KeyboardInterrupt:
            print("\n\nScraping interrupted by user.")
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    partial_data = json.load(f)
                print(f"Saved {len(partial_data)} courses before interruption")
            except:
                pass
        except Exception as e:
            print(f"\nAn error occurred: {e}")
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    print("York University Course Catalog Scraper")
    print("=" * 60)
    print("Starting scraper...")
    print("This may take a while depending on the number of courses.\n")
    
    scraper = YorkCourseScraper()
    scraper.run()
    
    print("\nScraping complete!")
