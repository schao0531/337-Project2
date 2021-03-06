'''Version 0.1'''
from bs4 import BeautifulSoup
from requests import get
import re
import json
global results
from pprint import pprint
import pdb

resdict = {}
#https://www.allrecipes.com/recipe/80827/easy-garlic-broiled-chicken/
def autograder(url):
    '''Accepts the URL for a recipe, and returns a dictionary of the
    parsed results in the correct format. See project sheet for
    details on correct format.'''
    # your code here
#    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
#    r = urlopen(req).read()
#    soup = BeautifulSoup(r, "html.parser")
#    print(soup.prettify())

    ingredient_dict(grab_ingredients(url))
    get_tools(url)
    get_structuredsteps(url)
    pprint(resdict)
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
    #pdb.set_trace()
    #soup = BeautifulSoup(html, "html.parser")
    items = []
    for line in html.select('label'):
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
    resdict["ingredients"] = ingredient_list
    return ingredient_list


####################################################################################################################################
# PREP STUFF
####################################################################################################################################

def grab_steps(url):
    html = get_raw_html(url)
    steps = []
    for line in html.select('span'):
        #         print(line)
        line = str(line)
        if "recipe-directions__list--item" in line:
            #pdb.set_trace()
            segments = line.split('>')
            steps.append(segments[1].split('\n')[0])
    return steps[:-1]


####################################################################################################################################
# TOOLS STUFF
####################################################################################################################################

def get_tools(url):
    steps = grab_steps(url)
    cooking_tools = []
    implied_tools = []
    official_tools = {}
    with open('tools.json') as f:
        official_tools = json.load(f)

    for s in steps:
        line = s.lower().strip()
        line = re.sub(r'[^\w\s]','',line)
        for t in official_tools:
            if t in line:
                cooking_tools.append(t)
            elif official_tools[t]:
                for w in official_tools[t]:
                    if w in line:
                        implied_tools.append(t)

    resdict["cooking tools"] = list(set(cooking_tools))
    resdict["implied cooking tools"] = list(set(implied_tools))
    return list(set(cooking_tools)), list(set(implied_tools))



####################################################################################################################################
# STEPS STUFF
####################################################################################################################################
def get_structuredsteps(url):
    steps = grab_steps(url)
    joined = " ".join(steps)
    structured_steps = joined.split(".")

    resdict["structured steps"] = []

    time_units = ['sec', 'sec.', 'seconds', 'second' 'min', 'min.', 'minutes', 'minute', 'hour', 'hours', 'hr', 'hrs', 'hr.', 'hrs.']

    stop_words = ["and", "with", "the", "to"]

    ingredient_names = [x["name"][0] for x in resdict["ingredients"]]
    cooking_tools = [y for y in resdict["cooking tools"]]
    cooking_tools.extend([z for z in resdict["implied cooking tools"]])
    #some line for extracted methods
    #print(ingredient_names)
    #print(cooking_tools)
    for s in structured_steps:
        if s != "":
            ingredient_list = []
            for i in ingredient_names:
                for y in i.split():
                    if y not in stop_words and y in s:
                        ingredient_list.append(i)

            tools_list = [t for t in cooking_tools if t in s]

            #some line for methods

            cooking_time = ""
            tokens = s.split(" ")
            for x in range(len(tokens) - 2):
                if tokens[x].isdigit() and tokens[x + 1] in time_units:
                    cooking_time = tokens[x] + ' ' + tokens[x + 1]

            step = {
                "step": s,
                "ingredients": list(set(ingredient_list)),
                "tools": list(set(tools_list)),
                "cooking time": cooking_time
            }

            resdict["structured steps"].append(step)
    return resdict["structured steps"]

####################################################################################################################################
# TRANSFORMATIONS
####################################################################################################################################
def vegetarian(resdict):
    print("")

def main():
    #url = str(input("What recipe would you like to read?: ")).strip()
    url = "http://allrecipes.com/Recipe/Baked-Lemon-Chicken-with-Mushroom-Sauce/"
    autograder(url)

    #user loop
    # outer_loop = 1
    # while outer_loop == 1:
    #     url = str(input("What recipe would you like to read?: ")).strip()
    #     inner_loop = 1
    #     autograder(url)
    #     while inner_loop == 1:
    #         print("What do you want to do?")
    #         print ("\n1. Ingredients \n2. Cooking Tools\n3. Cooking Methods\n4. Steps\n5. Transform")
    #         user_input = str(input("Choose an option: ")).strip()
    #         if user_input == "1":
    #             pprint(resdict["ingredients"])
    #         elif user_input == "2":
    #             pprint(resdict["cooking tools"])
    #             pprint(resdict["implied cooking tools"])
    #         elif user_input == "3":
    #             print("Not implemented.")
    #         elif user_input == "4":
    #             pprint(resdict["structured steps"])
    #         elif user_input == "5":
    #             print("Not implemented")
    #         else:
    #             print("Invalid input.")
    #
    #         cont = input("Continue with this current recipe? y/n: ")
    #         if cont.lower() == 'y':
    #                 continue
    #         elif cont.lower() == 'n':
    #             inner_loop = -1
    #             break
    #         else:
    #             print("Invalid input.")
    #     exit = input("Exit program? y/n: ")
    #     if exit.lower() == "y":
    #         outer_loop = -1
    #         break
    #     else:
    #         continue


if __name__ == '__main__':
    main()
