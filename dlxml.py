from xml.etree.ElementTree import ElementTree as _ETree
from pathlib import Path as _Path
from sys import argv as _argv

class DeliciousXML:
    def __init__(self, filepath: str):
        with open(filepath) as f:
            self.etree = _ETree(file=f)
        self.root = self.etree.getroot()

        self.isbns = []
        self.books = []
        for i in self.root:
            for j in i:
                book = {}
                for k in j:
                    if k.tag == "key":
                        book[k.text] = j[list(j).index(k)+1].text
                        j.remove(j[list(j).index(k)+1])
                self.books.append(book)
                self.isbns.append(book["isbn"]) if book["isbn"] else ""
    
    def getBooks(self):
        return self.books




if __name__ == "__main__":
    xml = DeliciousXML(_argv[1])
    print(len(xml.isbns))

