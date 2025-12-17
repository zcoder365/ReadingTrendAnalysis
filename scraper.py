# goodreads_scraper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import time

def scrape_goodreads_2025():
    """
    scrapes the most popular books from 2025 on goodreads
    saves data to a csv file
    """
    
    # url to scrape
    url = "https://www.goodreads.com/book/popular_by_date/2025"
    
    # set up the selenium webdriver (using chrome)
    print("🚀 starting up chrome...")
    driver = webdriver.Chrome()
    
    try:
        # load the page
        print(f"📖 loading {url}...")
        driver.get(url)
        time.sleep(3)  # wait for initial page load
        
        # click "show more books" until it's gone
        click_count = 0
        while True:
            try:
                # find the "show more books" button
                show_more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show more books')]"))
                )
                
                # scroll to the button and click it
                driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
                time.sleep(1)
                show_more_button.click()
                click_count += 1
                print(f"✅ clicked 'show more books' (click #{click_count})")
                time.sleep(2)  # wait for new books to load
                
            except (TimeoutException, NoSuchElementException):
                # button not found - we've loaded all books!
                print(f"🎉 button disappeared - all books loaded!")
                break
        
        # now scrape all the books
        print("\n📊 counting books...")
        book_elements = driver.find_elements(By.CSS_SELECTOR, "div[itemtype='http://schema.org/Book']")
        total_books = len(book_elements)
        print(f"found {total_books} books total! scraping now...\n")
        
        # list to store all book data
        books_data = []
        
        # loop through each book and extract data
        for idx, book in enumerate(book_elements, 1):
            try:
                # extract title
                title_element = book.find_element(By.CSS_SELECTOR, "h3[data-testid='bookTitle']")
                title = title_element.text.strip()
                
                # extract author
                author_element = book.find_element(By.CSS_SELECTOR, "span[data-testid='name']")
                author = author_element.text.strip()
                
                # extract rating (e.g., "4.21")
                rating_element = book.find_element(By.CSS_SELECTOR, "span[class*='RatingStatistics__rating']")
                rating = rating_element.text.strip()
                
                # extract number of ratings (e.g., "2m ratings")
                ratings_count_element = book.find_element(By.XPATH, ".//span[contains(text(), 'ratings')]")
                ratings_count = ratings_count_element.text.strip()
                
                # extract number of shelvings (e.g., "3m shelvings")
                shelvings_count_element = book.find_element(By.XPATH, ".//span[contains(text(), 'shelvings')]")
                shelvings_count = shelvings_count_element.text.strip()
                
                # store the data
                book_data = {
                    'rank': idx,
                    'title': title,
                    'author': author,
                    'rating': rating,
                    'ratings_count': ratings_count,
                    'shelvings_count': shelvings_count
                }
                books_data.append(book_data)
                
                print(f"✅ scraped book #{idx}: {title}")
                
            except Exception as e:
                print(f"❌ error scraping book #{idx}: {e}")
                continue
        
        # save to csv
        csv_filename = "goodreads_2025_popular_books.csv"
        print(f"\n💾 saving data to {csv_filename}...")
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # define csv columns
            fieldnames = ['rank', 'title', 'author', 'rating', 'ratings_count', 'shelvings_count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # write header
            writer.writeheader()
            
            # write all book data
            for book in books_data:
                writer.writerow(book)
        
        print(f"✨ done! scraped {len(books_data)} books and saved to {csv_filename}")
        
    finally:
        # close the browser
        print("\n🔚 closing browser...")
        driver.quit()

if __name__ == "__main__":
    scrape_goodreads_2025()