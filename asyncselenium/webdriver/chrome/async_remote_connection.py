from asyncselenium.webdriver.remote.async_remote_connection import AsyncRemoteConnection

class AsyncChromeConnection(AsyncRemoteConnection):

    def __init__(self, remote_server_addr, keep_alive=True):
        AsyncRemoteConnection.__init__(self, remote_server_addr, keep_alive)
        self._commands["launchApp"] = ('POST', '/session/$sessionId/chromium/launch_app')
        self._commands["setNetworkConditions"] = ('POST', '/session/$sessionId/chromium/network_conditions')
        self._commands["getNetworkConditions"] = ('GET', '/session/$sessionId/chromium/network_conditions')
        self._commands['executeCdpCommand'] = ('POST', '/session/$sessionId/goog/cdp/execute')
