from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import time
import json
import re

def scrape_goodreads_2025():
    """
    scrapes the most popular books from 2025 on goodreads
    extracts data from the __NEXT_DATA__ json embedded in the page
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
        
        # get the fully rendered page source
        print("\n📄 grabbing page source...")
        page_source = driver.page_source
        
        # extract the json data from the __NEXT_DATA__ script tag
        print("🔍 extracting json data from page...")
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page_source, re.DOTALL)
        
        if not match:
            print("❌ could not find __NEXT_DATA__ json!")
            return
        
        # parse the json
        json_data = json.loads(match.group(1))
        
        # navigate to the apollo state which contains all book data
        apollo_state = json_data['props']['pageProps']['apolloState']
        
        # extract all book data from the apollo state
        books_data = []
        
        print("📚 parsing book data from json...\n")
        
        # iterate through all Work objects in the apollo state
        for key, value in apollo_state.items():
            if key.startswith('Work:') and isinstance(value, dict):
                # get book stats (ratings, average rating)
                stats = value.get('stats', {})
                ratings_count = stats.get('ratingsCount', 0)
                average_rating = stats.get('averageRating', 0)
                
                # get the best book reference
                details = value.get('details', {})
                best_book_ref = details.get('bestBook', {}).get('__ref', '')
                
                if not best_book_ref:
                    continue
                
                # look up the book details in apollo state
                book = apollo_state.get(best_book_ref, {})
                
                if not book:
                    continue
                
                # extract title
                title = book.get('titleComplete', 'N/A')
                
                # extract author
                author_edge = book.get('primaryContributorEdge', {})
                author_ref = author_edge.get('node', {}).get('__ref', '')
                author_data = apollo_state.get(author_ref, {})
                author = author_data.get('name', 'N/A')
                
                # format ratings count (convert to k/m format)
                if ratings_count >= 1000000:
                    formatted_ratings = f"{ratings_count / 1000000:.1f}m"
                elif ratings_count >= 1000:
                    formatted_ratings = f"{ratings_count / 1000:.0f}k"
                else:
                    formatted_ratings = str(ratings_count)
                
                # store book data with raw count for sorting
                books_data.append({
                    'title': title,
                    'author': author,
                    'rating': average_rating,
                    'ratings_count': formatted_ratings,
                    'ratings_count_raw': ratings_count  # for sorting
                })
        
        # sort by ratings count (most popular first)
        books_data.sort(key=lambda x: x['ratings_count_raw'], reverse=True)
        
        # add rank and remove raw count
        for idx, book in enumerate(books_data, 1):
            book['rank'] = idx
            del book['ratings_count_raw']
        
        print(f"✨ found {len(books_data)} books!\n")
        
        # print first 10 books
        for book in books_data[:10]:
            print(f"✅ #{book['rank']}: {book['title']} by {book['author']} ({book['rating']}⭐, {book['ratings_count']} ratings)")
        
        if len(books_data) > 10:
            print(f"... and {len(books_data) - 10} more books ...\n")
        
        # save to csv
        if len(books_data) > 0:
            csv_filename = "goodreads_2025_popular_books.csv"
            print(f"💾 saving {len(books_data)} books to {csv_filename}...")
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['rank', 'title', 'author', 'rating', 'ratings_count']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
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