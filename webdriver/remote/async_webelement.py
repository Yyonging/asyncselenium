import base64
import warnings
import zipfile
import os

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.command import Command
from selenium.webdriver.common.utils import keys_to_typing
from selenium.webdriver.remote.webelement import getAttribute_js, isDisplayed_js, IOStream
from selenium.common.exceptions import WebDriverException

class AsyncWebElement(WebElement):

    @property
    async def tag_name(self) -> str:
        """This element's ``tagName`` property."""
        return (await self._execute(Command.GET_ELEMENT_TAG_NAME))['value']

    @property
    async def text(self) -> str:
        """The text of the element."""
        return (await self._execute(Command.GET_ELEMENT_TEXT))['value']

    async def click(self) -> None:
        """Clicks the element."""
        await self._execute(Command.CLICK_ELEMENT)

    async def submit(self) -> None:
        """Submits a form."""
        if self._w3c:
            form = await self.find_element(By.XPATH, "./ancestor-or-self::form")
            await self._parent.execute_script(
                "var e = arguments[0].ownerDocument.createEvent('Event');"
                "e.initEvent('submit', true, true);"
                "if (arguments[0].dispatchEvent(e)) { arguments[0].submit() }", form)
        else:
            await self._execute(Command.SUBMIT_ELEMENT)

    async def clear(self) -> None:
        """Clears the text if it's a text entry element."""
        await self._execute(Command.CLEAR_ELEMENT)

    async def get_property(self, name: str):
        """
        Gets the given property of the element.

        :Args:
            - name - Name of the property to retrieve.

        Example::

            text_length = target_element.get_property("text_length")
        """
        try:
            return (await self._execute(Command.GET_ELEMENT_PROPERTY, {"name": name}))["value"]
        except WebDriverException:
            # if we hit an end point that doesnt understand getElementProperty lets fake it
            return await self.parent.execute_script('return arguments[0][arguments[1]]', self, name)

    async def get_attribute(self, name: str):
        """Gets the given attribute or property of the element.

        This method will first try to return the value of a property with the
        given name. If a property with that name doesn't exist, it returns the
        value of the attribute with the same name. If there's no attribute with
        that name, ``None`` is returned.

        Values which are considered truthy, that is equals "true" or "false",
        are returned as booleans.  All other non-``None`` values are returned
        as strings.  For attributes or properties which do not exist, ``None``
        is returned.

        :Args:
            - name - Name of the attribute/property to retrieve.

        Example::

            # Check if the "active" CSS class is applied to an element.
            is_active = "active" in target_element.get_attribute("class")

        """

        attributeValue = ''
        if self._w3c:
            attributeValue = await self.parent.execute_script(
                "return (%s).apply(null, arguments);" % getAttribute_js,
                self, name)
        else:
            resp = await self._execute(Command.GET_ELEMENT_ATTRIBUTE, {'name': name})
            attributeValue = resp.get('value')
            if attributeValue is not None:
                if name != 'value' and attributeValue.lower() in ('true', 'false'):
                    attributeValue = attributeValue.lower()
        return attributeValue

    async def is_selected(self):
        """Returns whether the element is selected.

        Can be used to check if a checkbox or radio button is selected.
        """
        return (await self._execute(Command.IS_ELEMENT_SELECTED))['value']

    async def is_enabled(self):
        """Returns whether the element is enabled."""
        return (await self._execute(Command.IS_ELEMENT_ENABLED))['value']

    async def send_keys(self, *value):
        """Simulates typing into the element.

        :Args:
            - value - A string for typing, or setting form fields.  For setting
              file inputs, this could be a local file path.

        Use this to send simple key events or to fill out form fields::

            form_textfield = driver.find_element_by_name('username')
            form_textfield.send_keys("admin")

        This can also be used to set file inputs.

        ::

            file_input = driver.find_element_by_name('profilePic')
            file_input.send_keys("path/to/profilepic.gif")
            # Generally it's better to wrap the file path in one of the methods
            # in os.path to return the actual path to support cross OS testing.
            # file_input.send_keys(os.path.abspath("path/to/profilepic.gif"))

        """
        # transfer file to another machine only if remote driver is used
        # the same behaviour as for java binding
        if self.parent._is_remote:
            local_file = self.parent.file_detector.is_local_file(*value)
            if local_file is not None:
                value = self._upload(local_file)
        await self._execute(Command.SEND_KEYS_TO_ELEMENT,
                      {'text': "".join(keys_to_typing(value)),
                       'value': keys_to_typing(value)})

    async def is_displayed(self):
        """Whether the element is visible to a user."""
        # Only go into this conditional for browsers that don't use the atom themselves
        if self._w3c:
            return await self.parent.execute_script(
                "return (%s).apply(null, arguments);" % isDisplayed_js,
                self)
        else:
            return (await self._execute(Command.IS_ELEMENT_DISPLAYED))['value']

    @property
    async def location_once_scrolled_into_view(self):
        """THIS PROPERTY MAY CHANGE WITHOUT WARNING. Use this to discover
        where on the screen an element is so that we can click it. This method
        should cause the element to be scrolled into view.

        Returns the top lefthand corner location on the screen, or ``None`` if
        the element is not visible.

        """
        if self._w3c:
            old_loc = (await self._execute(Command.W3C_EXECUTE_SCRIPT, {
                'script': "arguments[0].scrollIntoView(true); return arguments[0].getBoundingClientRect()",
                'args': [self]}))['value']
            return {"x": round(old_loc['x']),
                    "y": round(old_loc['y'])}
        else:
            return (await self._execute(Command.GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW))['value']

    @property
    async def size(self):
        """The size of the element."""
        size = {}
        if self._w3c:
            size = (await self._execute(Command.GET_ELEMENT_RECT))['value']
        else:
            size = (await self._execute(Command.GET_ELEMENT_SIZE))['value']
        new_size = {"height": size["height"],
                    "width": size["width"]}
        return new_size

    @property
    async def location(self):
        """The location of the element in the renderable canvas."""
        if self._w3c:
            old_loc = (await self._execute(Command.GET_ELEMENT_RECT))['value']
        else:
            old_loc = (await self._execute(Command.GET_ELEMENT_LOCATION))['value']
        new_loc = {"x": round(old_loc['x']),
                   "y": round(old_loc['y'])}
        return new_loc

    @property
    async def rect(self):
        """A dictionary with the size and location of the element."""
        if self._w3c:
            return (await self._execute(Command.GET_ELEMENT_RECT))['value']
        else:
            rect = (await self.size).copy()
            rect.update(await self.location)
            return rect

    @property
    async def screenshot_as_base64(self):
        """
        Gets the screenshot of the current element as a base64 encoded string.

        :Usage:
            img_b64 = element.screenshot_as_base64
        """
        return (await self._execute(Command.ELEMENT_SCREENSHOT))['value']

    @property
    async def screenshot_as_png(self):
        """
        Gets the screenshot of the current element as a binary data.

        :Usage:
            element_png = element.screenshot_as_png
        """
        return base64.b64decode((await self.screenshot_as_base64).encode('ascii'))

    async def screenshot(self, filename):
        """
        Saves a screenshot of the current element to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            element.screenshot('/Screenshots/foo.png')
        """
        if not filename.lower().endswith('.png'):
            warnings.warn("name used for saved screenshot does not match file "
                          "type. It should end with a `.png` extension", UserWarning)
        png = await self.screenshot_as_png
        try:
            with open(filename, 'wb') as f:
                f.write(png)
        except IOError:
            return False
        finally:
            del png
        return True

    async def find_element(self, by=By.ID, value=None):
        """
        Find an element given a By strategy and locator. Prefer the find_element_by_* methods when
        possible.

        :Usage:
            element = element.find_element(By.ID, 'foo')

        :rtype: WebElement
        """
        if self._w3c:
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

        return (await self._execute(Command.FIND_CHILD_ELEMENT,
                                {"using": by, "value": value}))['value']

    async def find_elements(self, by=By.ID, value=None):
        """
        Find elements given a By strategy and locator. Prefer the find_elements_by_* methods when
        possible.

        :Usage:
            element = element.find_elements(By.CLASS_NAME, 'foo')

        :rtype: list of WebElement
        """
        if self._w3c:
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

        return (await self._execute(Command.FIND_CHILD_ELEMENTS,
                             {"using": by, "value": value}))['value']

    async def _upload(self, filename):
        fp = IOStream()
        zipped = zipfile.ZipFile(fp, 'w', zipfile.ZIP_DEFLATED)
        zipped.write(filename, os.path.split(filename)[1])
        zipped.close()
        content = base64.encodestring(fp.getvalue())
        if not isinstance(content, str):
            content = content.decode('utf-8')
        try:
            return await self._execute(Command.UPLOAD_FILE, {'file': content})['value']
        except WebDriverException as e:
            if "Unrecognized command: POST" in e.__str__():
                return filename
            elif "Command not found: POST " in e.__str__():
                return filename
            elif '{"status":405,"value":["GET","HEAD","DELETE"]}' in e.__str__():
                return filename
            else:
                raise e
