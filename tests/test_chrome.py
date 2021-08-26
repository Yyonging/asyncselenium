import asyncio
import sys
sys.path.append('.')
from selenium.webdriver.chrome import service
from asyncselenium.webdriver.chrome.async_webdriver import AsyncChromeDriver

driver_path = '/home/deep/codes/zd_module/drivers/chromedriver'
async def test_get():
    browser = await AsyncChromeDriver(driver_path)
    await browser.get('https://www.baidu.com')
    await asyncio.sleep(5)
    await browser.quit()

async def test_multi_browser():
    service = AsyncChromeDriver.get_service(driver_path)
    browser = await AsyncChromeDriver(driver_path, service=service)
    await browser.get('https://www.baidu.com')
    browser2 = await AsyncChromeDriver(driver_path, service=service)
    await browser2.get('https://news.baidu.com')
    await asyncio.sleep(5)
    await browser.quit(stop_service=False)
    await browser2.get('https://www.baidu.com')
    await asyncio.sleep(5)
    await browser2.quit()

asyncio.run(test_multi_browser())
