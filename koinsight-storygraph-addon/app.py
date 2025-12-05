"""
StoryGraph Sync Service
Syncs reading progress from KoInsight to StoryGraph
"""

from flask import Flask, request, jsonify
import sqlite3
import os
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
STORYGRAPH_EMAIL = os.environ.get('STORYGRAPH_EMAIL')
STORYGRAPH_PASSWORD = os.environ.get('STORYGRAPH_PASSWORD')
KOINSIGHT_DB_PATH = os.environ.get('KOINSIGHT_DB_PATH', '/app/data/koinsight.db')

class StoryGraphSyncer:
    """Handles syncing reading progress to StoryGraph"""
    
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        
    def init_driver(self):
        """Initialize headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome driver initialized")
        
    def login(self):
        """Login to StoryGraph"""
        try:
            logger.info("Logging into StoryGraph...")
            self.driver.get('https://app.thestorygraph.com/users/sign_in')
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            
            # Find and fill email
            email_field = wait.until(
                EC.presence_of_element_located((By.ID, 'user_email'))
            )
            email_field.send_keys(self.email)
            
            # Find and fill password
            password_field = self.driver.find_element(By.ID, 'user_password')
            password_field.send_keys(self.password)
            
            # Submit form
            submit_button = self.driver.find_element(By.NAME, 'commit')
            submit_button.click()
            
            # Wait for redirect after login
            time.sleep(3)
            
            logger.info("Successfully logged in")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
            
    def search_book(self, title, author):
        """Search for a book on StoryGraph"""
        try:
            logger.info(f"Searching for: {title} by {author}")
            
            # Navigate to search
            self.driver.get('https://app.thestorygraph.com/browse')
            
            wait = WebDriverWait(self.driver, 10)
            
            # Find search box
            search_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"]'))
            )
            search_box.clear()
            search_box.send_keys(f"{title} {author}")
            search_box.submit()
            
            time.sleep(2)
            
            # Try to find the first result
            first_result = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.book-title-link'))
            )
            book_url = first_result.get_attribute('href')
            
            logger.info(f"Found book: {book_url}")
            return book_url
            
        except Exception as e:
            logger.error(f"Book search failed: {str(e)}")
            return None
            
    def update_progress(self, book_url, progress_percent, current_page, total_pages):
        """Update reading progress for a book"""
        try:
            logger.info(f"Updating progress to {progress_percent}%")
            
            self.driver.get(book_url)
            wait = WebDriverWait(self.driver, 10)
            
            # Look for "Update Progress" or "Add to TBR" button
            # This will vary based on whether book is already tracked
            try:
                # Try to find update progress button
                update_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Update')]"))
                )
                update_button.click()
                time.sleep(1)
                
            except TimeoutException:
                # Maybe need to add to currently reading first
                add_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Want to Read')]")
                add_button.click()
                time.sleep(1)
                
                # Set to Currently Reading
                currently_reading = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Currently Reading')]")
                currently_reading.click()
                time.sleep(1)
            
            # Enter page number
            page_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]'))
            )
            page_input.clear()
            page_input.send_keys(str(current_page))
            
            # Submit
            submit = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit.click()
            
            time.sleep(2)
            logger.info("Progress updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update progress: {str(e)}")
            return False
            
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")


def get_reading_progress_from_koinsight():
    """Query KoInsight database for current reading progress"""
    try:
        # Connect to KoInsight SQLite database
        conn = sqlite3.connect(KOINSIGHT_DB_PATH)
        cursor = conn.cursor()
        
        # Query for books currently being read
        # Note: You'll need to adjust this query based on actual KoInsight schema
        query = """
        SELECT 
            title,
            authors,
            pages,
            last_page,
            CAST(last_page AS FLOAT) / CAST(pages AS FLOAT) * 100 as progress_percent,
            last_open
        FROM books
        WHERE status = 'reading' OR last_open > datetime('now', '-7 days')
        ORDER BY last_open DESC
        """
        
        cursor.execute(query)
        books = cursor.fetchall()
        
        conn.close()
        
        # Format results
        reading_list = []
        for book in books:
            reading_list.append({
                'title': book[0],
                'authors': book[1],
                'total_pages': book[2],
                'current_page': book[3],
                'progress_percent': round(book[4], 1),
                'last_open': book[5]
            })
            
        logger.info(f"Found {len(reading_list)} books in progress")
        return reading_list
        
    except Exception as e:
        logger.error(f"Failed to query KoInsight database: {str(e)}")
        return []


@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'StoryGraph Sync',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/sync', methods=['POST'])
def sync():
    """
    Main sync endpoint
    Can be triggered manually or by Cloud Scheduler
    """
    try:
        logger.info("Starting sync process...")
        
        # Check configuration
        if not STORYGRAPH_EMAIL or not STORYGRAPH_PASSWORD:
            return jsonify({
                'error': 'StoryGraph credentials not configured'
            }), 500
        
        # Get books from KoInsight
        books = get_reading_progress_from_koinsight()
        
        if not books:
            return jsonify({
                'message': 'No books to sync',
                'synced': 0
            })
        
        # Initialize syncer
        syncer = StoryGraphSyncer(STORYGRAPH_EMAIL, STORYGRAPH_PASSWORD)
        syncer.init_driver()
        
        # Login
        if not syncer.login():
            syncer.close()
            return jsonify({'error': 'Failed to login to StoryGraph'}), 500
        
        # Sync each book
        results = []
        for book in books:
            try:
                # Search for book
                book_url = syncer.search_book(book['title'], book['authors'])
                
                if book_url:
                    # Update progress
                    success = syncer.update_progress(
                        book_url,
                        book['progress_percent'],
                        book['current_page'],
                        book['total_pages']
                    )
                    
                    results.append({
                        'title': book['title'],
                        'status': 'success' if success else 'failed',
                        'progress': book['progress_percent']
                    })
                else:
                    results.append({
                        'title': book['title'],
                        'status': 'not_found'
                    })
                    
            except Exception as e:
                logger.error(f"Error syncing {book['title']}: {str(e)}")
                results.append({
                    'title': book['title'],
                    'status': 'error',
                    'error': str(e)
                })
        
        # Cleanup
        syncer.close()
        
        return jsonify({
            'message': 'Sync complete',
            'synced': len([r for r in results if r['status'] == 'success']),
            'total': len(books),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/manual-sync', methods=['POST'])
def manual_sync():
    """
    Manual sync endpoint that accepts book data directly from Kindle
    For when you want to bypass KoInsight
    """
    try:
        data = request.json
        
        if not data or 'books' not in data:
            return jsonify({'error': 'No book data provided'}), 400
        
        logger.info(f"Manual sync requested for {len(data['books'])} books")
        
        # Initialize syncer
        syncer = StoryGraphSyncer(STORYGRAPH_EMAIL, STORYGRAPH_PASSWORD)
        syncer.init_driver()
        
        if not syncer.login():
            syncer.close()
            return jsonify({'error': 'Failed to login'}), 500
        
        results = []
        for book in data['books']:
            book_url = syncer.search_book(book['title'], book['author'])
            
            if book_url:
                success = syncer.update_progress(
                    book_url,
                    book['progress'],
                    book['current_page'],
                    book['total_pages']
                )
                results.append({
                    'title': book['title'],
                    'status': 'success' if success else 'failed'
                })
            else:
                results.append({
                    'title': book['title'],
                    'status': 'not_found'
                })
        
        syncer.close()
        
        return jsonify({
            'message': 'Manual sync complete',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Manual sync failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
