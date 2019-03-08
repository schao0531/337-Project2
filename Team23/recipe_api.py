'''Version 0.3'''
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
    print('loading... \n')
    get_ingredients(url)
    get_tools(url)
    get_methods(url)
    get_structuredsteps(url)
    
    print(get_title(url)+' Recipe: \n')

    print('-------------------------------')
    print('INGREDIENTS')
    print('------------------------------- \n')

    for ingredient_dict in resdict['ingredients']:
        print(ingredient_dict['full_string'])
        print('Ingredient: ',', '.join(ingredient_dict['name']))
        print('Quantity: ',', '.join(ingredient_dict['quantity']))
        print('Measurement: ',', '.join(ingredient_dict['measurement']))
        print('Descriptor: ',', '.join(ingredient_dict['descriptor']))
        print('')

    print('-------------------------------')
    print('TOOLS')
    print('------------------------------- \n')
    print('Named: '+', '.join(resdict['cooking tools']))
    print('Implied: '+', '.join(resdict['implied cooking tools']))
    print('')

    print('-------------------------------')
    print('METHODS')
    print('------------------------------- \n')
    print(', '.join(resdict['cooking methods']))
    print('')

    
    print('-------------------------------')
    print('INSTRUCTIONS')
    print('------------------------------- \n')
    for i in range(len(resdict['structured steps'])):
        print('Step ',str(i+1),': ')
        step_dict = resdict['structured steps'][i]
        print(step_dict['step'])
        print('Relevant Ingredients: '+', '.join(step_dict['ingredients']))
        print('Relevant Tools: '+', '.join(step_dict['tools']))
        print('Cooking Time: '+', '.join(step_dict['cooking time']))
        print('')

    return


####################################################################################################################################
# GENERAL STUFF
####################################################################################################################################

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

def get_title(url):
    url_list = url.split('/')
    if len(url_list[-1])==0:
        title = url_list[-2]
    else:
        title = url_list[-1]
    title_list = title.split('-')
    title = ' '.join(title_list)
    return title.title()


####################################################################################################################################
# INGREDIENT STUFF
####################################################################################################################################

def ingredients_from_url(url):
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
        measurement = measurement.replace("(","").replace(")","")
        measurement = [measurement]
        words = words[3:]
    else:
        measurement = [word for word in words if word in measurement_units]                                  
        if len(measurement)==0 and ('to taste' in ' '.join(words) or 'for flavor' in ' '.join(words) or 'as needed' in ' '.join(words)):
            measurement=['to taste']
            words = ' '.join(words).replace('to taste','').replace('for flavor','').replace('as needed','')
            words = words.split(' ')
        elif len(measurement)==0:
            measurement=['unspecified']
        words = [word for word in words if word not in measurement_units]

    descriptor_terms = [line.split('\n')[0] for line in open('descriptor_terms.txt', 'r').readlines()]
    descriptors = [word for word in words if word in descriptor_terms]
    if len(descriptors)==0:
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
        name = [ingredient1.replace(',',''),ingredient2.replace(',','')]
    else:
        name = [' '.join(words).replace(',','')]

    return {"name":name,
            "quantity":quantity,
            "measurement":measurement,
            "descriptor":descriptors,
            "preparation":preparation,
            "prep_description":prep_description,
            "max":Max,
            "full_string":string
            }

def get_ingredients(url):
    ingredient_list = ingredients_from_url(url)
    ingredient_data = []
    for ingredient in ingredient_list:
        ingredient_data.append(ingredient_parser(ingredient))
    resdict["ingredients"] = ingredient_data
    return ingredient_data


####################################################################################################################################
# TOOL & METHOD STUFF
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

def get_methods(url):
    steps = grab_steps(url)
    cooking_methods = []
    official_methods = {}
    with open('methods.json') as f:
        official_methods = json.load(f)

    for s in steps:
        line = s.lower().strip()
        line = re.sub(r'[^\w\s]','',line)
        for m in official_methods:
            if m in line:
                cooking_methods.append(m)
            elif official_methods[m]:
                for w in official_methods[m]:
                    if w in line:
                        cooking_methods.append(m)

    resdict["cooking methods"] = list(set(cooking_methods))
    return list(set(cooking_methods))

####################################################################################################################################
# STEP STUFF
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

def get_structuredsteps(url):
    steps = grab_steps(url)
    joined = " ".join(steps)
    structured_steps = joined.split(".")

    resdict["structured steps"] = []

    time_units = ['sec', 'sec.', 'seconds', 'second' 'min', 'min.', 'minutes', 'minute', 'hour', 'hours', 'hr', 'hrs', 'hr.', 'hrs.']

    stop_words = ["and", "with", "the", "to"]

    ingredient_dicts = [ingredient_dict for ingredient_dict in resdict["ingredients"]]
    ingredient_lists = [ingredient_dict['name'] for ingredient_dict in ingredient_dicts]
    ingredient_names = [inner for outer in ingredient_lists for inner in outer]
    cooking_tools = [y for y in resdict["cooking tools"]]
    cooking_tools.extend([z for z in resdict["implied cooking tools"]])
    #some line for extracted methods
    #print(ingredient_names)
    #print(cooking_tools)

    for s in structured_steps:
        s = s.lstrip()
        if s != "":
            ingredient_list = []
            for i in ingredient_names:
                for y in i.split():
                    if y not in stop_words and y in s:
                        ingredient_list.append(i)
            if len(ingredient_list)==0:
                ingredient_list = ['none']

            tools_list = [t for t in cooking_tools if t in s]
            if len(tools_list)==0:
                tools_list = ['unspecified']

            #some line for methods

            cooking_time = ""
            tokens = s.split(" ")
            for x in range(len(tokens) - 1):
                if tokens[x].isdigit() and tokens[x + 1] in time_units:
                    cooking_time = [tokens[x] + ' ' + tokens[x + 1]]
            if len(cooking_time)==0:
                cooking_time = ['unspecified']
            step = {
                "step": s,
                "ingredients": list(set(ingredient_list)),
                "tools": list(set(tools_list)),
                "cooking time": cooking_time,
            }

            resdict["structured steps"].append(step)


####################################################################################################################################
# MAIN
####################################################################################################################################

def main():
#     url = "http://allrecipes.com/recipe/easy-meatloaf/"
#     url = 'https://www.allrecipes.com/recipe/7453/chocolate-caramel-nut-cake/?internalSource=rotd&referringId=22935&referringContentType=Recipe%20Hub'
#     url = 'https://thewoksoflife.com/2018/08/peach-daiquiris-frozen/'
    url = str(input("What recipe would you like to read?: \n")).strip()
    autograder(url)
    
if __name__ == '__main__':
    main()


# In[125]:


'''Version 0.2'''
from bs4 import BeautifulSoup
from requests import get
import re
import json
global results
from pprint import pprint
import pdb

resdict = {}

def autograder(url):
    '''Accepts the URL for a recipe, and returns a dictionary of the
    parsed results in the correct format. See project sheet for
    details on correct format.'''
    # your code here    
    print('loading... \n')
    get_ingredients(url)
    get_tools(url)
    get_methods(url)
    get_structuredsteps(url)
    return resdict

def pretty_output(url):
    '''Accepts the URL for a recipe, and returns a clear parsed and broken-down recipe with everything the autograder would have asked for.'''
    # your code here
    print('loading... \n')
    get_ingredients(url)
    get_tools(url)
    get_methods(url)
    get_structuredsteps(url)
    
    print(get_title(url)+' Recipe: \n')
    
    print('-------------------------------')
    print('INGREDIENTS')
    print('------------------------------- \n')
    
    for ingredient_dict in resdict['ingredients']:
        print(ingredient_dict['full_string'])
        print('Ingredient: ',', '.join(ingredient_dict['name']))
        print('Quantity: ',', '.join(ingredient_dict['quantity']))
        print('Measurement: ',', '.join(ingredient_dict['measurement']))
        print('Descriptor: ',', '.join(ingredient_dict['descriptor']))
        print('')

    print('-------------------------------')
    print('TOOLS')
    print('------------------------------- \n')
    print('Named: '+', '.join(resdict['cooking tools']))
    print('Implied: '+', '.join(resdict['implied cooking tools']))
    print('')

    print('-------------------------------')
    print('METHODS')
    print('------------------------------- \n')
    print(', '.join(resdict['cooking methods']))
    print('')


    print('-------------------------------')
    print('INSTRUCTIONS')
    print('------------------------------- \n')
    for i in range(len(resdict['structured steps'])):
        print('Step ',str(i+1),': ')
        step_dict = resdict['structured steps'][i]
        print(step_dict['step'])
        print('Relevant Ingredients: '+', '.join(step_dict['ingredients']))
        print('Relevant Tools: '+', '.join(step_dict['tools']))
        print('Relevant Methods: '+', '.join(step_dict['methods']))
        print('Cooking Time: '+', '.join(step_dict['cooking time']))
        print('')

    return


##########################################################################################################
# GENERAL STUFF
##########################################################################################################

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

def get_title(url):
    url_list = url.split('/')
    if len(url_list[-1])==0:
        title = url_list[-2]
    else:
        title = url_list[-1]
    title_list = title.split('-')
    title = ' '.join(title_list)
    return title.title()


##########################################################################################################
# INGREDIENT STUFF
##########################################################################################################

def ingredients_from_url(url):
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
        measurement = measurement.replace("(","").replace(")","")
        measurement = [measurement]
        words = words[3:]
    else:
        measurement = [word for word in words if word in measurement_units]                                  
        if len(measurement)==0 and ('to taste' in ' '.join(words) or 'for flavor' in ' '.join(words) or 'as needed' in ' '.join(words)):
            measurement=['to taste']
            words = ' '.join(words).replace('to taste','').replace('for flavor','').replace('as needed','')
            words = words.split(' ')
        elif len(measurement)==0:
            measurement=['unspecified']
        words = [word for word in words if word not in measurement_units]

    descriptor_terms = [line.split('\n')[0] for line in open('descriptor_terms.txt', 'r').readlines()]
    descriptors = [word for word in words if word in descriptor_terms]
    if len(descriptors)==0:
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
        name = [ingredient1.replace(',',''),ingredient2.replace(',','')]
    else:
        name = [' '.join(words).replace(',','')]

    return {"name":name,
            "quantity":quantity,
            "measurement":measurement,
            "descriptor":descriptors,
            "preparation":preparation,
            "prep_description":prep_description,
            "max":Max,
            "full_string":string
            }

def get_ingredients(url):
    ingredient_list = ingredients_from_url(url)
    ingredient_data = []
    for ingredient in ingredient_list:
        ingredient_data.append(ingredient_parser(ingredient))
    resdict["ingredients"] = ingredient_data
    return ingredient_data


##########################################################################################################
# TOOL & METHOD STUFF
##########################################################################################################

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

def get_methods(url):
    steps = grab_steps(url)
    cooking_methods = []
    official_methods = {}
    with open('methods.json') as f:
        official_methods = json.load(f)

    for s in steps:
        line = s.lower().strip()
        line = re.sub(r'[^\w\s]','',line)
        for m in official_methods:
            if m in line:
                cooking_methods.append(m)
            elif official_methods[m]:
                for w in official_methods[m]:
                    if w in line:
                        cooking_methods.append(m)

    resdict["cooking methods"] = list(set(cooking_methods))
    return list(set(cooking_methods))

##########################################################################################################
# STEP STUFF
##########################################################################################################

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

def get_structuredsteps(url):
    steps = grab_steps(url)
    joined = " ".join(steps)
    structured_steps = joined.split(".")

    resdict["structured steps"] = []

    time_units = ['sec', 'sec.', 'seconds', 'second' 'min', 'min.', 'minutes', 'minute', 'hour', 'hours', 'hr', 'hrs', 'hr.', 'hrs.']

    stop_words = ["and", "with", "the", "to", "or", "more", "as"]

    ingredient_dicts = [ingredient_dict for ingredient_dict in resdict["ingredients"]]
    ingredient_lists = [ingredient_dict['name'] for ingredient_dict in ingredient_dicts]
    ingredient_names = [inner for outer in ingredient_lists for inner in outer]
    cooking_tools = [y for y in resdict["cooking tools"]]
    cooking_tools.extend([z for z in resdict["implied cooking tools"]])
    methods = {}
    
    official_methods = {}
    with open('methods.json') as f:
        official_methods = json.load(f)
    
    for m in resdict["cooking methods"]:
        methods[m] = official_methods[m]

    for s in structured_steps:
        s = s.lstrip()
        if s != "":
            ingredient_list = []
            for i in ingredient_names:
                for y in i.split():
                    if y not in stop_words and y in s:
                        if "broth" in i and "broth" not in s:
                            continue
                    ingredient_list.append(i)

            if len(ingredient_list)==0:
                ingredient_list = ['none']

            tools_list = [t for t in cooking_tools if t in s]
            if len(tools_list)==0:
                tools_list = ['unspecified']

            methods_list = []
            for m in methods.keys():
                if m in s:
                    methods_list.append(m)
                elif methods[m]:
                    for im in methods[m]:
                        if im in s and im not in " ".join(tools_list):
                            #print(im)
                            methods_list.append(m)
            if len(methods_list)==0:
                methods_list = ['unspecified']

            cooking_time = ""
            tokens = s.split(" ")
            for x in range(len(tokens) - 1):
                if tokens[x].isdigit() and tokens[x + 1] in time_units:
                    cooking_time = [tokens[x] + ' ' + tokens[x + 1]]
            if len(cooking_time)==0:
                cooking_time = ['unspecified']
                
            step = {
                "step": s,
                "ingredients": list(set(ingredient_list)),
                "tools": list(set(tools_list)),
                "cooking time": cooking_time,
                "methods": methods_list
            }

            resdict["structured steps"].append(step)


##########################################################################################################
# TRANSFORMATIONS
##########################################################################################################

def vegetarian(resdict, transform_type):
    transformed_rec = copy.deepcopy(resdict)
    official_veg_transform = {}
    with open('vegetarian.json') as f:
        official_veg_transform = json.load(f)

    substitutes = official_veg_transform["to veg"] if transform_type == "to veg" else official_veg_transform["from veg"]
    new_ingredients = transformed_rec["ingredients"]
    mapping = {}

    for i in new_ingredients:
        #pdb.set_trace()
        orig = i["name"][0].lower().strip()
        orig = re.sub(r'[^\w\s]','',orig)
        for w in orig.split():
            if w in list(substitutes.keys()):
                if "broth" in orig and w != "broth":
                    #pdb.set_trace()
                    continue
                else:
                    mapping[i["name"][0]] = substitutes[w][0]
                    i["name"] = substitutes[w][0]

    #pprint(resdict['ingredients'])
    #pprint(new_ingredients)
    #pprint(mapping)

    new_steps = transformed_rec["structured steps"]
    for s in new_steps:
        for m in mapping.keys():
            if m in s["ingredients"]:
                new_ingredient_list = [x if x != m else mapping[m] for x in s["ingredients"]]
                s["ingredients"] = new_ingredient_list

    #pprint(resdict["structured steps"])
    #pprint(new_steps)
    return transformed_rec

##########################################################################################################
# MAIN
##########################################################################################################

def main():
    #url = "http://allrecipes.com/recipe/easy-meatloaf/"
    #url = 'https://thewoksoflife.com/2018/08/peach-daiquiris-frozen/'
    #url = 'https://www.allrecipes.com/recipe/80827/easy-garlic-broiled-chicken/'

    url = str(input("What recipe would you like to read?: \n")).strip()
    #autograder(url)
    pretty_output(url)
    
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
    #             pprint(resdict["cooking methods"])
    #         elif user_input == "4":
    #             pprint(resdict["structured steps"])
    #         elif user_input == "5":
    #             print("How do you want to transform the recipe?")
    #             print("\n1. To vegeratian \n2. From vegetarian")
    #             transform_type = str(input("Choose an option: ")).strip()
    #             if transform_type == "1":
    #                 pprint(vegetarian(resdict, "to veg"))
    #             elif transform_type == "2":
    #                 pprint(vegetarian(resdict, "from veg"))
    #             else:
    #                 print("Invalid transformation type.")
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
    #
if __name__ == '__main__':
    main()
