import asyncio

from selenium import webdriver
from selenium.webdriver.common.by import By
from asyncselenium.webdriver.remote.async_webdriver import AsyncWebdriver
from asyncselenium.webdriver.support.async_wait import AsyncWebDriverWait
from asyncselenium.webdriver.support import async_expected_conditions as ec

chrome_options = webdriver.ChromeOptions()

async def test_get():
    browser = await AsyncWebdriver(options=chrome_options)
    wait = AsyncWebDriverWait(browser, 20)
    await browser.get('https://www.baidu.com')

async def test_find_ele():
    browser = await AsyncWebdriver(options=chrome_options)
    wait = AsyncWebDriverWait(browser, 20)
    ele = await wait.until(ec.presence_of_element_located((By.XPATH, '//*[@id="su"]')))
    print(ele)

async def test_find_ele2():
    browser = await AsyncWebdriver(options=chrome_options)
    wait = AsyncWebDriverWait(browser, 20)
    ele = await browser.find_element_by_xpath('//*[@id="su"]')
    print(ele)

async def send_click():
    browser = await AsyncWebdriver(options=chrome_options)
    wait = AsyncWebDriverWait(browser, 20)
    ele = await wait.until(ec.presence_of_element_located((By.XPATH, '//*[@id="su"]')))
    search = await wait.until(ec.presence_of_element_located((By.XPATH, '//*[@id="kw"]')))
    await search.send_keys('百度')
    print(await ele.tag_name)

async def test_ec_visiable():
    browser = await AsyncWebdriver(options=chrome_options)
    wait = AsyncWebDriverWait(browser, 20)
    await browser.get('https://www.baidu.com')
    eles = await wait.until(ec.visibility_of_any_elements_located((By.XPATH, '//*[@id="su"]')))
    print(eles)

asyncio.run(test_ec_visiable())
