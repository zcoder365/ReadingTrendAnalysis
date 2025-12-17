from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import csv
import time
import re

def get_correct_genres(driver, book_url, max_genres=2):
    """
    visits a book page and extracts the ACTUAL genres (not the nav menu!)
    returns comma-separated string of top 1-2 genres
    """
    if not book_url:
        return "N/A"
    
    try:
        driver.get(book_url)
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # the actual genres are in the page text after "Genres" label
        # they're links that look like: <a href="/genres/fantasy">Fantasy</a>
        # but we need to SKIP the navigation menu at the top
        
        genres = []
        
        # method 1: find the "Genres" text and get the links after it
        page_text = soup.get_text()
        if 'Genres' in page_text:
            # find all genre links (they have /genres/ in href)
            all_genre_links = soup.find_all('a', href=re.compile(r'/genres/'))
            
            # the navigation menu genres (we want to SKIP these):
            nav_genres = {'Art', 'Biography', 'Business', "Children's", 'Christian', 
                         'Classics', 'Comics', 'Cookbooks', 'Ebooks', 'Fantasy', 
                         'Fiction', 'Graphic Novels', 'Historical Fiction', 'History',
                         'Horror', 'Memoir', 'Music', 'Mystery', 'Nonfiction', 'Poetry',
                         'Psychology', 'Romance', 'Science', 'Science Fiction', 
                         'Self Help', 'Sports', 'Thriller', 'Travel', 'Young Adult'}
            
            # collect genres that are NOT in the nav menu
            seen = set()
            for link in all_genre_links:
                genre_text = link.get_text(strip=True)
                
                # skip if it's a nav menu genre AND appears early in the page
                # (book genres appear later in the page)
                if genre_text in nav_genres:
                    # check if this is likely the nav (by looking at parent structure)
                    parent_text = link.parent.get_text(strip=True) if link.parent else ""
                    # if the parent contains the nav menu genres, skip it
                    if any(nav in parent_text for nav in ['Home', 'My Books', 'Browse', 'Community']):
                        continue
                
                # valid genre criteria:
                if (genre_text and 
                    len(genre_text) < 30 and  # genres are usually short
                    genre_text not in seen):
                    genres.append(genre_text)
                    seen.add(genre_text)
                    
                    if len(genres) >= max_genres:
                        break
        
        if genres:
            return ", ".join(genres[:max_genres])
        
        return "N/A"
        
    except Exception as e:
        print(f"      error: {e}")
        return "N/A"


def fix_genres_in_csv(input_csv, output_csv, max_genres=2):
    """
    reads csv with wrong genres, gets correct genres from book pages
    saves to new csv with correct genres
    """
    print("🚀 setting up chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        # read existing csv
        print(f"📖 reading {input_csv}...")
        books = []
        with open(input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            books = list(reader)
        
        print(f"📚 found {len(books)} books\n")
        
        # get correct genres for each book
        print(f"🎨 getting correct top {max_genres} genre(s) for each book...")
        print("   (this will take ~30-60 mins)\n")
        
        for idx, book in enumerate(books, 1):
            # construct book url from title and author
            title = book.get('title', '')
            author = book.get('author', '')
            
            # search for book on goodreads
            search_query = f"{title} {author}".replace(' ', '+')
            search_url = f"https://www.goodreads.com/search?q={search_query}"
            
            try:
                # go to search page
                driver.get(search_url)
                time.sleep(2)
                
                # click first result to get to book page
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                first_result = soup.find('a', class_=re.compile('bookTitle'))
                
                if first_result:
                    book_url = first_result.get('href')
                    if not book_url.startswith('http'):
                        book_url = f"https://www.goodreads.com{book_url}"
                    
                    # get genres from book page
                    genres = get_correct_genres(driver, book_url, max_genres)
                    book['genres'] = genres
                    
                    # progress update every 10 books
                    if idx % 10 == 0:
                        print(f"   ✅ {idx}/{len(books)} - {title[:40]}... → {genres}")
                else:
                    book['genres'] = "N/A"
                    print(f"   ❌ {idx}/{len(books)} - couldn't find: {title[:40]}")
                
            except Exception as e:
                book['genres'] = "N/A"
                print(f"   ❌ {idx}/{len(books)} - error: {e}")
            
            time.sleep(1.5)  # be nice to goodreads
        
        print(f"\n✅ finished getting genres!\n")
        
        # save to new csv
        print(f"💾 saving corrected data to {output_csv}...")
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['year', 'rank', 'title', 'author', 'rating', 'ratings_count', 'genres']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for book in books:
                writer.writerow(book)
        
        print(f"✨ done! saved to {output_csv}\n")
        
        # show sample
        print("📊 sample of corrected genres (first 10 books):")
        for book in books[:10]:
            print(f"   {book['title'][:50]}: {book['genres']}")
    
    except Exception as e:
        print(f"\n❌ error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🔚 closing browser...")
        driver.quit()


if __name__ == "__main__":
    print("=" * 60)
    print("GENRE FIXER - Getting correct book genres")
    print("=" * 60)
    
    # your files
    input_file = "goodreads_2020_to_2025_books.csv"
    output_file = "goodreads_2020_to_2025_books_FIXED.csv"
    
    # get top 2 genres for each book
    fix_genres_in_csv(input_file, output_file, max_genres=1)