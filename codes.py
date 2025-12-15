class Borrowing:
    UserBanned = 0
    UserDelayedBook = 1
    UserTooManyBooks = 2
    NoBooksInSystem = 3

class BooksFinder:
    BookNotFound = -404
    NoBookSelected = -10
    BorrowedBookSelected = -11