from bs4 import BeautifulSoup
import requests
import json
from secrets import *
import sqlite3
import plotly.express as px

CACHE_FNAME = 'cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

# if there was no file, no worries. There will be soon!
except:
    CACHE_DICTION = {}


def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_" + "_".join(res)

def get_unique_key(url):
  return url  

def make_request_using_cache_api(baseurl, params):
    unique_ident = params_unique_combination(baseurl,params)

    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    ## if not, fetch the data afresh, add it to the cache,
    ## then write the cache to file
    else:
        print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(baseurl, params)
        CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]
def make_request_using_cache_html(url, header):
    unique_ident = get_unique_key(url)

    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        #print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    ## if not, fetch the data afresh, add it to the cache,
    ## then write the cache to file
    else:
        #print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(url, headers=header)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]


# CREATE DATABASE
# -----------------------------------------------------------
def init_db():
    conn = sqlite3.connect('final_proj.db')
    cur = conn.cursor()

    # Drop tables
    statement = '''
        DROP TABLE IF EXISTS 'Authors';
    '''
    cur.execute(statement)
    statement = '''
        DROP TABLE IF EXISTS 'Books';
    '''
    cur.execute(statement)

    conn.commit()


    statement = '''
        CREATE TABLE 'Authors' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Last' TEXT,
                'First' TEXT
        );
    '''
    cur.execute(statement)
    statement = '''
        CREATE TABLE 'Books' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Title' TEXT,
            'AuthorId' INTEGER,
            'Rating' REAL,
            'Genre' TEXT,
            'Description' TEXT,
            FOREIGN KEY(AuthorId) REFERENCES Authors(Id)
        );
    '''
    cur.execute(statement)
    conn.commit()
    conn.close()

#init_db()

def insert_stuff_authors(book_list):
    conn = sqlite3.connect('final_proj.db')
    cur = conn.cursor()

    for i in book_list:
        first_name = i.author.split()[0]
        if len(i.author.split()) == 2:
            last_name = i.author.split()[1]
        elif len(i.author.split()) == 3:
            last_name = i.author.split()[2]
        else:
            last_name = 'NULL'

        #check to see if author alread in database
        cur.execute('SELECT First,Last FROM Authors WHERE First="' + str(first_name) + '" AND Last="' + str(last_name) + '"')
        check = cur.fetchone()
        #print(check)
        if check == None:
            insertion = (None, last_name, first_name)
            statement = 'INSERT INTO "Authors" '
            statement += 'VALUES (?, ?, ?)'
            cur.execute(statement, insertion)
        else:
            pass
    conn.commit()
    conn.close()

#insert_stuff_authors(d)

def insert_stuff_books(book_list):
    conn = sqlite3.connect('final_proj.db')
    cur = conn.cursor()

    for i in book_list:
        insertion = (None, i.title, i.author, i.rating, i.genre, i.description)
        statement = 'INSERT INTO "Books" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)

        #update AuthorId
        #print(i.author.split())
        if len(i.author.split()) == 1:
            cur.execute('SELECT "Id" FROM Authors WHERE First="' + str(i.author.split()[0]) + '" AND Last="NULL"')
            author_id = cur.fetchone()[0]
            #print(author_id)
            t = (str(author_id), str(i.author))
            statement = 'UPDATE Books '
            statement += 'SET AuthorId=? '
            statement += 'WHERE AuthorId=?'
            #print(statement)
            cur.execute(statement, t)
        elif len(i.author.split()) == 2:
            cur.execute('SELECT "Id" FROM Authors WHERE First="' + str(i.author.split()[0]) + '" AND Last="' + str(i.author.split()[1]) + '"')
            author_id = cur.fetchone()[0]
            #print(author_id)
            t = (str(author_id), str(i.author))
            statement = 'UPDATE Books '
            statement += 'SET AuthorId=? '
            statement += 'WHERE AuthorId=?'
            #print(statement)
            cur.execute(statement, t)
        elif len(i.author.split()) == 3:
            cur.execute('SELECT "Id" FROM Authors WHERE First="' + str(i.author.split()[0]) + '" AND Last="' + str(i.author.split()[2]) + '"')
            author_id = cur.fetchone()[0]
            #print(author_id)
            t = (str(author_id), str(i.author))
            statement = 'UPDATE Books '
            statement += 'SET AuthorId=? '
            statement += 'WHERE AuthorId=?'
            #print(statement)
            cur.execute(statement, t)
    conn.commit()
    conn.close()

#insert_stuff_books(d)

# FUNCTIONS TO RETRIEVE DATA 
# ----------------------------------------------------
wish_list = []
class Book():
    def __init__(self, title, author, rating, desc, genre):
        self.title = title
        self.author = author
        self.rating = rating
        self.description = desc
        self.genre = genre
    def __str__(self):
        return "{} by {} ({})".format(self.title, self.author, self.rating)


def get_books_genre_most_read(genre, plot = False):
    baseurl = 'https://www.goodreads.com/genres'
    genre_url = 'https://www.goodreads.com/genres/most_read/' + genre 
    header = {'User-Agent': 'Mozilla/5.0'}
    page_text = make_request_using_cache_html(genre_url, header)
    page_soup = BeautifulSoup(page_text, 'html.parser')
    content_div = page_soup.find_all(class_ ='coverWrapper')
    books = []
    #print(content_div[0])
    if plot == False:
        for i in content_div[:20]:
            details_url_abbr = i.find('a')['href']
            #print(details_url_abbr)
            details_url = 'https://goodreads.com' + details_url_abbr
            #print(details_url)
            book_page_text = make_request_using_cache_html(details_url, header = header)
            book_page_soup = BeautifulSoup(book_page_text, 'html.parser')
            book_title_header = book_page_soup.find(id = 'bookTitle')
            if book_title_header != None:
                book_title = book_title_header.text.strip()
                #print(book_title)
            book_author_header = book_page_soup.find(class_ = 'authorName')
            if book_author_header != None:
                book_author = book_author_header.text.strip()
            book_rating_header = book_page_soup.find(itemprop = 'ratingValue')
            if book_rating_header != None:
                book_rating = book_rating_header.text.strip()
            book_description_content = book_page_soup.find(id = 'description')
            k = 0
            if book_description_content != None:
                for x in book_description_content:
                    if x != None:
                        k += 1
                        if k > 2:
                            try:
                                book_description = x.text.strip()
                                #print(len(book_description))
                                break
                            except:
                                pass
            else:
                book_description = "No description available"
            #print(book_description)
            book_instance = Book(book_title, book_author, book_rating, book_description, genre)
            books.append(book_instance)
    n = 0
    if plot == True:
        for i in content_div:
            if n < 10:
                n += 1
                details_url_abbr = i.find('a')['href']
                #print(details_url_abbr)
                details_url = 'https://goodreads.com' + details_url_abbr
                #print(details_url)
                book_page_text = make_request_using_cache_html(details_url, header = header)
                book_page_soup = BeautifulSoup(book_page_text, 'html.parser')
                book_title_header = book_page_soup.find(id = 'bookTitle')
                if book_title_header != None:
                    book_title = book_title_header.text.strip()
                    #print(book_title)
                book_author_header = book_page_soup.find(class_ = 'authorName')
                if book_author_header != None:
                    book_author = book_author_header.text.strip()
                book_rating_header = book_page_soup.find(itemprop = 'ratingValue')
                if book_rating_header != None:
                    book_rating = book_rating_header.text.strip()
                book_description_content = book_page_soup.find(id = 'description')
                k = 0
                if book_description_content != None:
                    for x in book_description_content:
                        if x != None:
                            k += 1
                            if k > 2:
                                try:
                                    book_description = x.text.strip()
                                    break
                                    #print(book_description)
                                except:
                                    pass
                else:
                    book_description = "No description available"
                #print(book_description)
                book_instance = Book(book_title, book_author, book_rating, book_description, genre)
                books.append(book_instance)
            else:
                pass
    insert_stuff_authors(books)
    insert_stuff_books(books)
    return books

#d = get_books_genre_most_read('young-adult')



def get_books_genre_popular(genre):
    baseurl = 'https://www.goodreads.com/genres'
    genre_url = 'https://www.goodreads.com/shelf/show/' + genre 
    header = {'User-Agent': 'Mozilla/5.0'}
    page_text = make_request_using_cache_html(genre_url, header)
    page_soup = BeautifulSoup(page_text, 'html.parser')
    content_div = page_soup.find_all(class_ ='elementList')
    books = []
    #print(content_div[0])
    for i in content_div[:20]:
        details_url_abbr = i.find('a')['href']
        #print(details_url_abbr)
        details_url = 'https://goodreads.com' + details_url_abbr
        #print(details_url)
        book_page_text = make_request_using_cache_html(details_url, header = header)
        book_page_soup = BeautifulSoup(book_page_text, 'html.parser')
        book_title_header = book_page_soup.find(id = 'bookTitle')
        #print(book_title_header)
        if book_title_header != None:
            book_title = book_title_header.text.strip()
            #print(book_title)
        book_author_header = book_page_soup.find(class_ = 'authorName')
        if book_author_header != None:
            book_author = book_author_header.text.strip()
            #print(book_author)
        book_rating_header = book_page_soup.find(itemprop = 'ratingValue')
        if book_rating_header != None:
            book_rating = book_rating_header.text.strip()

        book_description_content = book_page_soup.find(id = 'description')
        k = 0
        if book_description_content != None:
            for x in book_description_content:
                k += 1
                if k > 2:
                    try:
                        book_description = x.text.strip()
                        #print(book_description)
                        break
                    except:
                        pass
        else:
            book_description = "No description"
        book_instance = Book(book_title, book_author, book_rating, book_description, genre)
        books.append(book_instance)
    insert_stuff_authors(books)
    insert_stuff_books(books)
    return books

# d = get_books_genre_popular('romance')

# --------------------------------------------------------------
# CREATE BOXPLOTS
# boxplots showing distribution of ratings by genre
def boxplot(genre):
    most_read = get_books_genre_most_read(genre)
    popular = get_books_genre_popular(genre)
    ratings = []
    name = []
    for i in most_read:
        ratings.append(i.rating)
        name.append(genre)
    for j in popular:
        ratings.append(j.rating)
        name.append(genre)
    fig = px.box(ratings, x = name, y = ratings, title = "Ratings for " + str(genre))
    # tips = px.data.tips()
    # print(tips)
    # fig = px.box(tips, y="total_bill")
    fig.write_html('plots_for_final.html', auto_open=True)

def multiple_boxplot(list_of_genres):
    ratings = []
    name = []
    for genre in list_of_genres:
        most_read = get_books_genre_most_read(genre, plot = True)
        #popular = get_books_genre_popular(genre)
        for i in most_read:
            ratings.append(i.rating)
            name.append(genre)
        # for j in popular:
        #     ratings.append(j.rating)
        #     name.append(genre)
    fig = px.box(ratings, x = name, y = ratings, title = "Comparison of Genre Ratings")
    # tips = px.data.tips()
    # print(tips)
    # fig = px.box(tips, y="total_bill")
    fig.update_xaxes(title_text='Genre')
    fig.update_yaxes(title_text='Rating')
    fig.write_html('plots_for_final.html', auto_open=True)
#boxplot('romance')
#multiple_boxplot(['Philosophy', 'Poetry', 'Psychology'])
#--------------------------------------------------------------------

# Make program so that user can select multiple genres and compare ratings via boxplots!
genre_choices_list = {'Art': 'art', 'Biography': 'biography','Business':'business','Chick-Lit':'chick-lit',"Children's":'childrens', 'Christian':'christian','Classics':'classics','Comics':'comics','Contemporary':'contemporary','Cookbooks':'coockbooks','crime':'crime','Ebooks':'ebooks','Fantasy':'fantasy','Fiction':'fiction','LGBTQ':'lgbt','Graphic-Novels':'graphic-novles','Historical-Fiction':'historical-fiction','History':'history','Horror':'horror','Humor':'humor','Manga':'manga','Memoir':'memoir','Music':'music','Mystery':'mystery','Nonfiction': 'non-fiction','Paranormal':'paranormal','Philosophy':'philosophy','Poetry':'Poetry','Psychology':'psychology','Religion':'religion','Romance':'romance','Science':'science','Science-Fiction': 'science-fiction','Self-Help':'self-help','Suspense':'suspense','Spirituality':'spirituality','Sports':'sports','Thriller':'thriller','Travel':'travel','Young-Adult':'young-adult'}
lowercase_genre_choices = []
for i in genre_choices_list:
    lowercase_genre_choices.append(i.lower())
#print(lowercase_genre_choices)
def print_genre_choices():
    pretty_list = []
    for i in genre_choices_list:
        pretty_list.append(i)
    enumerated_pretty_list = list(enumerate(pretty_list,1))
    for i in enumerated_pretty_list:
        print(i[0],i[1])
    #return enumerated_pretty_list

def get_enumerated_genre_choices():
    pretty_list = []
    for i in genre_choices_list:
        pretty_list.append(i)
    enumerated_pretty_list = list(enumerate(pretty_list,1))
    return enumerated_pretty_list

def print_instructions():
    i = '''
Possibe commands:
list genres:
    Presents the list of available genres
    A valid genre is how it is presented in this list (all lowercase is fine)
popular <genre number>/<genre name>
    Presents the list of most popular books in that genre 
    example calls: popular 3, popular fiction
most read <genre number>/<genre name> 
    Presents the list of most read books of that genre this week
    example calls: most read 16, most read fantasy
compare <list of genre numbers/names seperated by comma>
    Presents box plots comparing the ratings of desired genres
    Please don't put spaces in genre list
    example calls: compare 3,6,11 or compare bibliography,horror,mystery,romance
exit
    Exits the program
help
    Provides list of available commands (these instructions)
        '''
    print(i)
# b = get_enumerated_genre_choices()
# print(b)
#print_instructions()
def interactive_program():
    accepted_first = ['popular','most','compare','help','exit','list', 'info']
    response = ''
    enumerated_genres = get_enumerated_genre_choices()
    init_db()
    while response != 'exit':
        print(" ")
        response = input("Enter a command: ")
        split = response.split()
        if split[0] not in accepted_first:
            print("Invalid command. Please try again")
        if split[0] == "list":
            print_genre_choices()
        elif split[0] == "help":
            print_instructions()
        elif split[0] == "compare":
            genres_to_compare = split[1].split(',')
            #print(genres_to_compare)
            # numbers given
            if str.isnumeric(genres_to_compare[0]) == True:
                #print("yes")
                updated_list = []
                for genre_num in genres_to_compare:
                    for x in enumerated_genres:
                        if x[0] == int(genre_num):
                            #print("got it ")
                            #print(x[1])
                            updated_list.append([x[1]])
                real_list = []
                #print(real_list)
                for i in updated_list:
                    real_list.append(i[0])
                #print(real_list)
                multiple_boxplot(real_list)
            # words given
            else:
                for g in genres_to_compare:
                    if g not in lowercase_genre_choices:
                        print("Only valid genres will be graphed")
                        continue
                updated_list = []
                #print(genres_to_compare)
                for genre in genres_to_compare:
                    for k in genre_choices_list:
                        if k.lower() == genre:
                            updated_list.append(genre_choices_list[k])
                #print(updated_list)
                multiple_boxplot(updated_list)
        elif split[0] == "popular":
            if str.isnumeric(split[1]) == True:
                for x in enumerated_genres:
                    if int(split[1]) == x[0]:
                        book_list = get_books_genre_popular(genre_choices_list[x[1]])
            elif split[1] not in lowercase_genre_choices:
                print("Please enter a valid genre")
                #print(" ")
                continue
            else:
                for k in genre_choices_list:
                    if k.lower() == split[1]:
                        book_list = get_books_genre_popular(genre_choices_list[k])
            active_enumerated_book_list = list(enumerate(book_list,start = 1))
            active = "popular"
            for b in active_enumerated_book_list:
                print(b[0], b[1])
            print("type 'info <book number> to get the book's description")
            print(" ")
        elif split[0] == "most":
            if str.isnumeric(split[-1]) == True:
                for x in enumerated_genres:
                    if int(split[-1]) == x[0]:
                        book_list = get_books_genre_most_read(genre_choices_list[x[1]])
            elif split[-1] not in lowercase_genre_choices:
                print("Please enter a valid genre")
                #print(" ")
                continue
            else:
                for k in genre_choices_list:
                    if k.lower() == split[-1]:
                        book_list = get_books_genre_popular(genre_choices_list[k])
            active_enumerated_book_list = list(enumerate(book_list,start = 1))
            active = "most read"
            for b in active_enumerated_book_list:
                print(b[0], b[1])
            print("Type 'info <book number> to get the book's description")
            print(" ")
        elif split[0] == "info":
            try:
                for m in active_enumerated_book_list:
                    if int(split[1]) == m[0]:
                        title_for_description = m[1].title
                        print(title_for_description)
                        conn = sqlite3.connect('final_proj.db')
                        cur = conn.cursor()
                        cur.execute('SELECT Description FROM Books WHERE Title="' + str(title_for_description) + '"')
                        info = cur.fetchone()[0]
                        print(info)
                        conn.commit()
                        conn.close()
            except:
                print("No active book list. Get one by typing popular <genre> or most read <genre>")
                print(" ")
    print("Bye!")




if __name__ == "__main__": 
    interactive_program()
    pass
                        




