from collections import deque
import logging
import sys
import asyncio
import types

import aiohttp
from bs4 import BeautifulSoup

import db

HOST = 'https://www.jamieoliver.com'
PATH = '/recipes/all'

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

async def main():
    async with aiohttp.ClientSession() as session:
        num_of_pages = await get_number_of_pages(session)
        logger.info('Number of pages: %d', num_of_pages)
        urls = get_links_for_recipe_pages(session, num_of_pages)
        links = await asyncio.gather(*(get_recipe_links(session, url) for url in urls))
        links = [link for list_of_links in links for link in list_of_links]
        logger.info('Got recipe links')
        recipes = deque()
        await asyncio.gather(*(get_recipes(session, link, recipes) for link in links))
        logger.info('Got recipes')
        logger.info(f'{len(recipes)} recipes shown')
        show_recipes(recipes)
        conn = db.connect_db()
        db.insert_recipes(conn, recipes)
        db.query_results(conn)

async def get_number_of_pages(session: aiohttp.ClientSession) -> int:
    response = await fetch(f'{HOST}{PATH}', session)
    soup = make_soup(response)
    pagination_div = soup.find('div', class_='pagination-grid__progress astro-b4fc5k6u')
    p_tag = pagination_div.find('p')
    strong_tags = p_tag.find_all('strong')
    return -(int(strong_tags[1].string) // -(int(strong_tags[0].string)))

async def fetch(url: str, session: aiohttp.ClientSession) -> types.CoroutineType:
    async with session.get(url) as response:
        return await response.text()
    
def make_soup(response: aiohttp.ClientResponse) -> BeautifulSoup:
    return BeautifulSoup(response, 'html.parser')

def get_links_for_recipe_pages(session: aiohttp.ClientSession, num_of_pages: int):
    urls = []
    for page_num in range(num_of_pages):
        query = f'page={page_num}'
        url = f'{HOST}{PATH}?{query}'
        urls.append(url)
    return urls

async def get_recipe_links(session: aiohttp.ClientSession, url: str) -> list[str]:
    links = []
    response = await fetch(url, session)
    soup = make_soup(response)
    content_div = soup.find_all('div', class_='content-grid-item--4-col')
    [links.append(content.find('a').get('href')) for content in content_div if content_div]
    return links

async def get_recipes(session: aiohttp.ClientSession, link: str, recipes: deque) -> None:
    recipe = {}
    response = await fetch(f'{HOST}{link}', session)
    soup = make_soup(response)
    recipe['title'] = add_recipe_title(soup)
    recipe['ingredients'] = add_recipe_ingredients(soup)
    recipe['method'] = add_recipe_method(soup)
    if recipe['method'] != '[]':
        recipes.appendleft(recipe)
        logger.info(f'Added {len(recipes)} recipe{'s' if len(recipes) != 1 else ''}')
    else:
        logger.warning(f'Recipe for {recipe['title']} unavailable. Skipping...')

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
    asyncio.run(main())
