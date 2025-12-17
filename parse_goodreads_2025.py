from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import csv
import time
import re

def scrape_goodreads_2025():
    """
    scrapes the most popular books from 2025 on goodreads
    uses selenium to load the page, then parses with beautifulsoup
    saves data to a csv file
    """
    
    url = "https://www.goodreads.com/book/popular_by_date/2025"
    
    # set up chrome options to look like a real browser
    print("🚀 setting up chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # remove headless if you want to see the browser
    # options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    
    # make selenium less detectable
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        print(f"📖 loading {url}...")
        driver.get(url)
        
        # wait longer for the page to fully load
        print("⏳ waiting for content to load...")
        time.sleep(8)  # give javascript time to render everything
        
        # scroll down to trigger any lazy loading
        print("📜 scrolling to load more content...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # click "show more books" button until it's gone
        click_count = 0
        max_clicks = 20  # safety limit
        print("\n🔽 clicking 'show more books' button...")
        
        while click_count < max_clicks:
            try:
                # find all buttons on the page
                buttons = driver.find_elements(By.TAG_NAME, "button")
                show_more_button = None
                
                # look for the "show more books" button
                for button in buttons:
                    button_text = button.text.lower()
                    if "show more" in button_text and "book" in button_text:
                        show_more_button = button
                        break
                
                if show_more_button and show_more_button.is_displayed():
                    # scroll to button and click it
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", show_more_button)
                    click_count += 1
                    print(f"✅ clicked 'show more books' (click #{click_count})")
                    time.sleep(3)  # wait for new books to load
                else:
                    print(f"🎉 no more 'show more' button! loaded all books after {click_count} clicks")
                    break
                    
            except Exception as e:
                print(f"🎉 finished clicking after {click_count} clicks")
                break
        
        # scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # get the fully rendered page source
        print("\n📄 grabbing page source...")
        page_source = driver.page_source
        
        # parse with beautifulsoup
        print("🍜 parsing html with beautifulsoup...")
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # find all book title links
        book_links = soup.find_all('a', {'data-testid': 'bookTitle'})
        print(f"📚 found {len(book_links)} books!\n")
        
        if len(book_links) == 0:
            print("❌ no books found - something went wrong")
            # save page source for debugging
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("💾 saved page source to debug_page_source.html for inspection")
            return
        
        # scrape each book
        books_data = []
        
        for idx, link in enumerate(book_links, 1):
            try:
                # get title from the link text
                title = link.get_text(strip=True)
                
                # find the parent container that has all the book info
                # we need to go up the tree to find the BookListItem div
                parent = link.find_parent('div', class_=re.compile('BookListItem'))
                
                if not parent:
                    # try alternative parent structure
                    parent = link.find_parent('div')
                
                if parent:
                    # extract author
                    author_span = parent.find('span', {'data-testid': 'name'})
                    author = author_span.get_text(strip=True) if author_span else "N/A"
                    
                    # extract rating
                    rating_span = parent.find('span', class_=re.compile('RatingStatistics'))
                    rating = rating_span.get_text(strip=True) if rating_span else "N/A"
                    
                    # extract ratings count and shelvings count
                    # they're in a div with data-testid="ratingsCount"
                    ratings_div = parent.find('div', {'data-testid': 'ratingsCount'})
                    
                    if ratings_div:
                        ratings_text = ratings_div.get_text(strip=True)
                        
                        # parse with regex: "2m ratings · 3m shelvings"
                        ratings_match = re.search(r'([\d.,]+[kmKM]?)\s+ratings?', ratings_text)
                        shelvings_match = re.search(r'([\d.,]+[kmKM]?)\s+shelvings?', ratings_text)
                        
                        ratings_count = ratings_match.group(1) if ratings_match else "N/A"
                        shelvings_count = shelvings_match.group(1) if shelvings_match else "N/A"
                    else:
                        # alternative: look for text containing "ratings" and "shelvings"
                        all_text = parent.get_text()
                        ratings_match = re.search(r'([\d.,]+[kmKM]?)\s+ratings?', all_text)
                        shelvings_match = re.search(r'([\d.,]+[kmKM]?)\s+shelvings?', all_text)
                        
                        ratings_count = ratings_match.group(1) if ratings_match else "N/A"
                        shelvings_count = shelvings_match.group(1) if shelvings_match else "N/A"
                    
                    # store the book data
                    book_data = {
                        'rank': idx,
                        'title': title,
                        'author': author,
                        'rating': rating,
                        'ratings_count': ratings_count,
                        'shelvings_count': shelvings_count
                    }
                    books_data.append(book_data)
                    
                    print(f"✅ book #{idx}: {title} by {author} ({rating}⭐)")
                else:
                    print(f"⚠️  couldn't find parent for book #{idx}: {title}")
                    
            except Exception as e:
                print(f"❌ error scraping book #{idx}: {e}")
                continue
        
        # save to csv
        if len(books_data) > 0:
            csv_filename = "goodreads_2025_popular_books.csv"
            print(f"\n💾 saving {len(books_data)} books to {csv_filename}...")
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                # csv columns
                fieldnames = ['rank', 'title', 'author', 'rating', 'ratings_count', 'shelvings_count']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # write header
                writer.writeheader()
                
                # write all book data
                for book in books_data:
                    writer.writerow(book)
            
            print(f"✨ done! successfully scraped {len(books_data)} books!")
            print(f"📊 csv saved as: {csv_filename}")
        else:
            print("\n❌ no books were scraped")
        
    except Exception as e:
        print(f"\n❌ fatal error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🔚 closing browser...")
        driver.quit()

if __name__ == "__main__":
    scrape_goodreads_2025()