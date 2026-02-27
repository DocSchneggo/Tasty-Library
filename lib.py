import os, pathlib as path, json as jsn, yaml as yml, sqlite3 as sql
import pyfzf.pyfzf as f
import codes as Codes
from datetime import datetime as dt, timedelta as td

class Validation:
    def __init__(self, *, only:list[str]|None = None, exclude:list[str] | None = None):
        self.only = only
        self.exclude = exclude
    
    def validate(self, s:str):
        if self.only:
            for i in s:
                if not i in self.only:
                    return False, i
            return True, None
        
        for j in s:
            if j in self.exclude:
                return False, j
            
        return True, None
    
SQL_CREATE_TABLES = """
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  created_at VARCHAR(255),
  name VARCHAR(255) UNIQUE,
  state INTEGER
);
CREATE TABLE books (
  id INTEGER PRIMARY KEY,
  created_at VARCHAR(255),
  title VARCHAR(255),
  isbn VARCHAR(255),
  description VARCHAR(255),
  author VARCHAR(255),
  borrowed_by VARCHAR(255),
  borrowed_at VARCHAR(255)
);
CREATE TABLE borrows (
  id INTEGER PRIMARY KEY,
  created_at VARCHAR(255),
  book_id INT,
  borrower_id INT,
  return_date VARCHAR(255),
  renewed INT,
  delayed BOOLEAN
);
CREATE TABLE settings (
  id INTEGER PRIMARY KEY,
  key VARCHAR(255),
  value VARCHAR(255)
);
"""

def findProfile():
    """
    Finds available profiles in the local directory.
    """
    profiles = []
    for i in os.listdir():
        if i.endswith(".tl"):
            profiles.append(i)
          
    return profiles

def getDB():
    """
    Gets the selected Profile and returns the database.
    """
    with open(path.Path(__file__).parent / "config.json", "r") as f:
        config_data:dict = jsn.load(f)
    try:
        return sql.connect(path.Path(config_data["active_profile_path"]) / (config_data["active_profile_name"] + ".db"))
    except IndexError as e:
        print("No Profile selected. Please use tl connect to select a profile.", str(e))
        return False
    
class UserStates:
    """
    An enum for User states
    """
    Active = 0
    Inactive = 1
    Banned = 2
    BannedFromBorrowing = 3
    Special1 = 4

def table(keys:list[str], values:list, spacing:int=30):
    """
    Generates a table from keys and values with a set spacing.
    """
    string_ = []
    for i in keys:
        string_.append(f"{i.ljust(spacing)}")
    string = "|".join(string_)
    string += "\n" + ("="*(spacing*len(keys) + len(keys))) + "\n"
    for i in values:
        subs_ = []
        for j in i:
            subs_.append(str(j).ljust(spacing))
        subs = "|".join(subs_) + "\n"
        string += subs
    
    print(string)

def fzf_book(data:list):
    """
    A fzf-like list for selecting a book.
    """
    string:list[str] = []
    for i in data:
        string.append(f"{"BORROWED" if i[6] else "        "} | {str(i[0]).ljust(5)} | {str(i[2])[:50].ljust(50)} | {str(i[5])[:40].ljust(40)} | {str(i[4])[:50]}")
    
    fzf = f.FzfPrompt()
    try: 
        choice = fzf.prompt(choices=string,
            fzf_options = '--header="BORROWED | ID    | TITLE                                              | AUTHORS                                  | DESCRIPTION"'
        )
        if not choice:
            return Codes.BooksFinder.NoBookSelected, None
        idx = string.index(choice[0])
        book = data[idx]
        if string[idx].startswith("BORROWED"):
            return Codes.BooksFinder.BorrowedBookSelected, book
        return book, None
    except ValueError or IndexError:
        return Codes.BooksFinder.NoBookSelected, None


def confirm(prompt:str, options:dict={"y":True, "n":False}, default="y"):
    """
    Confirmation prompt with customisable options.
    """
    conf = input(f"{prompt} [{"/".join([(i.upper() if default == i else i) for i in list(options.keys())])}]: ").lower()
    if conf not in options.keys():
        conf = default
    
    return options[conf]

def getConfig():
    """
    Gets the tl config file.
    """
    with open(path.Path(__file__).parent / "config.json", "r") as f:
        config_data = jsn.load(f)
    return config_data

def getProfileSettings():
    """
    Gets the settings from the active profile.
    """
    try:
        path_ = getConfig()["active_profile_path"]
        with open(path.Path(path_) / "settings.yml") as f:
            data = yml.load(f.read(), yml.loader.Loader)
        return data
    except:
        return False
    
def checkUserCanBorrow(name_or_id:str, db:sql.Connection):
    """
    Checks if the user can borrow books using the criteria defined in the profile's setting.yml file.
    """
    cur = db.cursor()

    user_res_u = cur.execute("SELECT u.* FROM users u LEFT JOIN borrows b ON u.id=b.borrower_id WHERE u.id=? OR u.name=?", (name_or_id, name_or_id))
    book_res = cur.execute("SELECT b.return_date, b.id FROM users u LEFT JOIN borrows b ON u.id=b.borrower_id WHERE u.id=? OR u.name=?", (name_or_id, name_or_id))
    borrows_of_user = book_res.fetchall()
    user = user_res_u.fetchone()
    if not user_res_u.fetchall(): return True

    delayed_book_count = sum([1 if i[0] == dt.now().date() else 0 for i in borrows_of_user])
    book_count = len(borrows_of_user)
    state = user[3]

    settings = getProfileSettings()
    max_books = settings["maxBooks"]
    max_delayed_books = settings["maxDelayedBook"]
    
    if max_delayed_books != "*":
        return True if delayed_book_count < max_delayed_books else Codes.Borrowing.UserDelayedBook
    if max_books != "*":
        return True if book_count < max_books else Codes.Borrowing.UserTooManyBooks
    return Codes.Borrowing.UserBanned if state == UserStates.Banned else True

def plOrSg(val:int, pl:str, sg:str):
    return pl if val != 1 else sg

def fzf(keys:dict[str:int], vals:list[list|tuple]):
    title_row = " | ".join([i.upper().ljust(keys[i]) for i in keys.keys()])
    pad = []
    for i in keys:
        pad.append(keys[i])
    data = []
    for i in vals:
        row = " | ".join([str(j).ljust(pad[i.index(j)]) for j in i])
        data.append(row)

    fzf_ = f.FzfPrompt()
    choice = fzf_.prompt(data, f'--header="{title_row}"')
    if not choice:
        return None
    
    idx = data.index(choice[0])
    print(idx)
    return idx

def confirm_book(title, authors, description, isbn):
    return confirm(f"""
Do you confirm the Following information:
=========================================
Title: {title}
Author/s: {authors}
Description: {description}
ISBN: {isbn}
Is this information correct? """)