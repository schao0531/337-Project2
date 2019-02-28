'''Version 0.1'''
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

#https://thewoksoflife.com/2018/08/peach-daiquiris-frozen/
def autograder(url):
    '''Accepts the URL for a recipe, and returns a dictionary of the
    parsed results in the correct format. See project sheet for
    details on correct format.'''
    # your code here
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    r = urlopen(req).read()
    soup = BeautifulSoup(r, "html.parser")
    print(soup.prettify())
    #return results

def main():
    url = str(input("What recipe would you like to read?: ")).strip()
    autograder(url)

if __name__ == '__main__':
    main()
