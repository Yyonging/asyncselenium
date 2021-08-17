from selenium.webdriver.common.alert import Alert
from selenium.webdriver.remote.command import Command
from selenium.webdriver.common.utils import keys_to_typing

class AsyncAlert(Alert):

    @property
    async def text(self):
        """
        Gets the text of the Alert.
        """
        if self.driver.w3c:
            return (await self.driver.execute(Command.W3C_GET_ALERT_TEXT))["value"]
        else:
            return (await self.driver.execute(Command.GET_ALERT_TEXT))["value"]

    async def dismiss(self):
        """
        Dismisses the alert available.
        """
        if self.driver.w3c:
            await self.driver.execute(Command.W3C_DISMISS_ALERT)
        else:
            await self.driver.execute(Command.DISMISS_ALERT)

    async def accept(self):
        """
        Accepts the alert available.

        Usage::
        Alert(driver).accept() # Confirm a alert dialog.
        """
        if self.driver.w3c:
            await self.driver.execute(Command.W3C_ACCEPT_ALERT)
        else:
            await self.driver.execute(Command.ACCEPT_ALERT)

    async def send_keys(self, keysToSend):
        """
        Send Keys to the Alert.

        :Args:
         - keysToSend: The text to be sent to Alert.


        """
        if self.driver.w3c:
            await self.driver.execute(Command.W3C_SET_ALERT_VALUE, {'value': keys_to_typing(keysToSend),
                                                              'text': keysToSend})
        else:
            await self.driver.execute(Command.SET_ALERT_VALUE, {'text': keysToSend})
