asyncselenium Package
=======================

1. This is a tools and libraries enabling web browser automation. 
2. it makes selenium to be async, and improve the performance! 
3. the useage is the same to selenium to make it easy to use.

you can simply install or upgrade:

    pip install -U asyncselenium

if you already make the remote driver running (use the default port 4444):

.. code-block:: python

    import asyncio

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from asyncselenium.webdriver.remote.async_webdriver import AsyncWebdriver
    from asyncselenium.webdriver.support.async_wait import AsyncWebDriverWait
    from asyncselenium.webdriver.support import async_expected_conditions as ec

    async def test_get():
        chrome_options = webdriver.ChromeOptions()
        browser = await AsyncWebdriver(options=chrome_options)
        wait = AsyncWebDriverWait(browser, 20)
        await browser.get('https://www.baidu.com')
        ele = await wait.until(ec.presence_of_element_located((By.XPATH, '//*[@id="su"]')))
        search = await wait.until(ec.presence_of_element_located((By.XPATH, '//*[@id="kw"]')))
        await search.send_keys('python')
        print(await ele.tag_name)
        await asyncio.sleep(3)
        await browser.quit()

    asyncio.run(test_get())

.. code-block:: python

    import asyncio
    import sys
    sys.path.append('.')
    from selenium.webdriver.chrome import service
    from asyncselenium.webdriver.chrome.async_webdriver import WebDriver
    
    driver_path = ''
    async def test_get():
        browser = await WebDriver(driver_path)
        await browser.get('https://www.baidu.com')
        await asyncio.sleep(5)
        await browser.quit()
    
    async def test_multi_browser():
        service = WebDriver.get_service(driver_path)
        browser = await WebDriver(driver_path, service=service)
        await browser.get('https://www.baidu.com')
        browser2 = await WebDriver(driver_path, service=service)
        await browser2.get('https://news.baidu.com')
        await asyncio.sleep(5)
        await browser.quit(stop_service=False)
        await browser2.get('https://www.baidu.com')
        await asyncio.sleep(5)
        await browser2.quit()
    
    asyncio.run(test_multi_browser())
