import warnings

from asyncselenium.webdriver.remote.async_webdriver import AsyncWebdriver
from asyncselenium.webdriver.chrome.async_remote_connection import AsyncChromeConnection
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class AsyncChromeDriver(AsyncWebdriver):

    async def __init__(self, executable_path="chromedriver", port=0,
                 options=None, service_args=None,
                 desired_capabilities=None, service_log_path=None,
                 chrome_options=None, keep_alive=True, service: Service=None, session_id=None):
        """
        Creates a new instance of the chrome driver.

        Starts the service and then creates new instance of chrome driver.

        :Args:
         - executable_path - path to the executable. If the default is used it assumes the executable is in the $PATH
         - port - port you would like the service to run, if left as 0, a free port will be found.
         - options - this takes an instance of ChromeOptions
         - service_args - List of args to pass to the driver service
         - desired_capabilities - Dictionary object with non-browser specific
           capabilities only, such as "proxy" or "loggingPref".
         - service_log_path - Where to log information from the driver.
         - chrome_options - Deprecated argument for options
         - keep_alive - Whether to configure ChromeRemoteConnection to use HTTP keep-alive.
        """
        if chrome_options:
            warnings.warn('use options instead of chrome_options',
                          DeprecationWarning, stacklevel=2)
            options = chrome_options

        if options is None:
            # desired_capabilities stays as passed in
            if desired_capabilities is None:
                desired_capabilities = self.create_options().to_capabilities()
        else:
            if desired_capabilities is None:
                desired_capabilities = options.to_capabilities()
            else:
                desired_capabilities.update(options.to_capabilities())
        self.service = service
        if not service:
            self.service = Service(
                executable_path,
                port=port,
                service_args=service_args,
                log_path=service_log_path)
            self.service.start()

        try:
            await AsyncWebdriver.__init__(
                self,
                command_executor=AsyncChromeConnection(
                    remote_server_addr=self.service.service_url,
                    keep_alive=keep_alive),
                desired_capabilities=desired_capabilities, session_id=session_id)
        except Exception:
            self.quit()
            raise
        self._is_remote = False

    @staticmethod
    def get_service(executable_path='chromedriver', port=0, service_args=None, service_log_path=None):
        service = Service(
                executable_path,
                port=port,
                service_args=service_args,
                log_path=service_log_path)
        service.start()
        return service

    async def launch_app(self, id):
        """Launches Chrome app specified by id."""
        return await self.execute("launchApp", {'id': id})

    async def get_network_conditions(self):
        """
        Gets Chrome network emulation settings.

        :Returns:
            A dict. For example:

            {'latency': 4, 'download_throughput': 2, 'upload_throughput': 2,
            'offline': False}

        """
        return await self.execute("getNetworkConditions")['value']

    async def set_network_conditions(self, **network_conditions):
        """
        Sets Chrome network emulation settings.

        :Args:
         - network_conditions: A dict with conditions specification.

        :Usage:
            driver.set_network_conditions(
                offline=False,
                latency=5,  # additional latency (ms)
                download_throughput=500 * 1024,  # maximal throughput
                upload_throughput=500 * 1024)  # maximal throughput

            Note: 'throughput' can be used to set both (for download and upload).
        """
        await self.execute("setNetworkConditions", {
            'network_conditions': network_conditions
        })

    async def execute_cdp_cmd(self, cmd, cmd_args):
        """
        Execute Chrome Devtools Protocol command and get returned result

        The command and command args should follow chrome devtools protocol domains/commands, refer to link
        https://chromedevtools.github.io/devtools-protocol/

        :Args:
         - cmd: A str, command name
         - cmd_args: A dict, command args. empty dict {} if there is no command args

        :Usage:
            driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': requestId})

        :Returns:
            A dict, empty dict {} if there is no result to return.
            For example to getResponseBody:

            {'base64Encoded': False, 'body': 'response body string'}

        """
        return await self.execute("executeCdpCommand", {'cmd': cmd, 'params': cmd_args})['value']

    async def quit(self, stop_service=True):
        """
        Closes the browser and shuts down the ChromeDriver executable
        that is started when starting the ChromeDriver
        """
        try:
            await AsyncWebdriver.quit(self)
        except Exception:
            # We don't care about the message because something probably has gone wrong
            pass
        finally:
            if stop_service:
                self.service.stop()

    def stop_service(self):
        self.service.stop()

    def create_options(self):
        return Options()