import logging
import sys
import requests
from bs4 import BeautifulSoup

import db

HOST = 'https://www.jamieoliver.com'
PATH = '/recipes/all'

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def main():
    response = requests.get(f'{HOST}{PATH}')
    soup = make_soup(response)
    logger.info('Soup made')
    links = get_recipe_links(soup)
    logger.info('Got recipe links')
    recipes = get_recipes(links)
    logger.info('Got recipes')
    show_recipes(recipes)
    logger.info(f'{len(recipes)} recipes shown')
    conn = db.connect_db()
    db.insert_recipes(conn, recipes)
    db.query_results(conn)

def make_soup(response: requests.Response) -> BeautifulSoup:
    return BeautifulSoup(response.content, 'html.parser')

def get_recipe_links(soup: BeautifulSoup) -> list[str]:
    page_num = 1
    links = []
    while True:
        content_div = soup.find_all('div', class_='content-grid-item--4-col')
        if not content_div:
            break
        [links.append(content.find('a').get('href')) for content in content_div if content_div]
        soup = load_more_recipes(page_num)
        page_num += 1
    return links

def load_more_recipes(page_num: int) -> BeautifulSoup:
    query = f'?page={page_num}'
    response = requests.get(f'{HOST}{PATH}{query}')
    return make_soup(response)

def get_recipes(links: list[str]) -> list[dict]:
    recipes = []
    for link in links:
        recipe = {}
        response = requests.get(f'{HOST}{link}')
        soup = make_soup(response)
        recipe['title'] = add_recipe_title(soup)
        recipe['ingredients'] = add_recipe_ingredients(soup)
        recipe['method'] = add_recipe_method(soup)
        if recipe['method'] != '[]':
            recipes.append(recipe)
            logger.info(f'Added {len(recipes)} recipe{'s' if len(recipes) != 1 else ''}')
        else:
            logger.warning(f'Recipe for {recipe['title']} unavailable. Skipping...')
    return recipes

def add_recipe_title(soup: BeautifulSoup) -> str:
    title = soup.find('h1', class_='detail-panel__page-title type-h2 sm:pt-32 astro-edmpjb4m')
    return title.string

def add_recipe_ingredients(soup: BeautifulSoup) -> str:
    ingredients = []
    ingredients_div = soup.find('div', class_='ingredients-rich-text')
    ingredients_p_tags = ingredients_div.find_all('p')
    for ingredient in ingredients_p_tags:
        if str(ingredient['class']) == '[\'type-h5\']' and str(ingredient.string) == "SHOP JAMIE’S SERVEWARE":
            break
        if str(ingredient['class']) == '[\'type-h5\']':
            continue
        a_tag = ingredient.a
        if a_tag is not None:
            a_tag = ingredient.a.extract()
            ingredients.append(str(ingredient.string) + " " + str(a_tag.string))
        else:
            ingredients.append((ingredient.string))
    return str(ingredients)

def add_recipe_method(soup: BeautifulSoup) -> str:
    method = []
    count = 1
    method_div = soup.find('div', class_='recipe-page--method astro-erqtmm5j').find_all('li')
    for step in method_div:
        method.append(f'{count}. {str(step.string)}')
        count += 1
    return str(method)

def show_recipes(recipes: list[dict]):
    for recipe in recipes:
        logger.info(recipe['title'])
        logger.info(recipe['ingredients'])
        logger.info(recipe['method'])

if __name__ == '__main__':
    main()
