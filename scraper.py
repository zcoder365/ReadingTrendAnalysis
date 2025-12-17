from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import time
import re

def scrape_goodreads_year(year):
    """
    scrapes the most popular books from a specific year on goodreads
    saves data to a csv file
    
    args:
        year (int): the year to scrape (e.g., 2025)
    """
    
    # url to scrape
    url = f"https://www.goodreads.com/book/popular_by_date/{year}"
    
    # set up the selenium webdriver (using chrome)
    print(f"🚀 starting up chrome for year {year}...")
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
        
        # find all book items by their class
        book_elements = driver.find_elements(By.CSS_SELECTOR, "div.BookListItem__body")
        total_books = len(book_elements)
        print(f"found {total_books} books total! scraping now...\n")
        
        # list to store all book data
        books_data = []
        
        # loop through each book and extract data
        for idx, book in enumerate(book_elements, 1):
            try:
                # extract title
                # the title is in an <a> tag with data-testid="bookTitle"
                title_element = book.find_element(By.CSS_SELECTOR, "a[data-testid='bookTitle']")
                title = title_element.text.strip()
                
                # extract author
                # author is in a span with data-testid="name"
                author_element = book.find_element(By.CSS_SELECTOR, "span[data-testid='name']")
                author = author_element.text.strip()
                
                # extract rating (e.g., "4.21")
                # rating is in a span with class containing "RatingStatistics__rating"
                rating_element = book.find_element(By.CSS_SELECTOR, "span.RatingStatistics__rating")
                rating = rating_element.text.strip()
                
                # extract ratings count and shelvings count
                # they appear together in text like "2m ratings · 3m shelvings"
                # we need to find the div containing this text
                ratings_text_element = book.find_element(By.XPATH, ".//div[@data-testid='ratingsCount']")
                ratings_text = ratings_text_element.text.strip()
                
                # parse out ratings and shelvings using regex
                # format: "2m ratings · 3m shelvings" or "969k ratings · 2m shelvings"
                ratings_match = re.search(r'([\d.]+[kmKM]?)\s+ratings?', ratings_text)
                shelvings_match = re.search(r'([\d.]+[kmKM]?)\s+shelvings?', ratings_text)
                
                ratings_count = ratings_match.group(1) if ratings_match else "N/A"
                shelvings_count = shelvings_match.group(1) if shelvings_match else "N/A"
                
                # store the data
                book_data = {
                    'rank': idx,
                    'title': title,
                    'author': author,
                    'rating': rating,
                    'ratings_count': ratings_count,
                    'shelvings_count': shelvings_count,
                    'year': year
                }
                books_data.append(book_data)
                
                print(f"✅ scraped book #{idx}: {title}")
                
            except Exception as e:
                print(f"❌ error scraping book #{idx}: {e}")
                continue
        
        # save to csv
        csv_filename = f"goodreads_{year}_popular_books.csv"
        print(f"\n💾 saving data to {csv_filename}...")
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # define csv columns
            fieldnames = ['rank', 'title', 'author', 'rating', 'ratings_count', 'shelvings_count', 'year']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # write header
            writer.writeheader()
            
            # write all book data
            for book in books_data:
                writer.writerow(book)
        
        print(f"✨ done! scraped {len(books_data)} books and saved to {csv_filename}")
        return len(books_data)
        
    finally:
        # close the browser
        print("\n🔚 closing browser...")
        driver.quit()

def scrape_multiple_years(start_year, end_year):
    """
    scrapes multiple years of goodreads data
    
    args:
        start_year (int): first year to scrape
        end_year (int): last year to scrape (inclusive)
    """
    print(f"\n🎯 scraping years {start_year} to {end_year}...\n")
    
    total_books = 0
    for year in range(start_year, end_year + 1):
        print(f"\n{'='*60}")
        print(f"📅 starting year {year}")
        print(f"{'='*60}\n")
        
        books_count = scrape_goodreads_year(year)
        total_books += books_count
        
        print(f"\n✅ completed year {year} - {books_count} books scraped")
        print("\n⏳ waiting 5 seconds before next year...\n")
        time.sleep(5)  # be nice to goodreads servers
    
    print(f"\n🎉🎉 all done! scraped {total_books} total books across {end_year - start_year + 1} years!")

if __name__ == "__main__":
    # scrape a single year
    # scrape_goodreads_year(2025)
    
    # OR scrape multiple years (2020-2025)
    scrape_multiple_years(2020, 2025)