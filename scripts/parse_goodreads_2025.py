from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import csv
import time
import json
import re

def scrape_goodreads_2025():
    """
    scrapes the most popular books from 2025 on goodreads
    uses BOTH the initial json data AND html parsing after clicking "show more"
    """
    
    url = "https://www.goodreads.com/book/popular_by_date/2025"
    
    # set up chrome options to look like a real browser
    print("🚀 setting up chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    # make selenium less detectable
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        print(f"📖 loading {url}...")
        driver.get(url)
        
        # wait for the page to fully load
        print("⏳ waiting for content to load...")
        time.sleep(8)
        
        # scroll down to trigger any lazy loading
        print("📜 scrolling to load more content...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # click "show more books" button until all books are loaded
        click_count = 0
        max_clicks = 25  # increased to make sure we get all 200
        print("\n🔽 clicking 'show more books' button...")
        
        while click_count < max_clicks:
            try:
                # find all buttons on the page
                buttons = driver.find_elements(By.TAG_NAME, "button")
                show_more_button = None
                
                # look for the "show more books" button
                for button in buttons:
                    try:
                        button_text = button.text.lower()
                        if "show more" in button_text and "book" in button_text:
                            show_more_button = button
                            break
                    except:
                        continue
                
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
                print(f"🎉 finished clicking after {click_count} clicks (error: {e})")
                break
        
        # scroll back to top so we can parse everything
        print("\n📜 scrolling through entire page to ensure everything is loaded...")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # scroll down in chunks to make sure everything renders
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        scroll_increment = 1000
        
        while current_position < total_height:
            current_position += scroll_increment
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(0.5)
        
        # scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # get the fully rendered page source
        print("\n📄 grabbing page source...")
        page_source = driver.page_source
        
        # parse with beautifulsoup to get all visible books
        print("🍜 parsing html with beautifulsoup...")
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # find all book containers
        book_articles = soup.find_all('article', class_='BookListItem')
        print(f"📚 found {len(book_articles)} book containers!\n")
        
        if len(book_articles) == 0:
            print("❌ no books found in html")
            return
        
        # extract data from each book
        books_data = []
        
        for idx, article in enumerate(book_articles, 1):
            try:
                # get title
                title_link = article.find('a', {'data-testid': 'bookTitle'})
                title = title_link.get_text(strip=True) if title_link else "N/A"
                
                # get author
                author_span = article.find('span', {'data-testid': 'name'})
                author = author_span.get_text(strip=True) if author_span else "N/A"
                
                # get rating - it's in the aria-label of the AverageRating div
                rating_div = article.find('div', class_='AverageRating')
                rating = "N/A"
                if rating_div and rating_div.get('aria-label'):
                    # aria-label format: "4.21 stars, 2 million ratings"
                    aria_label = rating_div.get('aria-label')
                    rating_match = re.search(r'([\d.]+)\s+stars?', aria_label)
                    if rating_match:
                        rating = rating_match.group(1)
                
                # get ratings count - also in aria-label
                ratings_count = "N/A"
                if rating_div and rating_div.get('aria-label'):
                    aria_label = rating_div.get('aria-label')
                    # formats: "2 million ratings" or "969 thousand ratings" or "617k ratings"
                    if 'million' in aria_label:
                        count_match = re.search(r'([\d.]+)\s+million', aria_label)
                        if count_match:
                            ratings_count = f"{count_match.group(1)}m"
                    elif 'thousand' in aria_label:
                        count_match = re.search(r'([\d.]+)\s+thousand', aria_label)
                        if count_match:
                            ratings_count = f"{count_match.group(1)}k"
                    else:
                        # try to find the number directly
                        count_match = re.search(r'([\d,]+)\s+ratings?', aria_label)
                        if count_match:
                            ratings_count = count_match.group(1)
                
                # store book data
                book_data = {
                    'rank': idx,
                    'title': title,
                    'author': author,
                    'rating': rating,
                    'ratings_count': ratings_count
                }
                books_data.append(book_data)
                
                # print progress for first 10 and last 10
                if idx <= 10 or idx > len(book_articles) - 10:
                    print(f"✅ #{idx}: {title} by {author} ({rating}⭐, {ratings_count} ratings)")
                elif idx == 11:
                    print(f"... scraping books #11 - {len(book_articles) - 10} ...")
                    
            except Exception as e:
                print(f"❌ error scraping book #{idx}: {e}")
                continue
        
        # save to csv
        if len(books_data) > 0:
            csv_filename = "goodreads_2025_popular_books.csv"
            print(f"\n💾 saving {len(books_data)} books to {csv_filename}...")
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['rank', 'title', 'author', 'rating', 'ratings_count']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for book in books_data:
                    writer.writerow(book)
            
            print(f"✨ done! successfully scraped {len(books_data)} books!")
            print(f"📊 csv saved as: {csv_filename}")
            
            # print summary
            print(f"\n📈 summary:")
            print(f"   total books scraped: {len(books_data)}")
            print(f"   with complete data: {sum(1 for b in books_data if b['author'] != 'N/A' and b['rating'] != 'N/A')}")
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