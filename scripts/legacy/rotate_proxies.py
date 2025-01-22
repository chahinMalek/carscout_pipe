import json
import requests
from itertools import cycle


if __name__ == '__main__':

    proxies_pool = [
        '161.53.129.23:3128',
        '145.40.121.73:3128',
    ]
    url = 'https://httpbin.org/ip'

    for i in range(len(proxies_pool)):
        proxy = proxies_pool[i]
        try:
            response = requests.get(
                url, 
                proxies={'http': proxy, 'https': proxy}, 
                timeout=30
            )
            print(f"{proxy} - Success: {json.loads(response.text).get('origin')}")
        except Exception as err:
            print(f'{proxy} - Connection refused: {err.__class__.__name__}')