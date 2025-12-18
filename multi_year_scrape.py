from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import csv
import time
import re

def scrape_goodreads_year(driver, year):
    """
    scrapes books from a specific year
    returns list of book data dictionaries
    """
    url = f"https://www.goodreads.com/book/popular_by_date/{year}"
    
    try:
        print(f"\n📖 loading {year} books from {url}...")
        driver.get(url)
        
        # wait for page to load
        print(f"⏳ waiting for {year} content to load...")
        time.sleep(8)
        
        # scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # click "show more books" until all books load
        click_count = 0
        max_clicks = 25
        print(f"📽 clicking 'show more books' for {year}...")
        
        while click_count < max_clicks:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                show_more_button = None
                
                for button in buttons:
                    try:
                        button_text = button.text.lower()
                        # IMPORTANT: must have BOTH "show more" AND "book" to avoid clicking individual book descriptions
                        if "show more" in button_text and "book" in button_text:
                            show_more_button = button
                            break
                    except:
                        continue
                
                if show_more_button and show_more_button.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", show_more_button)
                    click_count += 1
                    if click_count % 5 == 0:  # print every 5 clicks
                        print(f"   clicked {click_count} times...")
                    time.sleep(3)
                else:
                    print(f"   loaded all books after {click_count} clicks")
                    break
            except:
                break
        
        # scroll through page to ensure everything renders
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        scroll_increment = 1000
        
        while current_position < total_height:
            current_position += scroll_increment
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(0.3)
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # parse html
        print(f"🍜 parsing {year} html...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        book_articles = soup.find_all('article', class_='BookListItem')
        print(f"📚 found {len(book_articles)} books for {year}!\n")
        
        if len(book_articles) == 0:
            return []
        
        books_data = []
        
        for idx, article in enumerate(book_articles, 1):
            try:
                # get title
                title_link = article.find('a', {'data-testid': 'bookTitle'})
                title = title_link.get_text(strip=True) if title_link else "N/A"
                
                # get book url for genre scraping later
                book_url = title_link.get('href') if title_link else None
                if book_url and not book_url.startswith('http'):
                    book_url = f"https://www.goodreads.com{book_url}"
                
                # get author
                author_span = article.find('span', {'data-testid': 'name'})
                author = author_span.get_text(strip=True) if author_span else "N/A"
                
                # get rating from aria-label
                rating_div = article.find('div', class_='AverageRating')
                rating = "N/A"
                ratings_count = "N/A"
                
                if rating_div and rating_div.get('aria-label'):
                    aria_label = rating_div.get('aria-label')
                    
                    # extract rating
                    rating_match = re.search(r'([\d.]+)\s+stars?', aria_label)
                    if rating_match:
                        rating = rating_match.group(1)
                    
                    # extract ratings count
                    if 'million' in aria_label:
                        count_match = re.search(r'([\d.]+)\s+million', aria_label)
                        if count_match:
                            ratings_count = f"{count_match.group(1)}m"
                    elif 'thousand' in aria_label:
                        count_match = re.search(r'([\d.]+)\s+thousand', aria_label)
                        if count_match:
                            ratings_count = f"{count_match.group(1)}k"
                    else:
                        count_match = re.search(r'([\d,]+)\s+ratings?', aria_label)
                        if count_match:
                            ratings_count = count_match.group(1)
                
                book_data = {
                    'year': year,
                    'rank': idx,
                    'title': title,
                    'author': author,
                    'rating': rating,
                    'ratings_count': ratings_count,
                    'book_url': book_url
                }
                books_data.append(book_data)
                
                # print first 5 and last 5
                if idx <= 5 or idx > len(book_articles) - 5:
                    print(f"   ✅ #{idx}: {title} by {author}")
                elif idx == 6:
                    print(f"   ... scraping #{idx} - {len(book_articles) - 5} ...")
                    
            except Exception as e:
                print(f"   ❌ error scraping book #{idx}: {e}")
                continue
        
        return books_data
        
    except Exception as e:
        print(f"❌ error scraping {year}: {e}")
        return []


def get_book_genres(driver, book_url, max_genres=1):
    """
    visits a book's page and extracts its primary genre
    returns single genre string
    """
    if not book_url:
        return "N/A"
    
    try:
        driver.get(book_url)
        time.sleep(2)  # wait for page to load
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # strategy 1: look for the word "Genres" in the html, then grab the genre links that follow
        # find all text nodes containing "Genres" (using 'string' instead of deprecated 'text')
        all_text = soup.find_all(string=re.compile(r'Genres', re.IGNORECASE))
        
        for text_node in all_text:
            # get the parent element
            parent = text_node.parent
            if parent:
                # look for genre links near this "Genres" label
                # try to find sibling elements or children with genre links
                genre_links = parent.find_all('a', href=re.compile(r'/genres/'))
                
                # filter out navigation/generic links
                valid_genres = []
                for link in genre_links:
                    genre_text = link.get_text(strip=True)
                    # genres should be short, single words or two words max
                    if genre_text and len(genre_text) < 30 and not any(skip in genre_text.lower() for skip in ['browse', 'explore', 'home', 'recommendations']):
                        valid_genres.append(genre_text)
                
                if valid_genres:
                    # return just the first (primary) genre
                    return valid_genres[0]
        
        # strategy 2: if strategy 1 fails, look for specific genre-related div classes
        # goodreads often uses specific containers for book metadata
        genre_container = soup.find('div', class_=re.compile(r'genre', re.IGNORECASE))
        if genre_container:
            genre_links = genre_container.find_all('a', href=re.compile(r'/genres/'))
            for link in genre_links[:1]:  # just get the first one
                genre_text = link.get_text(strip=True)
                if genre_text and len(genre_text) < 30:
                    return genre_text
        
        # strategy 3: as a last resort, look for buttons or spans near "Genres"
        # (goodreads sometimes wraps genres in button elements)
        all_elements = soup.find_all(['button', 'span', 'a'])
        collecting = False
        for elem in all_elements:
            text = elem.get_text(strip=True)
            if 'Genres' in text:
                collecting = True
                continue
            if collecting and elem.name == 'a' and '/genres/' in elem.get('href', ''):
                genre_text = text
                if genre_text and len(genre_text) < 30:
                    return genre_text
                collecting = False  # stop after first genre
        
        return "N/A"
        
    except Exception as e:
        print(f"   ⚠️ error getting genre for {book_url}: {e}")
        return "N/A"


def scrape_goodreads_multi_year(start_year, end_year, include_genres=False):
    """
    scrapes goodreads data for multiple years
    optionally includes genre data (much slower)
    """
    print("🚀 setting up chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    all_books = []
    
    try:
        # scrape each year
        for year in range(start_year, end_year + 1):
            year_books = scrape_goodreads_year(driver, year)
            all_books.extend(year_books)
            print(f"✅ scraped {len(year_books)} books from {year}")
        
        print(f"\n🎉 total books scraped: {len(all_books)}")
        
        # optionally get genres
        if include_genres and len(all_books) > 0:
            print(f"\n🎨 getting genres for {len(all_books)} books (this will take a while)...")
            
            for idx, book in enumerate(all_books, 1):
                genres = get_book_genres(driver, book.get('book_url'))
                book['genres'] = genres
                
                if idx % 50 == 0:  # progress update every 50 books
                    print(f"   processed {idx}/{len(all_books)} books...")
                
                time.sleep(1)  # be nice to the server
            
            print(f"✅ finished getting genres!")
        
        # save to csv
        if len(all_books) > 0:
            csv_filename = f"goodreads_{start_year}_to_{end_year}_books.csv"
            print(f"\n💾 saving {len(all_books)} books to {csv_filename}...")
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['year', 'rank', 'title', 'author', 'rating', 'ratings_count']
                if include_genres:
                    fieldnames.append('genres')
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                for book in all_books:
                    writer.writerow(book)
            
            print(f"✨ done! successfully scraped {len(all_books)} books!")
            print(f"📊 csv saved as: {csv_filename}")
            
            # summary by year
            print(f"\n📈 summary by year:")
            for year in range(start_year, end_year + 1):
                count = sum(1 for b in all_books if b['year'] == year)
                print(f"   {year}: {count} books")
        
    except Exception as e:
        print(f"\n❌ fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n📚 closing browser...")
        driver.quit()


if __name__ == "__main__":
    # TEST MODE - scrape just 2025 to verify it works
    print("=" * 60)
    print("GOODREADS SCRAPER: 2025 ONLY (TEST)")
    print("=" * 60)
    
    # scraping WITH genres - will take ~30-60 minutes for all books
    scrape_goodreads_multi_year(2025, 2025, include_genres=True)