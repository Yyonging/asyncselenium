import asyncio

from selenium import webdriver
from async_webdriver import AsyncWebdriver
from selenium.webdriver.remote.command import Command

class Automation:

    def __init__(self) -> None:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--window-size=1920,1080')
        self.browser = AsyncWebdriver(options=chrome_options)
    
    async def start(self):
        await self.browser.start()
    
    async def get(self):
        await self.browser.get('http://www.baidu.com')()

async def test_get():
    automation = Automation()
    await automation.start()
    await automation.get()

asyncio.run(test_get())
