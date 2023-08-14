import logging
import ssl
import json
from re import compile
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup

from config import FILEPATH_CA, DIR_REPORTS
from my_logging import log_and_print


@dataclass
class Flight:
    id_para: int
    min_para_date_local: str
    info: int = 1
    comment: str = ''
    plan_type: int = 1

    def dict(self) -> dict[str, str]:
        return {k: str(v) for k, v in self.__dict__.items()}

    def json(self) -> str:
        return json.dumps(self.dict())


class Scraper:
    _ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=str(FILEPATH_CA))
    _ssl_context.options |= 0x4  # https://stackoverflow.com/a/71646353/15637940

    def __init__(self, login: str, password: str):
        self._login = login
        self._password = password

    @property
    def main_page_data(self):
        return f'-----------------------------809499292195008333228646371\r\nContent-Disposition: form-data; name="referer"\r\n\r\nhttps://edu.rossiya-airlines.com//\r\n-----------------------------809499292195008333228646371\r\nContent-Disposition: form-data; name="login"\r\n\r\n1\r\n-----------------------------809499292195008333228646371\r\nContent-Disposition: form-data; name="user_id"\r\n\r\n\r\n-----------------------------809499292195008333228646371\r\nContent-Disposition: form-data; name="backend_url"\r\n\r\nhttps://sup.rossiya-airlines.com:8080\r\n-----------------------------809499292195008333228646371\r\nContent-Disposition: form-data; name="username"\r\n\r\n{self._login}\r\n-----------------------------809499292195008333228646371\r\nContent-Disposition: form-data; name="userpass"\r\n\r\n{self._password}\r\n-----------------------------809499292195008333228646371\r\nContent-Disposition: form-data; name="domain"\r\n\r\nstc.local\r\n-----------------------------809499292195008333228646371\r\nContent-Disposition: form-data; name="submit"\r\n\r\nвойти\r\n-----------------------------809499292195008333228646371--\r\n'.encode()

    async def authorize(self) -> None:
        async with self.session.post(
            'https://sup.rossiya-airlines.com:8080/api/login',
                json={'login': self._login, 'password': self._password, 'app_name': 'LinksDesktop'},
        ) as resp:
            json = await resp.json()
            assert not json.get('error'), f'Authorization FAILED!\n{json=}'

    async def post_main_page(self) -> None:
        async with self.session.post(
                'https://edu.rossiya-airlines.com/',
                headers={
                    'Content-Type': 'multipart/form-data;'
                                    ' boundary=---------------------------809499292195008333228646371',
                },
                data=self.main_page_data
        ):
            pass

    async def get_workplan_page(self, date_from: str):
        async with self.session.post(
            url='https://edu.rossiya-airlines.com/workplan/',
            data={'dateFrom': date_from, 'time_type': 'UTC'},
        ) as response:
            return await response.text()

    async def get_one_flight_page(self, flight: Flight) -> str:
        async with self.session.post(
                'https://edu.rossiya-airlines.com/workplan/view-1/ajax-1',
                data=flight.dict()
        ) as resp:
            return await resp.text()

    async def download_file(self, url: str) -> None:
        async with self.session.get(url) as resp:
            with open(DIR_REPORTS / self.get_filename_from_url(url), 'wb') as f:
                f.write(await resp.read())

    @staticmethod
    def get_filename_from_url(url: str) -> str:
        parsed_url = urlparse(url)
        qs = parse_qs(parsed_url.query)
        dt = qs.get('flight_date')[0].replace('-', '_')
        n = qs.get('flight_number')[0]
        return f'flight_report__{dt}__{n}.xlsx'

    async def __aenter__(self):
        conn = TCPConnector(ssl=self._ssl_context)
        self.session = await ClientSession(connector=conn).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()


class Parser:
    re_flights = compile(r'(?<=work_plan\(\')(\d+)\',\'(.+)(?=\')')
    re_report_hrefs = compile(r'(?<=window\.open\(\').+?(?=\')')

    def __init__(self, html: str):
        self._soup = BeautifulSoup(html, 'lxml')

    def get_flights(self) -> list[Flight]:
        flights = []

        for button in self._soup.find('div', 'info_block hronology').find_all(
                'button', class_='btn btn-sm btn-info'):
            reg_res = self.re_flights.search(button.get('onclick'))
            flight = Flight(id_para=reg_res.group(1), min_para_date_local=reg_res.group(2))

            if flight not in flights:
                flights.append(flight)

        return flights

    def get_flight_report_hrefs(self) -> list[str]:
        hrefs = []

        for button in self._soup.find_all('button', {'title': 'Отчёт по рейсу'}):
            onclick = button.get('onclick')
            if onclick:
                reg_res = self.re_report_hrefs.search(onclick)
                if reg_res:
                    href = reg_res.group(0)
                    if href not in hrefs:
                        hrefs.append(href)
        
        return hrefs


async def download_reports_for_month(
        login: str,
        password: str,
        month: str
) -> None:
    try:
        await _download_reports_for_month(login=login, password=password, month=month)
    except Exception as e:
        logging.error(e, exc_info=True)
        raise e


async def _download_reports_for_month(
        login: str,
        password: str,
        month: str
) -> None:
    async with Scraper(login=login, password=password) as scraper:
        await scraper.authorize()
        log_and_print('Authorized successfully')
        await scraper.post_main_page()
        log_and_print('Sent request to main page for updating cookies')

        html_workplan = await scraper.get_workplan_page(date_from=month)
        log_and_print('Got month workplan page')
        flights = Parser(html_workplan).get_flights()

        if not flights:
            return log_and_print(f'Empty list of flights for {month=}')

        for i, flight in enumerate(flights, start=1):
            html_flight = await scraper.get_one_flight_page(flight)
            hrefs = Parser(html_flight).get_flight_report_hrefs()
            urls = [f'https://edu.rossiya-airlines.com{href}' for href in hrefs]
            log_and_print(f'{i}/{len(flights)} | Parsed {len(urls)=}')

            for url in urls:
                log_and_print(f'Start downloading {url=}')
                await scraper.download_file(url)