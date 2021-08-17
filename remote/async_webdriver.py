import asyncio
import base64
import typing

from typing import Any
from asyncselenium.remote.async_object import Asyncobject
from asyncselenium.remote.async_webelement import AsyncWebElement
from asyncselenium.remote.async_swith_to import AsyncSwithTo
from asyncselenium.remote.async_remote_connection import AsyncRemoteConnection
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.remote.webdriver import WebDriver, _make_w3c_caps
from selenium.common.exceptions import (InvalidArgumentException,
                                        WebDriverException,
                                        NoSuchCookieException)
from selenium.webdriver.common.by import By

class AsyncWebdriver(WebDriver, Asyncobject):
    _web_element_cls = AsyncWebElement

    async def __init__(self, command_executor='http://127.0.0.1:4444/wd/hub',
                 desired_capabilities=None, browser_profile=None, proxy=None,
                 keep_alive=False, file_detector=None, options=None, session_id=None, w3c=True):    
        super().__init__(command_executor=command_executor, desired_capabilities=desired_capabilities, browser_profile=browser_profile, proxy=proxy, keep_alive=keep_alive, file_detector=file_detector, options=options)
        await self.start(session_id, w3c)

    def start_session(self, capabilities, browser_profile):
        self.temp_capabilities = capabilities
        self.temp_browser_profile = browser_profile
    
    async def start(self, session_id=None, w3c=True):
        if type(self.command_executor) is RemoteConnection:
            self.command_executor = AsyncRemoteConnection(self.command_executor._url, keep_alive=self.command_executor.keep_alive)
        self._switch_to = AsyncSwithTo(self)
        
        if session_id:
            self.session_id = session_id
            self.command_executor.w3c = self.w3c = w3c
            return 
        capabilities, browser_profile = self.temp_capabilities, self.temp_browser_profile
        if not isinstance(capabilities, dict):
            raise InvalidArgumentException("Capabilities must be a dictionary")
        if browser_profile:
            if "moz:firefoxOptions" in capabilities:
                capabilities["moz:firefoxOptions"]["profile"] = browser_profile.encoded
            else:
                capabilities.update({'firefox_profile': browser_profile.encoded})
        w3c_caps = _make_w3c_caps(capabilities)
        parameters = {"capabilities": w3c_caps,
                      "desiredCapabilities": capabilities}
        response = await self.execute(Command.NEW_SESSION, parameters)
        if 'sessionId' not in response:
            response = response['value']
        self.session_id = response['sessionId']
        self.capabilities = response.get('value')

        # if capabilities is none we are probably speaking to
        # a W3C endpoint
        if self.capabilities is None:
            self.capabilities = response.get('capabilities')

        # Double check to see if we have a W3C Compliant browser
        self.w3c = response.get('status') is None
        self.command_executor.w3c = self.w3c

    def execute(self, driver_command, params=None) -> typing.Coroutine:

        async def _async_execute():
            nonlocal params
            if self.session_id is not None:
                if not params:
                    params = {'sessionId': self.session_id}
                elif 'sessionId' not in params:
                    params['sessionId'] = self.session_id

            params = self._wrap_value(params)
            response = await self.command_executor.execute(driver_command, params)()
            if response:
                self.error_handler.check_response(response)
                response['value'] = self._unwrap_value(
                    response.get('value', None))
                return response
            # If the server doesn't send a response, assume the command was
            # a success
            return {'success': 0, 'value': None, 'sessionId': self.session_id}            
        return _async_execute()

    async def get(self, url):
        await self.execute(Command.GET, {'url': url})
    
    @property
    async def title(self):
        """Returns the title of the current page.

        :Usage:
            title = driver.title
        """
        resp = await self.execute(Command.GET_TITLE)
        return resp['value'] if resp['value'] is not None else ""

    async def find_element(self, by=By.ID, value=None):
        """
        Find an element given a By strategy and locator. Prefer the find_element_by_* methods when
        possible.

        :Usage:
            element = driver.find_element(By.ID, 'foo')

        :rtype: WebElement
        """
        if self.w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value
        res = await self.execute(Command.FIND_ELEMENT, {
            'using': by,
            'value': value})
        return res['value']

    async def find_element_by_xpath(self, xpath):
        """
        Finds an element by xpath.

        :Args:
         - xpath - The xpath locator of the element to find.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_xpath('//div/td[1]')
        """
        return await self.find_element(by=By.XPATH, value=xpath)

    async def execute_script(self, script, *args):
        """
        Synchronously Executes JavaScript in the current window/frame.

        :Args:
         - script: The JavaScript to execute.
         - \*args: Any applicable arguments for your JavaScript.

        :Usage:
            driver.execute_script('return document.title;')
        """
        converted_args = list(args)
        command = None
        if self.w3c:
            command = Command.W3C_EXECUTE_SCRIPT
        else:
            command = Command.EXECUTE_SCRIPT

        return (await self.execute(command, {
            'script': script,
            'args': converted_args}))['value']


    async def execute_async_script(self, script, *args):
        """
        Asynchronously Executes JavaScript in the current window/frame.

        :Args:
         - script: The JavaScript to execute.
         - \*args: Any applicable arguments for your JavaScript.

        :Usage:
            script = "var callback = arguments[arguments.length - 1]; " \
                     "window.setTimeout(function(){ callback('timeout') }, 3000);"
            driver.execute_async_script(script)
        """
        converted_args = list(args)
        if self.w3c:
            command = Command.W3C_EXECUTE_SCRIPT_ASYNC
        else:
            command = Command.EXECUTE_ASYNC_SCRIPT

        return (await self.execute(command, {
            'script': script,
            'args': converted_args}))['value']

    @property
    async def current_url(self):
        """
        Gets the URL of the current page.

        :Usage:
            driver.current_url
        """
        return (await self.execute(Command.GET_CURRENT_URL))['value']
    
    async def quit(self):
        """
        Quits the driver and closes every associated window.

        :Usage:
            driver.quit()
        """
        try:
            await self.execute(Command.QUIT)
        finally:
            self.stop_client()

    async def get_cookies(self):
        """
        Returns a set of dictionaries, corresponding to cookies visible in the current session.

        :Usage:
            driver.get_cookies()
        """
        return (await self.execute(Command.GET_ALL_COOKIES))['value']
    
    async def get_cookie(self, name):
        """
        Get a single cookie by name. Returns the cookie if found, None if not.

        :Usage:
            driver.get_cookie('my_cookie')
        """
        if self.w3c:
            try:
                return (await self.execute(Command.GET_COOKIE, {'name': name}))['value']
            except NoSuchCookieException:
                return None
        else:
            cookies = await self.get_cookies()
            for cookie in cookies:
                if cookie['name'] == name:
                    return cookie
            return None    

    async def implicitly_wait(self, time_to_wait):
        """
        Sets a sticky timeout to implicitly wait for an element to be found,
           or a command to complete. This method only needs to be called one
           time per session. To set the timeout for calls to
           execute_async_script, see set_script_timeout.

        :Args:
         - time_to_wait: Amount of time to wait (in seconds)

        :Usage:
            driver.implicitly_wait(30)
        """
        if self.w3c:
            await self.execute(Command.SET_TIMEOUTS, {
                'implicit': int(float(time_to_wait) * 1000)})
        else:
            await self.execute(Command.IMPLICIT_WAIT, {
                'ms': float(time_to_wait) * 1000})

    async def get_screenshot_as_base64(self):
        """
        Gets the screenshot of the current window as a base64 encoded string
           which is useful in embedded images in HTML.

        :Usage:
            driver.get_screenshot_as_base64()
        """
        return (await self.execute(Command.SCREENSHOT))['value']
    
    async def get_screenshot_as_png(self):
        """
        Gets the screenshot of the current window as a binary data.

        :Usage:
            driver.get_screenshot_as_png()
        """
        return base64.b64decode((await self.get_screenshot_as_base64()).encode('ascii'))

    @property
    async def current_window_handle(self):
        """
        Returns the handle of the current window.

        :Usage:
            driver.current_window_handle
        """
        if self.w3c:
            return (await self.execute(Command.W3C_GET_CURRENT_WINDOW_HANDLE))['value']
        else:
            return (await self.execute(Command.GET_CURRENT_WINDOW_HANDLE))['value']

    @property
    async def window_handles(self):
        """
        Returns the handles of all windows within the current session.

        :Usage:
            driver.window_handles
        """
        if self.w3c:
            return (await self.execute(Command.W3C_GET_WINDOW_HANDLES))['value']
        else:
            return (await self.execute(Command.GET_WINDOW_HANDLES))['value']
    
    async def set_page_load_timeout(self, time_to_wait):
        """
        Set the amount of time to wait for a page load to complete
           before throwing an error.

        :Args:
         - time_to_wait: The amount of time to wait

        :Usage:
            driver.set_page_load_timeout(30)
        """
        try:
            await self.execute(Command.SET_TIMEOUTS, {
                'pageLoad': int(float(time_to_wait) * 1000)})
        except WebDriverException:
            await self.execute(Command.SET_TIMEOUTS, {
                'ms': float(time_to_wait) * 1000,
                'type': 'page load'})

    async def find_elements(self, by=By.ID, value=None):
        """
        Find elements given a By strategy and locator. Prefer the find_elements_by_* methods when
        possible.

        :Usage:
            elements = driver.find_elements(By.CLASS_NAME, 'foo')

        :rtype: list of WebElement
        """
        if self.w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value

        # Return empty list if driver returns null
        # See https://github.com/SeleniumHQ/selenium/issues/4555
        return (await self.execute(Command.FIND_ELEMENTS, {
            'using': by,
            'value': value}))['value'] or []