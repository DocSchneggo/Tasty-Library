from argparse import ArgumentParser, FileType
from sys import argv
import sqlite3 as sql
import yaml as yml
import json as jsn
import os
import pathlib as path
from datetime import datetime as dt
from datetime import timedelta as td
import pyfzf.pyfzf as f
import urllib.request
import codes
from dlxml import DeliciousXML
from time import sleep
import csv
from lib import UserStates

def BOOKS_API_BASE_LINK(isbn:str):
    return f"http://openlibrary.org/api/volumes/brief/isbn/{isbn}.json"

import lib
import presets as prs

parser = ArgumentParser("tl")
# parser.add_argument("-i", "--interactive", action="store_true", help="Start in interactive mode (Work in progress)") # TODO: implement
commands = parser.add_subparsers(
    title="command",
    dest="subcommands"
)

connect = commands.add_parser("connect", help="Connect to a profile", aliases=["c"])
connect.add_argument("path", type=str, help = "The path to the .tl folder")

user_commands = commands.add_parser("user", help="Manage Users", aliases=["u"])
user_commands_p = user_commands.add_subparsers(title="user commands", dest="user_subcommand")
remove_user = user_commands_p.add_parser("remove", help="Remove a user by username or id")
remove_user.add_argument("-b", "--ban", help = "The person is removed and banned from using the library. Provide the ban reason. For banning, see tl help banning", type=str)
remove_user.add_argument("-n", "--name", help = "ID to remove.", required=True, nargs="*")

query_user = user_commands_p.add_parser("query", help="Query Users by different criteria.")
query_user.add_argument("-d", "--delayed", help="Get all users that have delayed books.", action="store_true")
# query_user.add_argument("-s", "--sql", help="Execute an SQL statement. For more info consult tl help sql", type=str)
query_user.add_argument("-e", "--empty", help="Get all users that have no books.", action="store_true")
query_user.add_argument("-r", "--borrowed", help="Get all users that have books.", action="store_true")
query_user.add_argument("-b", "--banned", help="Show all banned users", action="store_true")
query_user.add_argument("-a", "--active", help="Show all active users", action="store_true")
query_user.add_argument("-n", "--inactive", help="Show all inactive users", action="store_true")
query_user.add_argument("-j", "--export-json", help="Export as json.", metavar="json_file")
query_user.add_argument("-t", "--export-txt", help="Export as txt.", metavar="txt_file")
query_user.add_argument("-c", "--export-csv", help="Export as csv.", metavar="csv_file")

manage_user = user_commands_p.add_parser("manage", help="Manage users database.")
manage_user.add_argument("-r", "--rename", help="Rename the user.")
manage_user.add_argument("-b", "--ban", help="Ban the user. For banning, see tl help banning")
manage_user.add_argument("-s", "--state", help="Set the user state.")
manage_user.add_argument("-c", "--clear", help="Clear the Users booklist. All books are automatically returned.")
manage_user.add_argument("name", help="Username. if left empty, a selection list is showed", nargs="*")

add_user = user_commands_p.add_parser("add", help="Add new users to the system.")
add_user.add_argument("name", type=str, help="The Username of the new user.", nargs="*")

borrow_p = commands.add_parser("borrow", help="Borrow books by user", aliases=["b"])
borrow_p.add_argument("name", help="Username or id", nargs="*")

return_p = commands.add_parser("return", aliases=["r"], help="return books")
return_by = return_p.add_mutually_exclusive_group(required=True)
return_by.add_argument("userid", help="user id", nargs="*")
return_by.add_argument("borrow_id", help="borrow id", nargs="*")
return_by.add_argument("username", help="username", nargs="*")

setup_p = commands.add_parser("setup", help="Setup new databases", prefix_chars="setup")
setup_commands = setup_p.add_subparsers(title="Setup commands", dest="setup_subcommand")
add_db = setup_commands.add_parser("add")
add_db.add_argument("-p", "--path", help="specifies the path. Defaults to local directory")
add_db.add_argument("-y", "--yes", help="Don't ask to overwrite.", action="store_true")
add_db.add_argument("name", help="New configuration name", nargs="*")

import_p = setup_commands.add_parser("import", help="import data from different formats.")
import_p.add_argument("file", help="The file to load.")
import_p.add_argument("-y", "--yes", help="Don't Prompt for adding.", action="store_true")
import_p_mode = import_p.add_mutually_exclusive_group(required=True)
import_p_mode.add_argument("-dlx", "--delicious_library_xml", help="import books from a Delicious Library xml file.", action="store_true")

book_p = commands.add_parser("book", help="Manage Books")
book_commands = book_p.add_subparsers(title="Book Commands", dest="book_subcommand")
add_book = book_commands.add_parser("add", help="Add Books")
add_book.add_argument("isbn", help="book isbn", type=str)
add_book.add_argument("-m", "--manually", help="Enter book details manually.", action="store_true")

manage_book_p = book_commands.add_parser("manage", help="Manage books")
manage_book_p.add_argument("-r", "--remove", help="Remove the selected book", action="store_true")
manage_book_p.add_argument("-n", "--rename", help="Rename the book", metavar="new_name")
manage_book_p.add_argument("-d", "--duplicate", help="Duplicate the book", action="store_true")
manage_book_p.add_argument("isbn", help="The ISBN of the Book", nargs="?", default="USE_FZF")

file_valid = lib.Validation(exclude=["?", "\\", "#", "+", "*", "~", "%", "{", "}", "[", "]", "."])

args = parser.parse_args(argv[1:])

# if args.interactive:
#    pass
# else:
match args.subcommands:
    case "connect":
        if not os.path.isdir(args.path):
            print("The path doesn't point to a valid directory.")
            quit(1)

        if not (os.path.isfile(args.path + "\\profile.tl.json")):
            print("The folder doesn't contain a profile configuration.")
            quit(1)
        
        path_ = path.Path(os.path.realpath(args.path))
        profile_name = path_.name.split(".")[0]

        with open(path_ / "profile.tl.json", "r") as f:
            data = jsn.load(f)

        if data["name"] != profile_name:
            print("The folder's profile config is invalid")
            quit(1)

        try:
            # if not os.path.isfile(path_ / data["rules"]):
            #     print("The folder's profile config is invalid")
            #     quit(1)
            if not os.path.isfile(path_ / data["user_settings"]):
                print("The folder's profile config is invalid")
                quit(1)
        except IndexError:
            print("The folder's profile config is invalid")
            quit(1)

        db_path = path_ / f"{profile_name}.db"

        if not os.path.isfile(db_path):
            print("The folder has no database.")
        
        print("Loaded profile config " + profile_name + ".")

        db = sql.connect(db_path)
        print(f"Connected to database {profile_name}.db.") 

        with open(path.Path(__file__).parent / "config.json", "r") as f:
            config_data = jsn.load(f)
            config_data["active_profile_path"] = path_.as_posix()
            config_data["active_profile_name"] = profile_name

        with open(path.Path(__file__).parent / "config.json", "w") as f: 
            f.write(jsn.dumps(config_data))  
        
        db.commit()
        db.close()
        quit(0)

    case "user":
        match args.user_subcommand:
            case "remove":
                if args.ban != None:
                    print(f"Banned User {args.id_}{" because of " + args.ban if args.ban.strip() != "" else ""}.")

                id_ = " ".join(args.name) if type(args.name) == list else args.name

                db = lib.getDB()
                if db == False: quit(1)

                cur = db.cursor()
                user_ = cur.execute("SELECT * FROM users WHERE name=? OR id=?", (id_, id_))
                user = user_.fetchall()

                if not user:
                    print("No user found with that name or id.")
                    db.close()
                    quit(1)

                cur.execute("DELETE FROM users WHERE name=? OR id=?;", (id_,id_,))
                cur.execute("DELETE FROM borrows WHERE borrower_id=?;", (id_,))

                print(f"Deleted user '{user[0][2]}'.")

                db.commit()
                db.close()
                quit(0)

            case "add":
                validation_result = file_valid.validate(args.name)

                if not (validation_result[0]):
                    print(f"Character '{validation_result[1]}' is not allowed in usernames.")
                    quit(1)

                name = " ".join(args.name) if type(args.name) == list else args.name
                if name == '': 
                    add_user.print_help()
                    quit(0)
                print(f"Adding user '{name}'.")

                db = lib.getDB()
                if db == False: quit(1)
                cur = db.cursor()

                try:
                    res = cur.execute(f"INSERT INTO users VALUES(NULL, ?, ?, 0);", (str(dt.now().date()), name))
                except sql.IntegrityError:
                    print("There is already a user with that name.")
                    print("Failed")
                    quit(1)

                db.commit()

                print(f"Added user '{name}' with id {db.execute(f"SELECT * FROM users WHERE name=?", (name,)).fetchone()[0]}.")

                db.close()
                quit(0)
            
            case "query":
                db = lib.getDB()
                query = "SELECT * FROM users"
                cols = ["ID", "Creation Date", "Name", "User State"]

                if args.delayed:
                    query = "SELECT u.* FROM borrows b JOIN users u ON b.borrower_id = u.id WHERE delayed=1"

                if args.empty:
                    query = "SELECT * FROM users u WHERE NOT EXISTS ( SELECT 1 FROM borrows b WHERE b.borrower_id = u.id);"

                if args.borrowed:
                    query = "SELECT u.* FROM users u JOIN borrows b ON b.borrower_id = u.id WHERE b.borrower_id = u.id"

                if args.active:
                    query = "SELECT * FROM users WHERE state = " + str(UserStates.Active)

                if args.inactive:
                    query = "SELECT * FROM users WHERE state = " + str(UserStates.Inactive)

                if args.banned:
                    query = "SELECT * FROM users WHERE state = " + str(UserStates.Banned)
                    
                db = lib.getDB()

                if not db:
                    quit(1)

                cur = db.cursor()
                res = cur.execute(query)
                data = res.fetchall()
                lib.table(cols, data, 20)

                if args.export_csv:
                    with open(args.export_csv, "w") as f:
                        writer = csv.DictWriter(f, cols)
                        for i in data:
                            writer.writerow()

                if args.export_json:
                    with open(args.export_json, "w") as f:
                        jsn.dump([map(lambda x: i[cols[i.index(x)]], i) for i in data], f)

                if args.export_txt:
                    with open(args.export_txt, "w") as f:
                        string = ""
                        for i in data:
                            string += f"""
User '{i[2]}'
------------------
ID: {i[0]}
created at: {i[1]}
State: {i[3]}
"""
                        f.write(string)

                quit(0)

            case _:
                user_commands.print_help()

    case "borrow":
        db = lib.getDB()
        
        if not db:
            quit(1)

        cur = db.cursor()

        config = lib.getProfileSettings()
        max_delayed_books = config["maxDelayedBook"]
        max_books = config["maxBooks"]

        books_ = cur.execute("SELECT * FROM books bo LEFT JOIN borrows br ON bo.id=br.book_id")
        books = books_.fetchall()

        name = " ".join(args.name) if type(args.name) == list else args.name

        user_res = cur.execute("SELECT * FROM users WHERE name=? OR id=?", (name, name))
        user = user_res.fetchone()

        if user == "":
            borrow_p.print_help()
            quit(0)

        match lib.checkUserCanBorrow(name, db):
            case True:
                pass

            case codes.Borrowing.UserBanned:
                print("User can't borrow because of being banned.")
                quit(0)

            case codes.Borrowing.UserDelayedBook:
                print(f"The user has more than {max_delayed_books} delayed book{lib.plOrSg(max_delayed_books, "", "s")}.")
                quit(0)

            case codes.Borrowing.UserTooManyBooks:
                print(f"The user has borrowed more than {max_books} book{lib.plOrSg(max_books, "", "s")}.")
                quit(0)
            
            case codes.Borrowing.NoBooksInSystem:
                print(f"There are no books in the system.")
                quit(0)

        print(f"Borrowing book to '{user[2]}'")

        book = lib.fzf_book(books)

        match book[0]:
            case codes.BooksFinder.BookNotFound:
                print("Book not found. Aborting.")
                quit(0)
            case codes.BooksFinder.BorrowedBookSelected:
                print("The selected book is already borrowed.")
                quit(0)
            case codes.BooksFinder.NoBookSelected:
                print("No book selected.")
                quit(0)

        book = book[0]
        book_id = book[0]

        try: 
            print(f"Selected Book '{book[2]}'. The book has to be returned the {(dt.now() + td(lib.getProfileSettings()["borrowingDuration"])).date().strftime("%d.%m.%Y")}.")
            cur.execute("INSERT INTO borrows VALUES(NULL, ?, ?, ?, ?, 0)", (str(dt.now().date()), book_id, user[0], str((dt.now() + td(lib.getProfileSettings()["borrowingDuration"])).date())))
            res = cur.execute("UPDATE books SET borrowed_by=?, borrowed_at=? WHERE id=?", (user[0], str(dt.now().date()), book_id))
        except Exception as e:
            print("There was an error with the settings.yml file of the selected profile.")
            print(e)
            quit(1)
        
        
        print(f"Borrowed book '{book[2]}' to '{user[2]}'")
        db.commit()

    case "return":
        db = lib.getDB()
        cur = db.cursor()

        borrow = None

        if args.borrow_id:
            borrow_id = " ".join(args.borrow_id)
            loan = cur.execute("SELECT * FROM borrows b JOIN users u ON u.id = b.borrower_id WHERE b.id=?", (borrow_id))
            borrow = loan.fetchone()
            

        if args.username or args.userid:
            loans = []
            if args.username:
                loans = cur.execute("SELECT * FROM ( SELECT * FROM borrows bb LEFT JOIN users u ON u.id = bb.borrower_id WHERE u.name=? ) b LEFT JOIN books bb ON b.book_id=bb.id", (" ".join(args.username),))
            elif args.userid:
                loans = cur.execute("SELECT * FROM ( SELECT * FROM borrows bb LEFT JOIN users u ON u.id = bb.borrower_id WHERE u.id=? ) b LEFT JOIN books bb ON b.book_id=bb.id", (" ".join(args.userid),))

            if not loans:
                quit(0)
            loan = loans.fetchall()
            if not loan or len(loan) == 0: 
                print("No loans matching the search criteria were found.")
                quit(1)

            keys = {
                "loan ID":7,
                "Book ID":7,
                "Book Title": 60,
                "User": 30,
                "Due": 10
            }
            loan_ = [[i[0], i[2], i[12], i[8], i[4]] for i in loan]
            idx = lib.fzf(keys, loan_)

            if idx == None:
                print("No loan selected.")
                quit(0)
            
            borrow = loan[idx]
        
            book_id = borrow[2]
            book_ = cur.execute("SELECT * FROM books WHERE id=?", (book_id, ))
            book = book_.fetchone()

        else:
            return_p.print_help()
            quit(0)

        
        if not borrow:
            print(f"There is no loan with the id '{args.borrow_id}'.")
            quit(1)
        
        book_id = borrow[2]
        book_ = cur.execute("SELECT * FROM books WHERE id=?", (book_id,))
        book = book_.fetchone()

        conf = lib.confirm(f"""
User: {borrow[8]}
Book: '{book[2]}' by '{book[5]}' (ISBN: {book[3]}, ID: {book[0]})
Due: {dt.fromisoformat(borrow[1]).strftime("%d.%m.%Y")}
Is this information correct? """)
        if conf:
            cur.execute("DELETE FROM borrows WHERE id=?", (borrow[0],))
            cur.execute("UPDATE books SET borrowed_by=NULL, borrowed_at=NULL WHERE id=?", (book[0],))
            print(f"Returned book '{book[2]}'.")
        
            db.commit()
            db.close()
            quit(0)
        
        print("Aborted.")
        quit(0)
    
    case "book":
        match args.book_subcommand:
            case "add":
                db = lib.getDB()
                if not db:
                    quit(1)
                cur = db.cursor()
                if not args.manually:
                    req = urllib.request.Request(BOOKS_API_BASE_LINK(str(args.isbn)))   
                    req.add_header("User-Agent", "TastyLibrary/1.0 (docSchneggo@outlook.com)") 
                    text = urllib.request.urlopen(req).read()
                    decoded_text = text.decode("utf-8")
                    obj = dict(jsn.loads(decoded_text))
                    try:
                        volume_info = obj["records"][list(obj["records"].keys())[0]]["data"]
                        authors = ", ".join([i["name"] for i in volume_info["authors"]])
                        title = volume_info["title"] + " - " + volume_info["subtitle"]
                        details = obj["records"][list(obj["records"].keys())[0]]["details"]["details"]
                        try:
                            desc = details["description"]
                        except KeyError:
                            desc = "< NO DESCRIPTION AVAILABLE >"
                        
                        if args.yes or lib.confirm_book(title, authors, desc, args.isbn):
                            res = cur.execute("INSERT INTO books VALUES(NULL, ?, ?, ?, ?, ?, NULL, NULL)", (str(dt.now().date()), title, i, desc, authors))
                            db.commit()
                            print(f"Added book '{title}' to database")
                        
                    except KeyError:
                        print("No Book found with ISBN '" + str(args.isbn) + "'.")
                
                else:
                    print("Please enter the book data manually.")
                    title = input("Title: ")
                    authors = input("Author/s (seperated by ', '): ")
                    desc = input("Description (you can leave it empty): ")
                    isbn = input("ISBN (if present): ")
                    desc = "< NO DESCRIPTION AVAILABLE >" if not desc else desc
                    
                if lib.confirm_book(title, authors, desc, isbn):

                    res = cur.execute("INSERT INTO books VALUES(NULL, ?, ?, ?, ?, ?, NULL, NULL)", (str(dt.now().date()), title, args.isbn, desc, authors))
                    db.commit()
                    db.close()
                    print(f"Added book '{title}' to database")

            case "manage":
                db = lib.getDB()
                if not db:
                    quit(1)
                
                cur = db.cursor()

                book = ()

                if args.isbn == "USE_FZF":
                    books_ = cur.execute("SELECT * FROM books")

                    books = books_.fetchall()

                    book_idx = lib.fzf_book(books)

                    match book_idx[0]:
                        case codes.BooksFinder.NoBookSelected:
                            print("No book selected. Aborting.")
                            db.commit()
                            db.close()
                            quit(0)
                        
                        case codes.BooksFinder.BorrowedBookSelected:
                            book = book_idx[1]

                        case codes.BooksFinder.BookNotFound:
                            print("The book was not found.")
                            db.commit()
                            db.close()
                            quit(1)

                        case _:
                            book = book_idx[0]
                    
                
                if lib.confirm_book(book[2], book[5], book[4], book[3]):
                    title = book[2]
                    if args.remove :

                        if lib.confirm("Delete '" + book[2] + "'? "): 
                            cur.execute("DELETE FROM books WHERE id=?", (book[0], ))
                            print(f"Deleted '{book[2]}' (ID: {book[0]})")
                            db.commit()
                            db.close()
                            quit(0)
                        else: 
                            print("Aborting.")
                            db.commit()
                            db.close()
                            quit(0)
                    
                    if args.rename:
                        if lib.confirm(f"Rename the book '{book[2]}' to '{args.rename}'? "):
                            cur.execute("UPDATE books SET title=? WHERE id=? ", (args.rename, book[0], ))
                            print(f"Renamed '{book[2]}' to '{args.rename}'.")
                            title = args.rename
                        else:
                            print("Aborting.")
                            quit(0)
                    
                    if args.duplicate:
                        if lib.confirm(f"Duplicate '{title}'? "):
                            cur.execute("INSERT INTO books VALUES (NULL, ?, ?, ?, ?, ?, ?, 'now')", tuple(book[1:-1]))
                            db.commit()

                            book_id_ = cur.execute("SELECT id FROM books WHERE borrowed_at='now'")
                            book_id = book_id_.fetchone()
                            cur.execute("UPDATE books SET borrowed_at=NULL WHERE borrowed_at='now'")
                            print(f"Duplicated '{book[2]}'. The new book has the id {book_id}")
                    
                    db.commit()
                    db.close()
                    quit(0)
            case _:
                book_p.print_help()

    case "setup":
        match args.setup_subcommand:
            case "add":
                validation_result = file_valid.validate(" ".join(args.name))
                if not validation_result[0]:
                    print(f"Character '{validation_result[1]}' is not allowed in the name")
                    quit(1)
                name = " ".join(args.name)
                print(f"Adding configuration with name '{name}'")
                try:
                    os.mkdir(f"{" ".join(args.name)}.tl")
                except:
                    print("A configuration with that name already exists in the local folder.")
                    quit(1)
                open(path.Path(f"{" ".join(args.name)}.tl") / " ".join(args.name) + ".db", "w").close()
                db = sql.connect(f"{" ".join(args.name)}.tl\\{" ".join(args.name)}.db")
                db.executescript(lib.SQL_CREATE_TABLES)
                db.commit()
                db.close()
                with open(f"{" ".join(args.name)}.tl\\profile.tl.json", "wb") as f:
                    f.write(jsn.dumps(prs.emptyProfile(" ".join(args.name))).encode())
                with open(f"{" ".join(args.name)}.tl\\settings.yml", "w") as f:
                    f.write(yml.dump(prs.emptySettings(), Dumper=yml.Dumper))
                
                quit(0)
            
            case "import":
                db = lib.getDB()
                if not db:
                    quit(1)
                cur = db.cursor()
                if args.file:
                    xml = DeliciousXML(args.file)
                    failed = []
                    
                    for i in xml.isbns:
                        req = urllib.request.Request(BOOKS_API_BASE_LINK(str(i)))   
                        req.add_header("User-Agent", "TastyLibrary/1.0 (docSchneggo@outlook.com)") 
                        text = urllib.request.urlopen(req).read()
                        decoded_text = text.decode("utf-8")
                        obj = dict(jsn.loads(decoded_text))
                        try:
                            volume_info = obj["records"][list(obj["records"].keys())[0]]["data"]
                            authors = ", ".join([i["name"] for i in volume_info["authors"]])
                            title = volume_info["title"] + " - " + volume_info["subtitle"]
                            details = obj["records"][list(obj["records"].keys())[0]]["details"]["details"]
                            try:
                                desc = details["description"]["value"] if type(details["description"]) == dict else details["description"]
                            except:
                                desc = "< NO DESCRIPTION AVAILABLE >"
                            
                            if args.yes or lib.confirm_book(title, authors, desc, i):
                                print(desc)
                                res = cur.execute("INSERT INTO books VALUES(NULL, ?, ?, ?, ?, ?, NULL, NULL)", (str(dt.now().date()), title, i, desc, authors))
                                db.commit()
                                print(f"Added book '{title}' to database")
                            
                        except KeyError:
                            print("No Book found with ISBN '" + str(i) + "'.")
                            failed.append(i)
                        
                        sleep(3)

                    print("Failed Books: \n- " + "\n- ".join(failed)) if failed else None
                    
                    db.close()

                    quit(0)
            
        setup_p.print_help()

    case _:
        parser.print_help()