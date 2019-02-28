'''Version 0.1'''
from bs4 import BeautifulSoup
from requests import get

#https://thewoksoflife.com/2018/08/peach-daiquiris-frozen/

def autograder(url):
    '''Accepts the URL for a recipe, and returns a dictionary of the
    parsed results in the correct format. See project sheet for
    details on correct format.'''
    # your code here
#    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
#    r = urlopen(req).read()
#    soup = BeautifulSoup(r, "html.parser")
#    print(soup.prettify())
    #return results

def get_raw_html(url):
    try:
        raw_html = get(url,stream=True)
        if raw_html.status_code == 200:
            html = BeautifulSoup(raw_html.content, 'html.parser')
            return html
        else:
            print(raw_html.status_code)
            sys.exit()
    except:
        print("URL ", url, " not recognized!")


####################################################################################################################################
# INGREDIENT STUFF
####################################################################################################################################

def grab_ingredients(url):
    html = get_raw_html(url)
    items = []
    for line in html.select('label'):
        #         print(line)
        line = str(line)
        if "{true: 'checkList__item'}" in line:
            segments = line.split('"')
            items.append(segments[3])
    return items[:-1]

def ingredient_parser(string):
    words = string.split(' ')
    
    # Quantity
    quantity = [words[0]]
    words = words[1:]
    
    # Measurement
    if '(' in words[0]:
        measurement = ' '.join(words[:3])
        measurement = measurement.replace("(","").replace(")","")
        measurement = [measurement]
        words = words[3:]
    else:
        measurement = [words[0]]
        words = words[1:]

    name = [' '.join(words)]

    descriptor = []
    preparation = []
    prep_description = []
    Max = []

    return {"name":name,
            "quantity":quantity,
            "measurement":measurement,
            "descriptor":descriptor,
            "preparation":preparation,
            "prep_description":prep_description,
            "max":Max
            }

def ingredient_dict(string_list):
    ingredient_list = []
    for ingredient in string_list:
        ingredient_list.append(ingredient_parser(ingredient))
    return ingredient_list


####################################################################################################################################
# PREP STUFF
####################################################################################################################################

def grab_steps(url):
    html = get_raw_html(url)
    items = []
    for line in html.select('span'):
        #         print(line)
        line = str(line)
        if "recipe-directions__list--item" in line:
            segments = line.split('>')
            items.append(segments[1].split('\n')[0])
    return items[:-1]


def main():
    url = str(input("What recipe would you like to read?: ")).strip()
    autograder(url)

if __name__ == '__main__':
    main()
