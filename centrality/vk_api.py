import requests
from time import time, sleep
from tqdm import tqdm

class Vk():
    def __init__(self, access_token=None):
        if not access_token:
            with open('access_token.txt') as f:
                access_token = f.read()
        self.access_token = access_token
        self.last_request = 0

        self.base_url = 'https://api.vk.com/method/'

    def dict_to_query(self, d):
        return '&'.join((f'{i[0]}={i[1]}' for i in d.items()))

    def wait_if_necessary(self):
        if time() - self.last_request <= 0.35:
            sleep(0.35 - (time() - self.last_request))


    def request(self, method, params):
        url = f'{self.base_url}{method}?{self.dict_to_query(params)}&access_token={self.access_token}&v=5.131'
        self.wait_if_necessary()
        self.last_request = time()
        return requests.get(url).json()['response']
        

    def get_user_friends(self, user_id):
        return self.request('friends.get', {'user_id':user_id})


def get_all_friends(start_list):
    vk = Vk()
    queue = start_list
    # Ищем всех друзей первого и второго рукопожатия. Если в очереди
    # очередной элемент - None, то считается, что перешли на следующий
    # уровень рукопожатия
    queue.append(None)
    max_rounds = 0
    _round = 0
    result = {}
    bar = tqdm()
    while len(queue) > 0:
        user = queue.pop(0)
        if not user:
            if _round >= max_rounds:
                break
            print('new round')
            _round += 1
            queue.append(None)
            continue
        result.setdefault(user, set())
        try:
            friends = vk.get_user_friends(user)['items']
            result[user] = set(friends)
            for f in friends:
                if f not in result and f not in queue:
                    queue.append(f)
        except Exception as e:
            # print(e)
            pass
        bar.update()

    return result


start_list = [
    96272105,
    198245847,
    209580238,
    58499883,
    248925812,
    93047688,
    203309613,
    225067605,
    87846703,
    386101283,
    275831361,
    222110446,
    98789579,
    172039039,
    466026608,
    470872693,
    51345081,
    159891320,
    166062413,
    176839273,
    193172908,
    152920018,
    174001824,
    100429433,
    183090306,
    117653847,
    73182682,
]
    

if __name__ == '__main__':
    res = get_all_friends(start_list)
