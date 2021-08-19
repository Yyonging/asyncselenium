from asyncselenium.webdriver.remote.async_webelement import AsyncWebElement
from asyncselenium.webdriver.remote.async_object import Asyncobject
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, UnexpectedTagNameException
from selenium.webdriver.support.select import Select

class AsyncSelect(Asyncobject, Select):

    async def __init__(self, webelement: AsyncWebElement):
        tag_name = await webelement.tag_name
        if tag_name.lower() != "select":
            raise UnexpectedTagNameException(
                    "Select only works on <select> elements, not on <%s>" %
                tag_name)
        self._el = webelement
        multi = await self._el.get_attribute("multiple")
        self.is_multiple = multi and multi != "false"

    @property
    async def options(self):
        """Returns a list of all options belonging to this select tag"""
        return await self._el.find_elements(By.TAG_NAME, 'option')
    
    @property
    async def all_selected_options(self):
        """Returns a list of all selected options belonging to this select tag"""
        ret = []
        options = await self.options
        for opt in options:
            if (await opt.is_selected()):
                ret.append(opt)
        return ret
    
    async def select_by_value(self, value):
        """Select all options that have a value matching the argument. That is, when given "foo" this
           would select an option like:

           <option value="foo">Bar</option>

           :Args:
            - value - The value to match against

           throws NoSuchElementException If there is no option with specisied value in SELECT
           """
        css = "option[value =%s]" % self._escapeString(value)
        opts = await self._el.find_elements(By.CSS_SELECTOR, css)
        matched = False
        for opt in opts:
            await self._setSelected(opt)
            if not self.is_multiple:
                return
            matched = True
        if not matched:
            raise NoSuchElementException("Cannot locate option with value: %s" % value)

    async def _setSelected(self, option):
        if not (await option.is_selected()):
            await option.click()

    async def _unsetSelected(self, option):
        if (await option.is_selected()):
            await option.click()
