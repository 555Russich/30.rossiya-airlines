from pathlib import Path
import asyncio
import ssl

from aiohttp import ClientSession, TCPConnector

from my_logging import get_logger


class Scraper:
    _headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://edu.rossiya-airlines.com',
        'Connection': 'keep-alive',
        # 'Referer': 'https://edu.rossiya-airlines.com/workplan/',
        # 'Cookie': 'PHPSESSID=4on83o44g6hs2dbpoovjbt5jbh',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }
    _ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    print(_ssl_context.options)
    _ssl_context.options |= 0x4  # https://stackoverflow.com/a/71646353/15637940
    print(_ssl_context.options)

    async def __aenter__(self):
        # conn = TCPConnector(ssl=self._ssl_context)
        self.session = await ClientSession().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get_workplan_page(self):
        cookies = {
            'PHPSESSID': '4on83o44g6hs2dbpoovjbt5jbh',
        }

        data = {
            'dateFrom': '01.05.2023',
            'time_type': 'UTC',
        }

        async with self.session.post(
            url='http://edu.rossiya-airlines.com/workplan/',
            # cookies=cookies,
            # headers=self._headers,
            ssl=self._ssl_context,
            # data=data,
        ) as response:
            print(response)


async def main():
    async with Scraper() as scraper:
        await scraper.get_workplan_page()


if __name__ == '__main__':
    get_logger(Path('scraper.log'))
    asyncio.run(main())
