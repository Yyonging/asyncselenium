from selenium.webdriver.remote.mobile import Mobile
from selenium.webdriver.remote.command import Command

class AsyncMobile(Mobile):

    @property
    async def network_connection(self):
        return self.ConnectionType((await self._driver.execute(Command.GET_NETWORK_CONNECTION))['value'])
    
    async def set_network_connection(self, network):
        """
        Set the network connection for the remote device.

        Example of setting airplane mode::

            driver.mobile.set_network_connection(driver.mobile.AIRPLANE_MODE)
        """
        mode = network.mask if isinstance(network, self.ConnectionType) else network
        return self.ConnectionType((await self._driver.execute(
            Command.SET_NETWORK_CONNECTION, {
                'name': 'network_connection',
                'parameters': {'type': mode}}))['value'])
    
    @property
    async def context(self):
        """
        returns the current context (Native or WebView).
        """
        return await self._driver.execute(Command.CURRENT_CONTEXT_HANDLE)

    @property
    async def contexts(self):
        """
        returns a list of available contexts
        """
        return await self._driver.execute(Command.CONTEXT_HANDLES)

    @context.setter
    async def context(self, new_context):
        """
        sets the current context
        """
        await self._driver.execute(Command.SWITCH_TO_CONTEXT, {"name": new_context})
