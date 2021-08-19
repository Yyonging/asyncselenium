import base64
import warnings

from typing import Any, Coroutine
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.remote.webdriver import WebDriver, _make_w3c_caps
from selenium.common.exceptions import (InvalidArgumentException,
                                        WebDriverException,
                                        NoSuchCookieException)
from selenium.webdriver.common.by import By
from asyncselenium.webdriver.remote.async_object import Asyncobject
from asyncselenium.webdriver.remote.async_swith_to import AsyncSwithTo
from asyncselenium.webdriver.remote.async_webelement import AsyncWebElement
from asyncselenium.webdriver.remote.async_remote_connection import AsyncRemoteConnection

class AsyncWebdriver(WebDriver, Asyncobject):
    _web_element_cls = AsyncWebElement

    async def __init__(self, command_executor='http://127.0.0.1:4444/wd/hub',
                 desired_capabilities=None, browser_profile=None, proxy=None,
                 keep_alive=False, file_detector=None, options=None, session_id=None, w3c=True):    
        super().__init__(command_executor=command_executor, desired_capabilities=desired_capabilities,
            browser_profile=browser_profile, proxy=proxy, keep_alive=keep_alive, file_detector=file_detector, options=options)
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

    def execute(self, driver_command, params=None) -> Coroutine:

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

    async def find_element_by_id(self, id_) -> AsyncWebElement:
        """Finds an element by id.

        :Args:
         - id\_ - The id of the element to be found.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_id('foo')
        """
        return await self.find_element(by=By.ID, value=id_)

    async def find_elements_by_id(self, id_) -> list[AsyncWebElement]:
        """
        Finds multiple elements by id.

        :Args:
         - id\_ - The id of the elements to be found.

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_id('foo')
        """
        return await self.find_elements(by=By.ID, value=id_)

    async def find_element_by_xpath(self, xpath) -> AsyncWebElement:
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

    async def find_elements_by_xpath(self, xpath) -> list[AsyncWebElement]:
        """
        Finds multiple elements by xpath.

        :Args:
         - xpath - The xpath locator of the elements to be found.

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_xpath("//div[contains(@class, 'foo')]")
        """
        return await self.find_elements(by=By.XPATH, value=xpath)

    async def find_element_by_link_text(self, link_text) -> AsyncWebElement:
        """
        Finds an element by link text.

        :Args:
         - link_text: The text of the element to be found.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_link_text('Sign In')
        """
        return await self.find_element(by=By.LINK_TEXT, value=link_text)

    async def find_elements_by_link_text(self, text) -> list[AsyncWebElement]:
        """
        Finds elements by link text.

        :Args:
         - link_text: The text of the elements to be found.

        :Returns:
         - list of webelement - a list with elements if any was found.  an
           empty list if not

        :Usage:
            elements = driver.find_elements_by_link_text('Sign In')
        """
        return await self.find_elements(by=By.LINK_TEXT, value=text)

    async def find_element_by_partial_link_text(self, link_text) -> AsyncWebElement:
        """
        Finds an element by a partial match of its link text.

        :Args:
         - link_text: The text of the element to partially match on.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_partial_link_text('Sign')
        """
        return await self.find_element(by=By.PARTIAL_LINK_TEXT, value=link_text)

    async def find_elements_by_partial_link_text(self, link_text) -> list[AsyncWebElement]:
        """
        Finds elements by a partial match of their link text.

        :Args:
         - link_text: The text of the element to partial match on.

        :Returns:
         - list of webelement - a list with elements if any was found.  an
           empty list if not

        :Usage:
            elements = driver.find_elements_by_partial_link_text('Sign')
        """
        return await self.find_elements(by=By.PARTIAL_LINK_TEXT, value=link_text)

    async def find_element_by_name(self, name) -> AsyncWebElement:
        """
        Finds an element by name.

        :Args:
         - name: The name of the element to find.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_name('foo')
        """
        return await self.find_element(by=By.NAME, value=name)

    async def find_elements_by_name(self, name) -> list[AsyncWebElement]:
        """
        Finds elements by name.

        :Args:
         - name: The name of the elements to find.

        :Returns:
         - list of webelement - a list with elements if any was found.  an
           empty list if not

        :Usage:
            elements = driver.find_elements_by_name('foo')
        """
        return await self.find_elements(by=By.NAME, value=name)

    async def find_element_by_tag_name(self, name) -> AsyncWebElement:
        """
        Finds an element by tag name.

        :Args:
         - name - name of html tag (eg: h1, a, span)

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_tag_name('h1')
        """
        return await self.find_element(by=By.TAG_NAME, value=name)

    async def find_elements_by_tag_name(self, name) -> list[AsyncWebElement]:
        """
        Finds elements by tag name.

        :Args:
         - name - name of html tag (eg: h1, a, span)

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_tag_name('h1')
        """
        return await self.find_elements(by=By.TAG_NAME, value=name)

    async def find_element_by_class_name(self, name) -> AsyncWebElement:
        """
        Finds an element by class name.

        :Args:
         - name: The class name of the element to find.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_class_name('foo')
        """
        return await self.find_element(by=By.CLASS_NAME, value=name)

    async def find_elements_by_class_name(self, name) -> list[AsyncWebElement]:
        """
        Finds elements by class name.

        :Args:
         - name: The class name of the elements to find.

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_class_name('foo')
        """
        return await self.find_elements(by=By.CLASS_NAME, value=name)

    async def find_element_by_css_selector(self, css_selector) -> AsyncWebElement:
        """
        Finds an element by css selector.

        :Args:
         - css_selector - CSS selector string, ex: 'a.nav#home'

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = driver.find_element_by_css_selector('#foo')
        """
        return await self.find_element(by=By.CSS_SELECTOR, value=css_selector)

    async def find_elements_by_css_selector(self, css_selector) -> list[AsyncWebElement]:
        """
        Finds elements by css selector.

        :Args:
         - css_selector - CSS selector string, ex: 'a.nav#home'

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = driver.find_elements_by_css_selector('.foo')
        """
        return await self.find_elements(by=By.CSS_SELECTOR, value=css_selector)

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

    @property
    async def page_source(self):
        """
        Gets the source of the current page.

        :Usage:
            driver.page_source
        """
        return (await self.execute(Command.GET_PAGE_SOURCE))['value']

    async def close(self):
        """
        Closes the current window.

        :Usage:
            driver.close()
        """
        await self.execute(Command.CLOSE)

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
    
    async def maximize_window(self):
        """
        Maximizes the current window that webdriver is using
        """
        params = None
        command = Command.W3C_MAXIMIZE_WINDOW
        if not self.w3c:
            command = Command.MAXIMIZE_WINDOW
            params = {'windowHandle': 'current'}
        await self.execute(command, params)

    async def fullscreen_window(self):
        """
        Invokes the window manager-specific 'full screen' operation
        """
        await self.execute(Command.FULLSCREEN_WINDOW)

    async def minimize_window(self):
        """
        Invokes the window manager-specific 'minimize' operation
        """
        await self.execute(Command.MINIMIZE_WINDOW)

    # Target Locators
    async def switch_to_active_element(self):
        """ Deprecated use driver.switch_to.active_element
        """
        warnings.warn("use driver.switch_to.active_element instead",
                      DeprecationWarning, stacklevel=2)
        return await self._switch_to.active_element

    async def switch_to_window(self, window_name):
        """ Deprecated use driver.switch_to.window
        """
        warnings.warn("use driver.switch_to.window instead",
                      DeprecationWarning, stacklevel=2)
        await self._switch_to.window(window_name)

    async def switch_to_frame(self, frame_reference):
        """ Deprecated use driver.switch_to.frame
        """
        warnings.warn("use driver.switch_to.frame instead",
                      DeprecationWarning, stacklevel=2)
        await self._switch_to.frame(frame_reference)

    async def switch_to_default_content(self):
        """ Deprecated use driver.switch_to.default_content
        """
        warnings.warn("use driver.switch_to.default_content instead",
                      DeprecationWarning, stacklevel=2)
        await self._switch_to.default_content()

    async def switch_to_alert(self):
        """ Deprecated use driver.switch_to.alert
        """
        warnings.warn("use driver.switch_to.alert instead",
                      DeprecationWarning, stacklevel=2)
        return await self._switch_to.alert

    # Navigation
    async def back(self):
        """
        Goes one step backward in the browser history.

        :Usage:
            driver.back()
        """
        await self.execute(Command.GO_BACK)

    async def forward(self):
        """
        Goes one step forward in the browser history.

        :Usage:
            driver.forward()
        """
        await self.execute(Command.GO_FORWARD)

    async def refresh(self):
        """
        Refreshes the current page.

        :Usage:
            driver.refresh()
        """
        await self.execute(Command.REFRESH)

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

    async def delete_cookie(self, name):
        """
        Deletes a single cookie with the given name.

        :Usage:
            driver.delete_cookie('my_cookie')
        """
        await self.execute(Command.DELETE_COOKIE, {'name': name})

    async def delete_all_cookies(self):
        """
        Delete all cookies in the scope of the session.

        :Usage:
            driver.delete_all_cookies()
        """
        await self.execute(Command.DELETE_ALL_COOKIES)

    async def add_cookie(self, cookie_dict):
        """
        Adds a cookie to your current session.

        :Args:
         - cookie_dict: A dictionary object, with required keys - "name" and "value";
            optional keys - "path", "domain", "secure", "expiry"

        Usage:
            driver.add_cookie({'name' : 'foo', 'value' : 'bar'})
            driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/'})
            driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/', 'secure':True})

        """
        await self.execute(Command.ADD_COOKIE, {'cookie': cookie_dict})

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

    async def set_script_timeout(self, time_to_wait):
        """
        Set the amount of time that the script should wait during an
           execute_async_script call before throwing an error.

        :Args:
         - time_to_wait: The amount of time to wait (in seconds)

        :Usage:
            driver.set_script_timeout(30)
        """
        if self.w3c:
            await self.execute(Command.SET_TIMEOUTS, {
                'script': int(float(time_to_wait) * 1000)})
        else:
            await self.execute(Command.SET_SCRIPT_TIMEOUT, {
                'ms': float(time_to_wait) * 1000})

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

    async def get_screenshot_as_file(self, filename):
        """
        Saves a screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            driver.get_screenshot_as_file('/Screenshots/foo.png')
        """
        if not filename.lower().endswith('.png'):
            warnings.warn("name used for saved screenshot does not match file "
                          "type. It should end with a `.png` extension", UserWarning)
        png = await self.get_screenshot_as_png()
        try:
            with open(filename, 'wb') as f:
                f.write(png)
        except IOError:
            return False
        finally:
            del png
        return True

    async def save_screenshot(self, filename):
        """
        Saves a screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            driver.save_screenshot('/Screenshots/foo.png')
        """
        return await self.get_screenshot_as_file(filename)

    async def get_screenshot_as_png(self):
        """
        Gets the screenshot of the current window as a binary data.

        :Usage:
            driver.get_screenshot_as_png()
        """
        return base64.b64decode((await self.get_screenshot_as_base64()).encode('ascii'))


    async def get_screenshot_as_base64(self):
        """
        Gets the screenshot of the current window as a base64 encoded string
           which is useful in embedded images in HTML.

        :Usage:
            driver.get_screenshot_as_base64()
        """
        return (await self.execute(Command.SCREENSHOT))['value']
    
    async def set_window_size(self, width, height, windowHandle='current'):
        """
        Sets the width and height of the current window. (window.resizeTo)

        :Args:
         - width: the width in pixels to set the window to
         - height: the height in pixels to set the window to

        :Usage:
            driver.set_window_size(800,600)
        """
        if self.w3c:
            if windowHandle != 'current':
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            await self.set_window_rect(width=int(width), height=int(height))
        else:
            await self.execute(Command.SET_WINDOW_SIZE, {
                'width': int(width),
                'height': int(height),
                'windowHandle': windowHandle})

    async def get_window_size(self, windowHandle='current'):
        """
        Gets the width and height of the current window.

        :Usage:
            driver.get_window_size()
        """
        command = Command.GET_WINDOW_SIZE
        if self.w3c:
            if windowHandle != 'current':
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            size = await self.get_window_rect()
        else:
            size = await self.execute(command, {'windowHandle': windowHandle})

        if size.get('value', None) is not None:
            size = size['value']

        return {k: size[k] for k in ('width', 'height')}

    async def set_window_position(self, x, y, windowHandle='current'):
        """
        Sets the x,y position of the current window. (window.moveTo)

        :Args:
         - x: the x-coordinate in pixels to set the window position
         - y: the y-coordinate in pixels to set the window position

        :Usage:
            driver.set_window_position(0,0)
        """
        if self.w3c:
            if windowHandle != 'current':
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            return await self.set_window_rect(x=int(x), y=int(y))
        else:
            await self.execute(Command.SET_WINDOW_POSITION,
                         {
                             'x': int(x),
                             'y': int(y),
                             'windowHandle': windowHandle
                         })

    async def get_window_position(self, windowHandle='current'):
        """
        Gets the x,y position of the current window.

        :Usage:
            driver.get_window_position()
        """
        if self.w3c:
            if windowHandle != 'current':
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            position = await self.get_window_rect()
        else:
            position = await self.execute(Command.GET_WINDOW_POSITION,
                                    {'windowHandle': windowHandle})['value']

        return {k: position[k] for k in ('x', 'y')}

    async def get_window_rect(self):
        """
        Gets the x, y coordinates of the window as well as height and width of
        the current window.

        :Usage:
            driver.get_window_rect()
        """
        return (await self.execute(Command.GET_WINDOW_RECT))['value']

    async def set_window_rect(self, x=None, y=None, width=None, height=None):
        """
        Sets the x, y coordinates of the window as well as height and width of
        the current window.

        :Usage:
            driver.set_window_rect(x=10, y=10)
            driver.set_window_rect(width=100, height=200)
            driver.set_window_rect(x=10, y=10, width=100, height=200)
        """
        if (x is None and y is None) and (height is None and width is None):
            raise InvalidArgumentException("x and y or height and width need values")

        return (await self.execute(Command.SET_WINDOW_RECT, {"x": x, "y": y,
                                                      "width": width,
                                                      "height": height}))['value']






    @property
    async def orientation(self):
        """
        Gets the current orientation of the device

        :Usage:
            orientation = driver.orientation
        """
        return (await self.execute(Command.GET_SCREEN_ORIENTATION))['value']

    @orientation.setter
    async def orientation(self, value):
        """
        Sets the current orientation of the device

        :Args:
        - value: orientation to set it to.

        :Usage:
            driver.orientation = 'landscape'
        """
        allowed_values = ['LANDSCAPE', 'PORTRAIT']
        if value.upper() in allowed_values:
            await self.execute(Command.SET_SCREEN_ORIENTATION, {'orientation': value})
        else:
            raise WebDriverException("You can only set the orientation to 'LANDSCAPE' and 'PORTRAIT'")

    @property
    async def log_types(self):
        """
        Gets a list of the available log types

        :Usage:
            driver.log_types
        """
        return (await self.execute(Command.GET_AVAILABLE_LOG_TYPES))['value']

    async def get_log(self, log_type):
        """
        Gets the log for a given log type

        :Args:
         - log_type: type of log that which will be returned

        :Usage:
            driver.get_log('browser')
            driver.get_log('driver')
            driver.get_log('client')
            driver.get_log('server')
        """
        return (await self.execute(Command.GET_LOG, {'type': log_type}))['value']
