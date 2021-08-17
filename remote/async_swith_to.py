from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.switch_to import SwitchTo, basestring
from asyncselenium.common.async_alert import AsyncAlert
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, NoSuchFrameException, NoSuchWindowException

class AsyncSwithTo(SwitchTo):

    @property
    async def active_element(self):
        """
        Returns the element with focus, or BODY if nothing has focus.

        :Usage:
            element = driver.switch_to.active_element
        """
        if self._driver.w3c:
            return (await self._driver.execute(Command.W3C_GET_ACTIVE_ELEMENT))['value']
        else:
            return (await self._driver.execute(Command.GET_ACTIVE_ELEMENT))['value']
    
    @property
    async def alert(self):
        """
        Switches focus to an alert on the page.

        :Usage:
            alert = driver.switch_to.alert
        """
        alert = AsyncAlert(self._driver)
        await alert.text
        return alert

    async def default_content(self):
        """
        Switch focus to the default frame.

        :Usage:
            driver.switch_to.default_content()
        """
        await self._driver.execute(Command.SWITCH_TO_FRAME, {'id': None})

    async def frame(self, frame_reference):
        """
        Switches focus to the specified frame, by index, name, or webelement.

        :Args:
         - frame_reference: The name of the window to switch to, an integer representing the index,
                            or a webelement that is an (i)frame to switch to.

        :Usage:
            driver.switch_to.frame('frame_name')
            driver.switch_to.frame(1)
            driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])
        """
        if isinstance(frame_reference, basestring) and self._driver.w3c:
            try:
                frame_reference = await self._driver.find_element(By.ID, frame_reference)
            except NoSuchElementException:
                try:
                    frame_reference = await self._driver.find_element(By.NAME, frame_reference)
                except NoSuchElementException:
                    raise NoSuchFrameException(frame_reference)

        await self._driver.execute(Command.SWITCH_TO_FRAME, {'id': frame_reference})

    async def parent_frame(self):
        """
        Switches focus to the parent context. If the current context is the top
        level browsing context, the context remains unchanged.

        :Usage:
            driver.switch_to.parent_frame()
        """
        await self._driver.execute(Command.SWITCH_TO_PARENT_FRAME)

    async def window(self, window_name):
        """
        Switches focus to the specified window.

        :Args:
         - window_name: The name or window handle of the window to switch to.

        :Usage:
            driver.switch_to.window('main')
        """
        if self._driver.w3c:
            await self._w3c_window(window_name)
            return
        data = {'name': window_name}
        await self._driver.execute(Command.SWITCH_TO_WINDOW, data)

    async def _w3c_window(self, window_name):
        async def send_handle(h):
            await self._driver.execute(Command.SWITCH_TO_WINDOW, {'handle': h})

        try:
            # Try using it as a handle first.
            await send_handle(window_name)
        except NoSuchWindowException as e:
            # Check every window to try to find the given window name.
            original_handle = await self._driver.current_window_handle
            handles = await self._driver.window_handles
            for handle in handles:
                await send_handle(handle)
                current_name = await self._driver.execute_script('return window.name')
                if window_name == current_name:
                    return
            await send_handle(original_handle)
            raise e
