from async_remote_connection import AsyncRemoteConnection
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.remote.webdriver import WebDriver, _make_w3c_caps
from selenium.common.exceptions import (InvalidArgumentException,
                                        WebDriverException,
                                        NoSuchCookieException)

class AsyncWebdriver(WebDriver):

    def start_session(self, capabilities, browser_profile):
        self.temp_capabilities = capabilities
        self.temp_browser_profile = browser_profile
    
    async def start(self):
        capabilities, browser_profile = self.temp_capabilities, self.temp_browser_profile
        if type(self.command_executor) is RemoteConnection:
            self.command_executor = AsyncRemoteConnection(self.command_executor._url, keep_alive=self.command_executor.keep_alive)
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
        response = await self.execute(Command.NEW_SESSION, parameters)()
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

    def execute(self, driver_command, params=None):

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
        return _async_execute

    def get(self, url):
        return self.execute(Command.GET, {'url': url})

    @property
    async def title(self):
        """Returns the title of the current page.

        :Usage:
            title = driver.title
        """
        resp = await self.execute(Command.GET_TITLE)()
        return resp['value'] if resp['value'] is not None else ""

    def close(self):
        """
        Closes the current window.

        :Usage:
            driver.close()
        """
        return self.execute(Command.CLOSE)
    
    def quit(self):
        """
        Quits the driver and closes every associated window.

        :Usage:
            driver.quit()
        """
        try:
            return self.execute(Command.QUIT)
        finally:
            self.stop_client()

    def maximize_window(self):
        """
        Maximizes the current window that webdriver is using
        """
        params = None
        command = Command.W3C_MAXIMIZE_WINDOW
        if not self.w3c:
            command = Command.MAXIMIZE_WINDOW
            params = {'windowHandle': 'current'}
        return self.execute(command, params)

    def fullscreen_window(self):
        """
        Invokes the window manager-specific 'full screen' operation
        """
        return self.execute(Command.FULLSCREEN_WINDOW)


    def minimize_window(self):
        """
        Invokes the window manager-specific 'minimize' operation
        """
        return self.execute(Command.MINIMIZE_WINDOW)

    def back(self):
        """
        Goes one step backward in the browser history.

        :Usage:
            driver.back()
        """
        return self.execute(Command.GO_BACK)


    # def forward(self):
    #     """
    #     Goes one step forward in the browser history.

    #     :Usage:
    #         driver.forward()
    #     """
    #     self.execute(Command.GO_FORWARD)

    # def refresh(self):
    #     """
    #     Refreshes the current page.

    #     :Usage:
    #         driver.refresh()
    #     """
    #     self.execute(Command.REFRESH)

    # # Options
    # def get_cookies(self):
    #     """
    #     Returns a set of dictionaries, corresponding to cookies visible in the current session.

    #     :Usage:
    #         driver.get_cookies()
    #     """
    #     return self.execute(Command.GET_ALL_COOKIES)['value']

    # def get_cookie(self, name):
    #     """
    #     Get a single cookie by name. Returns the cookie if found, None if not.

    #     :Usage:
    #         driver.get_cookie('my_cookie')
    #     """
    #     if self.w3c:
    #         try:
    #             return self.execute(Command.GET_COOKIE, {'name': name})['value']
    #         except NoSuchCookieException:
    #             return None
    #     else:
    #         cookies = self.get_cookies()
    #         for cookie in cookies:
    #             if cookie['name'] == name:
    #                 return cookie
    #         return None

    # def delete_cookie(self, name):
    #     """
    #     Deletes a single cookie with the given name.

    #     :Usage:
    #         driver.delete_cookie('my_cookie')
    #     """
    #     self.execute(Command.DELETE_COOKIE, {'name': name})

    # def delete_all_cookies(self):
    #     """
    #     Delete all cookies in the scope of the session.

    #     :Usage:
    #         driver.delete_all_cookies()
    #     """
    #     self.execute(Command.DELETE_ALL_COOKIES)

    # def add_cookie(self, cookie_dict):
    #     """
    #     Adds a cookie to your current session.

    #     :Args:
    #      - cookie_dict: A dictionary object, with required keys - "name" and "value";
    #         optional keys - "path", "domain", "secure", "expiry"

    #     Usage:
    #         driver.add_cookie({'name' : 'foo', 'value' : 'bar'})
    #         driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/'})
    #         driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/', 'secure':True})

    #     """
    #     self.execute(Command.ADD_COOKIE, {'cookie': cookie_dict})

    # # Timeouts
    # def implicitly_wait(self, time_to_wait):
    #     """
    #     Sets a sticky timeout to implicitly wait for an element to be found,
    #        or a command to complete. This method only needs to be called one
    #        time per session. To set the timeout for calls to
    #        execute_async_script, see set_script_timeout.

    #     :Args:
    #      - time_to_wait: Amount of time to wait (in seconds)

    #     :Usage:
    #         driver.implicitly_wait(30)
    #     """
    #     if self.w3c:
    #         self.execute(Command.SET_TIMEOUTS, {
    #             'implicit': int(float(time_to_wait) * 1000)})
    #     else:
    #         self.execute(Command.IMPLICIT_WAIT, {
    #             'ms': float(time_to_wait) * 1000})

    # def set_script_timeout(self, time_to_wait):
    #     """
    #     Set the amount of time that the script should wait during an
    #        execute_async_script call before throwing an error.

    #     :Args:
    #      - time_to_wait: The amount of time to wait (in seconds)

    #     :Usage:
    #         driver.set_script_timeout(30)
    #     """
    #     if self.w3c:
    #         self.execute(Command.SET_TIMEOUTS, {
    #             'script': int(float(time_to_wait) * 1000)})
    #     else:
    #         self.execute(Command.SET_SCRIPT_TIMEOUT, {
    #             'ms': float(time_to_wait) * 1000})

    # def set_page_load_timeout(self, time_to_wait):
    #     """
    #     Set the amount of time to wait for a page load to complete
    #        before throwing an error.

    #     :Args:
    #      - time_to_wait: The amount of time to wait

    #     :Usage:
    #         driver.set_page_load_timeout(30)
    #     """
    #     try:
    #         self.execute(Command.SET_TIMEOUTS, {
    #             'pageLoad': int(float(time_to_wait) * 1000)})
    #     except WebDriverException:
    #         self.execute(Command.SET_TIMEOUTS, {
    #             'ms': float(time_to_wait) * 1000,
    #             'type': 'page load'})

    # def find_element(self, by=By.ID, value=None):
    #     """
    #     Find an element given a By strategy and locator. Prefer the find_element_by_* methods when
    #     possible.

    #     :Usage:
    #         element = driver.find_element(By.ID, 'foo')

    #     :rtype: WebElement
    #     """
    #     if self.w3c:
    #         if by == By.ID:
    #             by = By.CSS_SELECTOR
    #             value = '[id="%s"]' % value
    #         elif by == By.TAG_NAME:
    #             by = By.CSS_SELECTOR
    #         elif by == By.CLASS_NAME:
    #             by = By.CSS_SELECTOR
    #             value = ".%s" % value
    #         elif by == By.NAME:
    #             by = By.CSS_SELECTOR
    #             value = '[name="%s"]' % value
    #     return self.execute(Command.FIND_ELEMENT, {
    #         'using': by,
    #         'value': value})['value']

    # def find_elements(self, by=By.ID, value=None):
    #     """
    #     Find elements given a By strategy and locator. Prefer the find_elements_by_* methods when
    #     possible.

    #     :Usage:
    #         elements = driver.find_elements(By.CLASS_NAME, 'foo')

    #     :rtype: list of WebElement
    #     """
    #     if self.w3c:
    #         if by == By.ID:
    #             by = By.CSS_SELECTOR
    #             value = '[id="%s"]' % value
    #         elif by == By.TAG_NAME:
    #             by = By.CSS_SELECTOR
    #         elif by == By.CLASS_NAME:
    #             by = By.CSS_SELECTOR
    #             value = ".%s" % value
    #         elif by == By.NAME:
    #             by = By.CSS_SELECTOR
    #             value = '[name="%s"]' % value

    #     # Return empty list if driver returns null
    #     # See https://github.com/SeleniumHQ/selenium/issues/4555
    #     return self.execute(Command.FIND_ELEMENTS, {
    #         'using': by,
    #         'value': value})['value'] or []

    # @property
    # def desired_capabilities(self):
    #     """
    #     returns the drivers current desired capabilities being used
    #     """
    #     return self.capabilities

    # def get_screenshot_as_file(self, filename):
    #     """
    #     Saves a screenshot of the current window to a PNG image file. Returns
    #        False if there is any IOError, else returns True. Use full paths in
    #        your filename.

    #     :Args:
    #      - filename: The full path you wish to save your screenshot to. This
    #        should end with a `.png` extension.

    #     :Usage:
    #         driver.get_screenshot_as_file('/Screenshots/foo.png')
    #     """
    #     if not filename.lower().endswith('.png'):
    #         warnings.warn("name used for saved screenshot does not match file "
    #                       "type. It should end with a `.png` extension", UserWarning)
    #     png = self.get_screenshot_as_png()
    #     try:
    #         with open(filename, 'wb') as f:
    #             f.write(png)
    #     except IOError:
    #         return False
    #     finally:
    #         del png
    #     return True

    # def save_screenshot(self, filename):
    #     """
    #     Saves a screenshot of the current window to a PNG image file. Returns
    #        False if there is any IOError, else returns True. Use full paths in
    #        your filename.

    #     :Args:
    #      - filename: The full path you wish to save your screenshot to. This
    #        should end with a `.png` extension.

    #     :Usage:
    #         driver.save_screenshot('/Screenshots/foo.png')
    #     """
    #     return self.get_screenshot_as_file(filename)

    # def get_screenshot_as_png(self):
    #     """
    #     Gets the screenshot of the current window as a binary data.

    #     :Usage:
    #         driver.get_screenshot_as_png()
    #     """
    #     return base64.b64decode(self.get_screenshot_as_base64().encode('ascii'))

    # def get_screenshot_as_base64(self):
    #     """
    #     Gets the screenshot of the current window as a base64 encoded string
    #        which is useful in embedded images in HTML.

    #     :Usage:
    #         driver.get_screenshot_as_base64()
    #     """
    #     return self.execute(Command.SCREENSHOT)['value']

    # def set_window_size(self, width, height, windowHandle='current'):
    #     """
    #     Sets the width and height of the current window. (window.resizeTo)

    #     :Args:
    #      - width: the width in pixels to set the window to
    #      - height: the height in pixels to set the window to

    #     :Usage:
    #         driver.set_window_size(800,600)
    #     """
    #     if self.w3c:
    #         if windowHandle != 'current':
    #             warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
    #         self.set_window_rect(width=int(width), height=int(height))
    #     else:
    #         self.execute(Command.SET_WINDOW_SIZE, {
    #             'width': int(width),
    #             'height': int(height),
    #             'windowHandle': windowHandle})

    # def get_window_size(self, windowHandle='current'):
    #     """
    #     Gets the width and height of the current window.

    #     :Usage:
    #         driver.get_window_size()
    #     """
    #     command = Command.GET_WINDOW_SIZE
    #     if self.w3c:
    #         if windowHandle != 'current':
    #             warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
    #         size = self.get_window_rect()
    #     else:
    #         size = self.execute(command, {'windowHandle': windowHandle})

    #     if size.get('value', None) is not None:
    #         size = size['value']

    #     return {k: size[k] for k in ('width', 'height')}

    # def set_window_position(self, x, y, windowHandle='current'):
    #     """
    #     Sets the x,y position of the current window. (window.moveTo)

    #     :Args:
    #      - x: the x-coordinate in pixels to set the window position
    #      - y: the y-coordinate in pixels to set the window position

    #     :Usage:
    #         driver.set_window_position(0,0)
    #     """
    #     if self.w3c:
    #         if windowHandle != 'current':
    #             warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
    #         return self.set_window_rect(x=int(x), y=int(y))
    #     else:
    #         self.execute(Command.SET_WINDOW_POSITION,
    #                      {
    #                          'x': int(x),
    #                          'y': int(y),
    #                          'windowHandle': windowHandle
    #                      })

    # def get_window_position(self, windowHandle='current'):
    #     """
    #     Gets the x,y position of the current window.

    #     :Usage:
    #         driver.get_window_position()
    #     """
    #     if self.w3c:
    #         if windowHandle != 'current':
    #             warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
    #         position = self.get_window_rect()
    #     else:
    #         position = self.execute(Command.GET_WINDOW_POSITION,
    #                                 {'windowHandle': windowHandle})['value']

    #     return {k: position[k] for k in ('x', 'y')}

    # def get_window_rect(self):
    #     """
    #     Gets the x, y coordinates of the window as well as height and width of
    #     the current window.

    #     :Usage:
    #         driver.get_window_rect()
    #     """
    #     return self.execute(Command.GET_WINDOW_RECT)['value']

    # def set_window_rect(self, x=None, y=None, width=None, height=None):
    #     """
    #     Sets the x, y coordinates of the window as well as height and width of
    #     the current window.

    #     :Usage:
    #         driver.set_window_rect(x=10, y=10)
    #         driver.set_window_rect(width=100, height=200)
    #         driver.set_window_rect(x=10, y=10, width=100, height=200)
    #     """
    #     if (x is None and y is None) and (height is None and width is None):
    #         raise InvalidArgumentException("x and y or height and width need values")

    #     return self.execute(Command.SET_WINDOW_RECT, {"x": x, "y": y,
    #                                                   "width": width,
    #                                                   "height": height})['value']

    # @property
    # def file_detector(self):
    #     return self._file_detector

    # @file_detector.setter
    # def file_detector(self, detector):
    #     """
    #     Set the file detector to be used when sending keyboard input.
    #     By default, this is set to a file detector that does nothing.

    #     see FileDetector
    #     see LocalFileDetector
    #     see UselessFileDetector

    #     :Args:
    #      - detector: The detector to use. Must not be None.
    #     """
    #     if detector is None:
    #         raise WebDriverException("You may not set a file detector that is null")
    #     if not isinstance(detector, FileDetector):
    #         raise WebDriverException("Detector has to be instance of FileDetector")
    #     self._file_detector = detector

    # @property
    # def orientation(self):
    #     """
    #     Gets the current orientation of the device

    #     :Usage:
    #         orientation = driver.orientation
    #     """
    #     return self.execute(Command.GET_SCREEN_ORIENTATION)['value']

    # @orientation.setter
    # def orientation(self, value):
    #     """
    #     Sets the current orientation of the device

    #     :Args:
    #      - value: orientation to set it to.

    #     :Usage:
    #         driver.orientation = 'landscape'
    #     """
    #     allowed_values = ['LANDSCAPE', 'PORTRAIT']
    #     if value.upper() in allowed_values:
    #         self.execute(Command.SET_SCREEN_ORIENTATION, {'orientation': value})
    #     else:
    #         raise WebDriverException("You can only set the orientation to 'LANDSCAPE' and 'PORTRAIT'")

    # @property
    # def application_cache(self):
    #     """ Returns a ApplicationCache Object to interact with the browser app cache"""
    #     return ApplicationCache(self)

    # @property
    # def log_types(self):
    #     """
    #     Gets a list of the available log types

    #     :Usage:
    #         driver.log_types
    #     """
    #     return self.execute(Command.GET_AVAILABLE_LOG_TYPES)['value']

    # def get_log(self, log_type):
    #     """
    #     Gets the log for a given log type

    #     :Args:
    #      - log_type: type of log that which will be returned

    #     :Usage:
    #         driver.get_log('browser')
    #         driver.get_log('driver')
    #         driver.get_log('client')
    #         driver.get_log('server')
    #     """
    #     return self.execute(Command.GET_LOG, {'type': log_type})['value']
