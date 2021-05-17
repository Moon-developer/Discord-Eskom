from ssl import create_default_context

from aiohttp.client_exceptions import ClientConnectorError, ServerDisconnectedError
from aiohttp_retry import RetryClient, ExponentialRetry


class EskomInterface:
    """Interface class to obtain load-shedding information using the Eskom API"""

    def __init__(self):
        """Initializes class parameters"""
        self.base_url = "https://loadshedding.eskom.co.za/LoadShedding"
        self.headers = {
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0"
        }
        self.ssl_context = create_default_context()
        self.ssl_context.set_ciphers("DEFAULT@SECLEVEL=1")

    async def async_query_api(self, endpoint, payload=None):
        """
        Queries a given endpoint on the Eskom loadshedding API with the specified payload and takes timeouts
        and connection losts into account with a Retry method.

        :param endpoint: The endpoint of the Eskom API
        :param payload: The parameters to apply to the query. Defaults to None.
        :return: The response object from the request
        """
        async with RetryClient() as client:
            async with client.get(
                    url=self.base_url + endpoint,
                    headers=self.headers,
                    params=payload,
                    ssl=self.ssl_context,
                    retry_options=ExponentialRetry(
                        attempts=50,
                        exceptions={
                            ClientConnectorError,
                            ServerDisconnectedError,
                            ConnectionError,
                            OSError,
                        }),
            ) as res:
                return await res.json()

    async def async_get_stage(self, attempts=30):
        """
        Get the current stage from the eskom site at `/GetStatus` endpoint
        :param attempts:
        :return:
        """
        api_result = None
        for attempt in range(attempts):
            res = await self.async_query_api('/GetStatus')
            if res:
                api_result = res
                if int(res) > 0:
                    return int(res) - 1
        if api_result:
            return 0
        else:
            print(f'Error, no response received from API after {attempts} attempts')
