"""
LeetCode Web Scraper using Selenium
Fetches all submission data from a user's LeetCode profile
"""

import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from typing import List, Dict
import time


class LeetCodeScraper:
    """
    Web scraper for fetching LeetCode submissions using Selenium.
    
    This scraper:
    1. Logs into LeetCode with provided credentials
    2. Opens the LeetCode progress/submissions page
    3. Scrolls to load all submissions
    4. Extracts submission data (title, difficulty, date)
    """
    
    def __init__(self):
        """Initialize the scraper with Chrome options"""
        self.driver = None
        self.options = webdriver.ChromeOptions()
        # Uncomment the line below to run in headless mode (no visible browser)
        # self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    async def fetch_submissions(self, username: str, email: str = None, password: str = None) -> List[Dict]:
        """
        Fetch all LeetCode submissions for a given user.
        
        Args:
            username: LeetCode username (displayed on profile)
            email: LeetCode account email (for login)
            password: LeetCode account password (for login)
            
        Returns:
            List of submission dictionaries with title, slug, difficulty, and date
        """
        print(f"📥 Starting LeetCode scraper for user: {username}")
        
        try:
            # Setup Chrome driver
            print("   Setting up Chrome driver...")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options
            )
            
            # Login to LeetCode if credentials provided
            if email and password:
                print("   Logging in to LeetCode...")
                await self._login(email, password)
                print("   ✓ Login successful")
            else:
                print("   ⚠️  No credentials provided - will attempt to fetch public data")
            
            # Navigate to LeetCode progress page (submissions/solved problems)
            url = "https://leetcode.com/progress/"
            print(f"   Opening: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            print("   Waiting for page to load...")
            time.sleep(5)
            
            # Check page content
            page_source = self.driver.page_source.lower()
            if "login" in page_source and "password" in page_source:
                print("⚠️  Still on login page - login may have failed")
                raise Exception("Authentication failed. Please check your credentials.")
            
            # Wait for submissions table to load
            print("   Waiting for submissions table...")
            wait = WebDriverWait(self.driver, 15)
            
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr")))
            except:
                print("   ⚠️  Table didn't load with expected selector, proceeding anyway...")
            
            # Give extra time for content to render
            time.sleep(2)
            
            # Scroll to load all submissions
            print("   Scrolling to load all submissions...")
            submissions = await self._scroll_and_collect_submissions()
            
            print(f"✅ Scraped {len(submissions)} submissions")
            return submissions
            
        except Exception as e:
            print(f"❌ Scraping error: {str(e)}")
            raise
        finally:
            if self.driver:
                print("   Closing browser...")
                self.driver.quit()
    
    async def _login(self, email: str, password: str):
        """
        Login to LeetCode using provided credentials.
        
        Args:
            email: LeetCode account email
            password: LeetCode account password
        """
        try:
            # Navigate to login page
            login_url = "https://leetcode.com/accounts/login/"
            print(f"   Navigating to login page...")
            self.driver.get(login_url)
            
            # Wait for login form to load
            time.sleep(3)
            
            # Enter email
            print(f"   Entering email...")
            try:
                email_input = self.driver.find_element(By.NAME, "login")
            except:
                # Alternative selectors
                email_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='email'], input[placeholder*='Email'], input[type='text']")
            
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(1)
            
            # Enter password
            print(f"   Entering password...")
            try:
                password_input = self.driver.find_element(By.NAME, "password")
            except:
                # Alternative selector
                password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(1)
            
            # Click sign in button - try multiple strategies
            print(f"   Clicking sign in...")
            sign_in_button = None
            
            # Strategy 1: Look for button by text
            try:
                sign_in_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Sign In')]")
                print("      → Found button by text (XPath)")
            except:
                print("      → Strategy 1 failed")
            
            # Strategy 2: Look for button by role and text
            if not sign_in_button:
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    print(f"      → Found {len(buttons)} buttons on page")
                    for btn in buttons:
                        btn_text = btn.text.lower()
                        print(f"         Button text: '{btn_text}'")
                        if "sign" in btn_text and "in" in btn_text:
                            sign_in_button = btn
                            print(f"      → Found 'Sign in' button")
                            break
                except Exception as e:
                    print(f"      → Strategy 2 failed: {e}")
            
            # Strategy 3: Find submit button
            if not sign_in_button:
                try:
                    sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    print("      → Found submit button")
                except:
                    print("      → Strategy 3 failed")
            
            # Strategy 4: Look for any button near the password field
            if not sign_in_button:
                try:
                    sign_in_button = self.driver.find_element(By.XPATH, "//button[1]")
                    print("      → Found first button on page")
                except:
                    print("      → Strategy 4 failed")
            
            if sign_in_button:
                sign_in_button.click()
                print("   ✓ Sign in button clicked")
            else:
                raise Exception("Could not find sign-in button")
            
            # Wait for login to complete and redirect
            print(f"   Waiting for authentication...")
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "login" in current_url.lower() or "accounts" in current_url.lower():
                # Try alternative buttons or check for errors
                page_source = self.driver.page_source.lower()
                if "invalid" in page_source or "incorrect" in page_source or "error" in page_source:
                    raise Exception("Invalid credentials - login failed")
                print("   ⚠️  Still on auth page, but proceeding...")
            else:
                print(f"   ✓ Successfully authenticated")
            
        except Exception as e:
            print(f"   ❌ Login failed: {str(e)}")
            raise Exception(f"Login failed: {str(e)}")
    
    async def _scroll_and_collect_submissions(self) -> List[Dict]:
        """
        Scroll through the submissions page and collect all submission data.
        
        Returns:
            List of submission dictionaries
        """
        submissions = []
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 100  # Increased max scrolls to get all submissions
        
        while scroll_count < max_scrolls:
            # Scroll down
            print(f"   Scroll {scroll_count + 1}/{max_scrolls}...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(1.5)
            
            # Get new height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Extract submissions using multiple selector strategies
            submission_items = self._extract_all_submissions()
            print(f"   Found {len(submission_items)} submissions on page")
            
            # Store unique submissions
            for submission in submission_items:
                if submission and submission not in submissions:
                    submissions.append(submission)
            
            # Check if we've reached the bottom
            if new_height == last_height:
                print(f"   Reached end of submissions")
                break
            
            last_height = new_height
            scroll_count += 1
            await asyncio.sleep(0.5)  # Async sleep
        
        # Remove duplicates based on titleSlug
        unique_submissions = []
        seen_slugs = set()
        for sub in submissions:
            slug = sub.get("titleSlug")
            if slug and slug not in seen_slugs:
                seen_slugs.add(slug)
                unique_submissions.append(sub)
        
        print(f"   Deduplicated to {len(unique_submissions)} unique problems")
        return unique_submissions
    
    def _extract_all_submissions(self) -> List[Dict]:
        """
        Extract all submission rows from the current page view.
        Uses multiple strategies to find submissions.
        """
        submissions = []
        
        # Strategy 1: Look for table rows containing submission data
        try:
            # Find all rows in the submission table
            rows = self.driver.find_elements(By.CSS_SELECTOR, "tr")
            
            for row in rows:
                try:
                    # Skip header rows
                    if row.find_elements(By.TAG_NAME, "th"):
                        continue
                    
                    # Extract problem link
                    links = row.find_elements(By.CSS_SELECTOR, "a[href*='/problems/']")
                    if not links:
                        continue
                    
                    link = links[0]
                    title = link.text.strip()
                    href = link.get_attribute("href")
                    
                    if not title or not href:
                        continue
                    
                    # Extract slug from URL
                    slug = href.split("/problems/")[1].rstrip("/") if "/problems/" in href else None
                    if not slug:
                        continue
                    
                    # Extract difficulty (look for colored text or badge)
                    difficulty = self._extract_difficulty_from_row(row)
                    
                    # Extract date
                    date_text = self._extract_date_from_row(row)
                    timestamp = self._parse_date(date_text)
                    
                    submission = {
                        "title": title,
                        "titleSlug": slug,
                        "difficulty": difficulty,
                        "timestamp": timestamp,
                        "platform": "leetcode"
                    }
                    
                    submissions.append(submission)
                    
                except Exception as e:
                    # Skip problematic rows
                    continue
        except Exception as e:
            print(f"   ⚠️  Error extracting submissions: {str(e)}")
        
        return submissions
    
    def _extract_difficulty_from_row(self, row) -> str:
        """
        Extract difficulty from a row element.
        Looks for colored difficulty badges (Easy, Medium, Hard).
        """
        try:
            # Look for elements containing difficulty text
            cells = row.find_elements(By.TAG_NAME, "td")
            
            for cell in cells:
                text = cell.text.strip()
                if text in ["Easy", "Medium", "Hard"]:
                    return text
                # Check for abbreviated form
                if text in ["Med", "Med."]:
                    return "Medium"
            
            # Fallback: look for any span with difficulty
            spans = row.find_elements(By.TAG_NAME, "span")
            for span in spans:
                text = span.text.strip()
                if text in ["Easy", "Medium", "Hard", "Med", "Med."]:
                    return "Medium" if text in ["Med", "Med."] else text
            
            return "Unknown"
        except:
            return "Unknown"
    
    def _extract_date_from_row(self, row) -> str:
        """
        Extract submission date from a row element.
        """
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            
            if cells:
                # First cell usually contains the date
                date_text = cells[0].text.strip()
                if date_text and not any(char.isalpha() for char in date_text[:3]):
                    # Looks like a date
                    return date_text
                
                # Check other cells
                for cell in cells:
                    text = cell.text.strip()
                    if any(month in text for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                        return text
                    if any(day in text for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
                        return text
            
            return "Unknown"
        except:
            return "Unknown"
    
    def _parse_date(self, date_text: str) -> int:
        """
        Parse LeetCode date format to Unix timestamp.
        
        Handles formats like:
        - "1 minute ago"
        - "2 hours ago"
        - "3 days ago"
        - "Jan 1, 2024"
        - "1/1/2024"
        """
        now = datetime.now()
        
        # Handle relative times
        if "minute" in date_text:
            minutes = int(date_text.split()[0])
            timestamp = int((now.timestamp() - (minutes * 60)))
        elif "hour" in date_text:
            hours = int(date_text.split()[0])
            timestamp = int((now.timestamp() - (hours * 3600)))
        elif "day" in date_text:
            days = int(date_text.split()[0])
            timestamp = int((now.timestamp() - (days * 86400)))
        elif "week" in date_text:
            weeks = int(date_text.split()[0])
            timestamp = int((now.timestamp() - (weeks * 604800)))
        elif "month" in date_text:
            months = int(date_text.split()[0])
            timestamp = int((now.timestamp() - (months * 2592000)))
        else:
            # Try to parse absolute date
            try:
                parsed_date = datetime.strptime(date_text, "%b %d, %Y")
                timestamp = int(parsed_date.timestamp())
            except:
                try:
                    parsed_date = datetime.strptime(date_text, "%m/%d/%Y")
                    timestamp = int(parsed_date.timestamp())
                except:
                    # Default to now if parsing fails
                    timestamp = int(now.timestamp())
        
        return timestamp


# Global instance
leetcode_scraper = LeetCodeScraper()
