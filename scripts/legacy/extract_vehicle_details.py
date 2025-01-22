import requests
from bs4 import BeautifulSoup
from configs.headers import DEFAULT_REQUEST_HEADERS


if __name__ == '__main__':

    request_url = 'https://www.olx.ba/artikal/50642985/audi-a1-1-6-tdi-2012-godina-alu-felge-park-senzori/'
    response = requests.get(
        request_url, headers=DEFAULT_REQUEST_HEADERS
    )
    response = BeautifulSoup(response.text, features='html.parser')
    print(response)
