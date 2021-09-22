from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import urllib.parse
import re
import json
import collections
import time
from flask import Flask, make_response


def get_search_value(ptn, text):
    res = re.search(ptn, text)

    if res:
        return res.group(1)
    else:
        return None


def get_search_values(ptn, text):
    res = re.search(ptn, text)

    if res:
        return res.groups()
    else:
        return None


def get_price_set(driver_obj):
    buf = []
    count = 1
    while True:
        try:
            price_str = driver_obj.find_element_by_xpath(
                f'//*[@id="__layout"]/div/main/div[2]/div[1]/div[3]/div[2]/div[1]/div[2]/div/table/tbody/tr[2]/td/p[{count}]/span[1]').text \
                        + ' ' + driver_obj.find_element_by_xpath(
                f'//*[@id="__layout"]/div/main/div[2]/div[1]/div[3]/div[2]/div[1]/div[2]/div/table/tbody/tr[2]/td/p[{count}]/span[2]').text
        except NoSuchElementException:
            break
        else:
            buf.append(list(price_str.split()))
            count += 1
    return buf


def scraping(name, driver):
    print('processing...')
    now_time = time.time()
    url = 'https://www.its-mo.com/search/' + urllib.parse.quote(name) + '/'
    driver.get(url)

    try:
        # Get the parking page
        html = driver.page_source
        data_str = get_search_value('window.__NUXT__=(.*);</script>', html)
        code = get_search_value('content:(.*?),todcode:', data_str)
        if len(code) > 1:
            code = get_search_value('"PPK_(.*?)"', code)
        else:
            code = get_search_value(r'config:\{\}\}\}.*,"PPK_(.*?)"', data_str)
        query_code = 'PPK_' + code + '-' + get_search_value('code:"(.*?)",point', data_str)
        url = 'https://www.its-mo.com/poi/' + urllib.parse.quote(query_code) + '/'

        # Get the near parking list
        driver.get(url)
        price_set = get_price_set(driver)

        html = driver.page_source
        data_str = get_search_value('window.__NUXT__=(.*);</script>', html)
        buf_str = get_search_value(r'nearPois:\[(.*?)\]', data_str)
        nearpoi_list = []
        while True:
            data_tup = get_search_values(r'text:"(.*?)",subText:(.*?),to:\{name:.*?,params:\{code:"(.*?)"', buf_str)
            if data_tup is None:
                break
            else:
                data_lis = list(data_tup)
                if len(data_lis[1]) > 1:
                    data_lis[1] = get_search_value(r'\((.*?)\)', data_lis[1])
                else:
                    data_lis[1] = get_search_value(r'config:\{\}\}\}.*"\(([0-9]*\.[0-9]*?)m\)"', data_str) + 'm'
                nearpoi_list.append(data_lis)
                buf_str = buf_str[re.search(r'\{(.*?)\}\}\}', buf_str).regs[0][1] + 1:]

        for nearPoi in nearpoi_list:
            url = 'https://www.its-mo.com/poi/' + urllib.parse.quote(nearPoi[2]) + '/'
            driver.get(url)
            nearPoi.append(get_price_set(driver))

        dic = collections.OrderedDict()
        dic["name"] = name
        label = ['remark', 'time', 'unit', 'fee']
        dic_price = collections.OrderedDict()
        for i, price in enumerate(price_set):
            dic_price[f"{i}"] = dict(zip(label, price))
        dic["price"] = dic_price
        dic_nears = collections.OrderedDict()
        for j, nearPoi in enumerate(nearpoi_list):
            dic_price_a = collections.OrderedDict()
            for k, nearPoiPrice in enumerate(nearPoi[3]):
                dic_price_a[f"{k}"] = dict(zip(label, nearPoiPrice))
            dic_nears[f"{j}"] = {"name": nearPoi[0], "distance": nearPoi[1], "price": dic_price_a}
        dic["near_parking"] = dic_nears
        return dic

    except NoSuchElementException as e:
        return {
            "error": {
                "name": name,
                "remark": 'HTMLの仕様が変わった可能性があります'
            }
        }
    except TypeError as e:
        return {
            "error": {
                "name": name,
                "remark": '検索結果がなかった可能性があります'
            }
        }
    finally:
        print('{0} END: {1}s'.format(name, time.time() - now_time))
        driver.close()


api = Flask(__name__)


@api.route('/search/<string:name>', methods=['GET'])
def param_mode(name):
    print('Entry the parameter route')
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-desktop-notifications')
    options.add_argument("--disable-extensions")
    options.add_argument('--lang=ja')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0')
    options.page_load_strategy = 'none'
    driver = webdriver.Chrome(options=options)
    return make_response(json.dumps(scraping(name, driver), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    print('Start getting parking information program')
    api.run(host='0.0.0.0', port=3000)
