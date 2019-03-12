"""Version 0.3"""
from bs4 import BeautifulSoup
from requests import get
import re
import json
global results
from pprint import pprint
import pdb
import nltk
nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords
import copy

resdict = {}


##########################################################################################################
# GENERAL
##########################################################################################################

def get_raw_html(url):
    try:
        raw_html = get(url, stream=True)
        if raw_html.status_code == 200:
            html = BeautifulSoup(raw_html.content, 'html.parser')
            return html
        else:
            print(raw_html.status_code)
            sys.exit()
    except:
        print("URL ", url, " not recognized!")


def get_title(url):
    url_list = url.split('/')
    if len(url_list[-1])==0:
        title = url_list[-2]
    else:
        title = url_list[-1]
    title_list = title.split('-')
    title = ' '.join(title_list)
    resdict["title"] = title
    return

##########################################################################################################
# INGREDIENTS
##########################################################################################################

def ingredients_from_url(url):
    html = get_raw_html(url)
    # pdb.set_trace()
    # soup = BeautifulSoup(html, "html.parser")
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
    if words[0][0].isnumeric() and words[1][0].isnumeric():
        quantity = [' '.join(words[:2])]
        words = words[2:]
    elif words[0][0].isnumeric():
        quantity = [words[0]]
        words = words[1:]
    else:
        quantity = ['unspecified']

    # Measurement
    measurement_units = [line.split('\n')[0] for line in open('measurement_units.txt', 'r').readlines()]
    if '(' in words[0]:
        measurement = ' '.join(words[:3])
        measurement = measurement.replace("(", "").replace(")", "")
        measurement = [measurement]
        words = words[3:]
    else:
        measurement = [word for word in words if word in measurement_units]
        if len(measurement) == 0 and ('to taste' in ' '.join(words) or 'for flavor' in ' '.join(words) or
                                      'as needed' in ' '.join(words)):
            measurement=['to taste']
            words = ' '.join(words).replace('to taste', '').replace('for flavor', '').replace('as needed', '')
            words = words.split(' ')
        elif len(measurement) == 0:
            measurement = ['unspecified']
        words = [word for word in words if word not in measurement_units]

    descriptor_terms = [line.split('\n')[0] for line in open('descriptor_terms.txt', 'r').readlines()]
    descriptors = [word for word in words if word in descriptor_terms]
    if len(descriptors) == 0:
        descriptors=['unspecified']
    words = [word for word in words if word not in descriptor_terms]

    preparation = []
    prep_description = []
    Max = []

    if 'and' in words:
        ingredient1 = words[:words.index('and')]
        ingredient1 = ingredient1 if isinstance(ingredient1, str) else ' '.join(ingredient1)
        ingredient2 = words[words.index('and')+1:]
        ingredient2 = ingredient2 if isinstance(ingredient2, str) else ' '.join(ingredient2)
        name = [ingredient1.replace(',', ''), ingredient2.replace(',', '')]
    else:
        name = [' '.join(words).replace(',', '')]

    return {"name": name,
            "quantity": quantity,
            "measurement": measurement,
            "descriptor": descriptors,
            "preparation": preparation,
            "prep_description": prep_description,
            "max": Max,
            "full_string": string
            }


def get_ingredients(url):
    ingredient_list = ingredients_from_url(url)
    ingredient_data = []
    for ingredient in ingredient_list:
        ingredient_data.append(ingredient_parser(ingredient))
    resdict["ingredients"] = ingredient_data

##########################################################################################################
# TOOLS & METHODS
##########################################################################################################

def get_tools(url):
    steps = grab_steps(url)
    cooking_tools = []
    implied_tools = []
    with open('tools.json') as f:
        official_tools = json.load(f)

    for s in steps:
        line = s.lower().strip()
        line = re.sub(r'[^\w\s]', '', line)
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


def get_methods(url):
    steps = grab_steps(url)
    cooking_methods = []
    with open('methods.json') as f:
        official_methods = json.load(f)

    for s in steps:
        line = s.lower().strip()
        line = re.sub(r'[^\w\s]', '', line)
        for m in official_methods:
            if m in line:
                cooking_methods.append(m)
            elif official_methods[m]:
                for w in official_methods[m]:
                    if w in line:
                        cooking_methods.append(m)

    resdict["cooking methods"] = list(set(cooking_methods))

##########################################################################################################
# STEPS/INSTRUCTIONS
##########################################################################################################


def grab_steps(url):
    html = get_raw_html(url)
    steps = []
    for line in html.select('span'):
        #         print(line)
        line = str(line)
        if "recipe-directions__list--item" in line:
            # pdb.set_trace()
            segments = line.split('>')
            steps.append(segments[1].split('\n')[0])
    return steps[:-1]


def get_structured_steps(url):
    steps = grab_steps(url)
    joined = " ".join(steps)
    structured_steps = joined.split(".")

    resdict["structured steps"] = []

    time_units = ['sec', 'sec.', 'seconds', 'second' 'min', 'min.', 'minutes', 'minute', 'hour', 'hours',
                  'hr', 'hrs', 'hr.', 'hrs.']

    stop_words = list(stopwords.words('english'))

    ingredient_dicts = [ingredient_dict for ingredient_dict in resdict["ingredients"]]
    ingredient_lists = [ingredient_dict['name'] for ingredient_dict in ingredient_dicts]
    ingredient_names = [inner for outer in ingredient_lists for inner in outer]
    cooking_tools = [y for y in resdict["cooking tools"]]
    cooking_tools.extend([z for z in resdict["implied cooking tools"]])
    methods = {}

    with open('methods.json') as f:
        official_methods = json.load(f)

    for m in resdict["cooking methods"]:
        methods[m] = official_methods[m]

    for s in structured_steps:
        l_s = s.lower().strip()

        if l_s != "":
            ingredient_list = []
            for i in ingredient_names:
                for y in i.split():
                    if y not in stop_words and y in l_s:
                        if "broth" in i and "broth" not in l_s:
                            continue
                        ingredient_list.append(i)

            if len(ingredient_list) == 0:
                ingredient_list = ['none']

            tools_list = [t for t in cooking_tools if t in l_s]
            if len(tools_list) == 0:
                tools_list = ['unspecified']

            methods_list = []
            for m in methods.keys():
                if m in l_s:
                    methods_list.append(m)
                elif methods[m]:
                    for im in methods[m]:
                        if im in l_s and im not in " ".join(tools_list):
                            # print(im)
                            methods_list.append(m)
            if len(methods_list) == 0:
                methods_list = ['unspecified']

            cooking_time = ""
            tokens = l_s.split(" ")
            for x in range(len(tokens) - 1):
                if tokens[x].isdigit() and tokens[x + 1] in time_units:
                    cooking_time = [tokens[x] + ' ' + tokens[x + 1]]
            if len(cooking_time) == 0:
                cooking_time = ['unspecified']

            step = {
                "step": s.strip(),
                "ingredients": list(set(ingredient_list)),
                "tools": list(set(tools_list)),
                "cooking time": cooking_time,
                "methods": methods_list
            }

            resdict["structured steps"].append(step)


##########################################################################################################
# TRANSFORMATIONS
##########################################################################################################

def replace_ingredients(resdict_alt, ingredient_dict):
    for item in ingredient_dict.keys():
        resdict_alt['title'] = resdict_alt['title'].lower().replace(item,ingredient_dict[item]).title()
        for ingredient in resdict_alt['ingredients']:
            ingredient['full_string'] = ingredient['full_string'].lower().replace(item,ingredient_dict[item]).capitalize()
            ingredient['name'] = [name.lower().replace(item,ingredient_dict[item]) for name in ingredient['name']]
        for step in resdict_alt['structured steps']:
            step['step'] = step['step'].lower().replace(item,ingredient_dict[item]).capitalize()
            step['ingredients'] = [name.lower().replace(item,ingredient_dict[item]) for name in step['ingredients']]
    return resdict_alt


def replace_tools(resdict_alt, tool_dict):
    for old_tool in tool_dict.keys():
        resdict_alt['cooking tools'] = [tool.lower().replace(old_tool, tool_dict[old_tool])
                                        for tool in resdict_alt['cooking tools']]
        resdict_alt['implied cooking tools'] = [tool.lower().replace(old_tool, tool_dict[old_tool])
                                                for tool in resdict_alt['implied cooking tools']]
        for step in resdict_alt['structured steps']:
            step['step'] = step['step'].lower().replace(old_tool, tool_dict[old_tool]).capitalize()
            step['tools'] = [tool.lower().replace(old_tool, tool_dict[old_tool]) for tool in step['tools']]
    return resdict_alt


def replace_methods(resdict_alt, method_dict):
    for old_method in method_dict.keys():
        resdict_alt['cooking methods'] = [method.lower().replace(old_method, method_dict[old_method])
                                          for method in resdict_alt['cooking methods']]
        for step in resdict_alt['structured steps']:
            step['step'] = step['step'].lower().replace(old_method, method_dict[old_method]).capitalize()
            step['methods'] = [method.lower().replace(old_method, method_dict[old_method])
                               for method in step['methods']]
    return resdict_alt


def universal_transformation(ingredient_dict={}, tool_dict={}, method_dict={}):
    resdict_alt = copy.deepcopy(resdict)
    if ingredient_dict != {}:
        resdict_alt = replace_ingredients(resdict_alt, ingredient_dict)
    if tool_dict != {}:
        resdict_alt = replace_tools(resdict_alt, tool_dict)
    if method_dict != {}:
        resdict_alt = replace_methods(resdict_alt, method_dict)
    return resdict_alt


def vegetarian_style():
    with open('to_vegetarian.json') as f:
        transformation_dict = json.load(f)
    return universal_transformation(ingredient_dict=transformation_dict['ingredients'])


def meatlover_style():
    with open('to_meatlover.json') as f:
        transformation_dict = json.load(f)
    return universal_transformation(ingredient_dict=transformation_dict['ingredients'])


def southern_style():
    with open('to_southern.json') as f:
        transformation_dict = json.load(f)
    southern_dict = universal_transformation(ingredient_dict=transformation_dict['ingredients'],
                                             tool_dict=transformation_dict['tools'],
                                             method_dict=transformation_dict['methods'])
    for ingredient in southern_dict['ingredients']:
        if ingredient['quantity'][0][0].isnumeric():
            ingredient['quantity'] = str(2 * int(ingredient['quantity'][0][0])) + ingredient['quantity'][0][1:]
    return southern_dict

def korean_style():
    with open('to_korean.json') as f:
        transformation_dict = json.load(f)
    korean_dict = universal_transformation(ingredient_dict=transformation_dict['ingredients'],
                                             tool_dict=transformation_dict['tools'],
                                             method_dict=transformation_dict['methods'])
    for ingredient in korean_dict['ingredients']:
        if ingredient['quantity'][0][0].isnumeric():
            ingredient['quantity'] = str(2 * int(ingredient['quantity'][0][0])) + ingredient['quantity'][0][1:]
    return korean_dict


# def vegetarian(transform_type):
#     transformed_rec = copy.deepcopy(resdict)
#     with open('vegetarian.json') as f:
#         official_veg_transform = json.load(f)

#     substitutes = official_veg_transform["to veg"] if transform_type == "to veg" else official_veg_transform["from veg"]

#     new_title = transformed_rec['title']
#     for word in transformed_rec['title'].split():
#         lowered = word.lower()
#         if lowered in substitutes:
#             new_title = new_title.replace(word, substitutes[lowered][0].capitalize())
#     transformed_rec['title'] = new_title

#     new_ingredients = transformed_rec["ingredients"]
#     mapping = {}

#     for i in new_ingredients:
#         orig = i["name"][0].lower().strip()
#         orig = re.sub(r'[^\w\s]', '', orig)
#         for w in orig.split():
#             if w in list(substitutes.keys()):
#                 if "broth" in orig and w != "broth":
#                     continue
#                 else:
#                     mapping[i["name"][0]] = substitutes[w][0]
#                     i["name"] = []
#                     i["name"].append(substitutes[w][0])

#         new_full_string = i['full_string']
#         for word in i["full_string"].split():
#             if word in substitutes:
#                 new_full_string = new_full_string.replace(word, substitutes[word][0])
#         i["full_string"] = new_full_string

#     new_steps = transformed_rec["structured steps"]
#     for s in new_steps:
#         for m in mapping.keys():
#             if m in s["ingredients"]:
#                 new_ingredient_list = [x if x != m else mapping[m] for x in s["ingredients"]]
#                 s["ingredients"] = new_ingredient_list

#         new_step = s["step"]
#         for word in s["step"].split():
#             if word in substitutes:
#                 new_step = new_step.replace(word, substitutes[word][0])
#         s["step"] = new_step

#     # pprint(resdict["structured steps"])
#     # pprint(new_steps)
#     return transformed_rec


##########################################################################################################
# PRINT FUNCTIONS
##########################################################################################################

def print_ingredients(res_dict):
    print('-------------------------------')
    print('INGREDIENTS')
    print('------------------------------- \n')

    for ingredient_dict in res_dict['ingredients']:
        print('"'+ingredient_dict['full_string']+'"')
        print('Ingredient: ', ', '.join(ingredient_dict['name']))
        print('Quantity: ', ', '.join(ingredient_dict['quantity']))
        print('Measurement: ', ', '.join(ingredient_dict['measurement']))
        print('Descriptor: ', ', '.join(ingredient_dict['descriptor']))
        print('')


def print_tools(res_dict):
    print('-------------------------------')
    print('TOOLS')
    print('------------------------------- \n')

    print('Named: '+', '.join(res_dict['cooking tools']))
    print('Implied: '+', '.join(res_dict['implied cooking tools']))
    print('')


def print_methods(res_dict):
    print('-------------------------------')
    print('METHODS')
    print('------------------------------- \n')
    print(', '.join(res_dict['cooking methods']))
    print('')


def print_steps(res_dict):
    print('-------------------------------')
    print('INSTRUCTIONS')
    print('------------------------------- \n')
    for i in range(len(res_dict['structured steps'])):
        print('Step ',str(i+1),': ')
        step_dict = res_dict['structured steps'][i]
        print('"'+step_dict['step']+'"')
        print('Relevant Ingredients: '+', '.join(step_dict['ingredients']))
        print('Relevant Tools: '+', '.join(step_dict['tools']))
        print('Relevant Methods: '+', '.join(step_dict['methods']))
        print('Cooking Time: '+', '.join(step_dict['cooking time']))
        print('')


def summary(transformed_resdict):
    """Used for pretty printing transformed recipes"""
    print(transformed_resdict['title'] + ' Recipe: \n')
    print_ingredients(transformed_resdict)
    print_tools(transformed_resdict)
    print_methods(transformed_resdict)
    print_steps(transformed_resdict)

##########################################################################################################
# MAIN
##########################################################################################################

def main():
    # url = "http://allrecipes.com/Recipe/Baked-Lemon-Chicken-with-Mushroom-Sauce/"
    # url = "http://allrecipes.com/recipe/easy-meatloaf/"

    # user loop
    outer_loop = 1
    while outer_loop == 1:
        url = str(input("What recipe would you like to read?: ")).strip()
        inner_loop = 1

        print('loading... \n')
        get_title(url)
        get_ingredients(url)
        get_tools(url)
        get_methods(url)
        get_structured_steps(url)
        print(resdict['title']+' Recipe: \n')
        #print(resdict)

        while inner_loop == 1:
            print("What do you want to do?")
            print ("\n1. Ingredients \n2. Cooking Tools\n3. Cooking Methods\n4. Steps\n5. Transform")
            user_input = str(input("Choose an option: ")).strip()
            print("")

            if user_input == "1":
                print_ingredients(resdict)

            elif user_input == "2":
                print_tools(resdict)

            elif user_input == "3":
                print_methods(resdict)

            elif user_input == "4":
                print_steps(resdict)

            elif user_input == "5":
                print("How do you want to transform the recipe?")
                print("\n1. To vegeratian \n2. To meat-lover \n3. To southern \n4. To Korean")
                transform_type = str(input("Choose an option: ")).strip()
                if transform_type == "1":
                    summary(vegetarian_style())
                elif transform_type == "2":
                    summary(meatlover_style())
                elif transform_type == "3":
                    summary(southern_style())
                elif transform_type == "4":
                    summary(korean_style())
                else:
                    print("Invalid transformation type.")
            else:
                print("Invalid input.")

            cont = input("Continue with this current recipe? y/n: ")
            if cont.lower() == 'y':
                    continue
            elif cont.lower() == 'n':
                inner_loop = -1
                break
            else:
                print("Invalid input.")
        exit = input("Exit program? y/n: ")
        if exit.lower() == "y":
            outer_loop = -1
            break
        else:
            continue


if __name__ == '__main__':
    main()
