import csv
import re

def convert_rating_count(rating_str):
    """
    converts rating count strings to actual numbers
    examples:
    - "1.5m" -> 1500000
    - "234k" -> 234000
    - "1,234" -> 1234
    - "N/A" -> 0
    """
    if rating_str == "N/A" or not rating_str:
        return 0
    
    # remove any whitespace
    rating_str = rating_str.strip()
    
    # check for millions
    if 'm' in rating_str.lower():
        # remove 'm' and convert to float, then multiply by 1,000,000
        number = float(rating_str.lower().replace('m', ''))
        return int(number * 1000000)
    
    # check for thousands
    elif 'k' in rating_str.lower():
        # remove 'k' and convert to float, then multiply by 1,000
        number = float(rating_str.lower().replace('k', ''))
        return int(number * 1000)
    
    # regular number with commas
    else:
        # remove commas and convert to int
        return int(rating_str.replace(',', ''))


def clean_goodreads_csv(input_filename, output_filename=None):
    """
    reads a goodreads csv and converts the ratings_count column to actual numbers
    if no output_filename is provided, it'll add '_cleaned' to the input filename
    """
    # if no output filename provided, create one
    if output_filename is None:
        # if input is "goodreads_2020_to_2025_books.csv"
        # output will be "goodreads_2020_to_2025_books_cleaned.csv"
        output_filename = input_filename.replace('.csv', '_cleaned.csv')
    
    print(f"📖 reading {input_filename}...")
    
    # read the csv
    with open(input_filename, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        # store all rows
        rows = []
        for row in reader:
            # convert the ratings_count to a number
            if 'ratings_count' in row:
                row['ratings_count'] = convert_rating_count(row['ratings_count'])
            rows.append(row)
    
    print(f"✅ processed {len(rows)} books")
    print(f"💾 saving cleaned data to {output_filename}...")
    
    # write the cleaned csv
    with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✨ done! cleaned csv saved as: {output_filename}")
    
    # show some example conversions
    print(f"\n📊 sample conversions:")
    for i, row in enumerate(rows[:5]):
        print(f"   {row['title']}: {row['ratings_count']:,} ratings")


if __name__ == "__main__":
    # USAGE: change this to your actual csv filename
    # once your scraper finishes, it'll create "goodreads_2020_to_2025_books.csv"
    # then run this script to clean it!
    
    input_file = "goodreads_2020_to_2025_books.csv"
    
    # this will create "goodreads_2020_to_2025_books_cleaned.csv"
    clean_goodreads_csv(input_file)
    
    # or if you want to specify a custom output name:
    # clean_goodreads_csv(input_file, "my_clean_data.csv")