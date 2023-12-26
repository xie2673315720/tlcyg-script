# 获取畅易阁指定区服的公示区账号信息，并保存的sqlite的表中
# 作者 xhl

import json
import sqlite3
import time
from datetime import datetime

import bs4
import requests
from DrissionPage import SessionPage


# 连接sqlite
def get_sqlite_conn():
    conn = sqlite3.connect("tl.db")
    cursor = conn.cursor()
    return conn, cursor


# 初始化数据库，创建表格
def sqlite_create_table():
    table_name = "tl_public_account_" + datetime.now().strftime("%m_%d__%H_%M")
    create_table_sql = "create table if not exists {}(商品id int, 关注数 int, 门派 varchar(15), 剩余时间 varchar(15), 装备评分 int,宝石评分 int, 价格 int, 详情链接 varchar(100))".format(
        table_name)
    print(create_table_sql)
    cursor.execute(create_table_sql)
    conn.commit()
    print("Table {} created".format(table_name))
    return table_name


# 获取账号列表
# 先通过request获取一页的账号列表，再遍历每一页的账号列表，使用DrissionPage三方库来获取每个账号的详情页提取关注的信息
def get_account(pg_num):
    url = ("http://tl.cyg.changyou.com/goods/public?world_id=3145&order_by=equip_point-desc&world_name=%25E7%258B%2582"
           "%25E6%2588%2598%25E5%25A4%25A9%25E4%25B8%258B&area_name=%25E5%2594%25AF%25E7%25BE%258E%25E7%2594%25B5"
           "%25E4%25BF%25A1&page_num={}#goodsTag".format(pg_num))
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/118.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    goods_ul = soup.find('ul', {'pg-goods-list'})
    dl = goods_ul.find_all('li')
    for account in dl:
        detail_url = account.find('dt', {'title'}).find('a').get('href')
        mp = account.find('span', {'name'}).text
        eq_score = account.find('span', {'di'}).find('b').text
        left_time = account.find('p', {'time'}).text
        goods_id = detail_url.split("=")[1]
        page = SessionPage()
        page.get(detail_url)
        goods_id_hided = page.ele('#loginToCollect').attr("data-goods-id")
        favor = get_favor(goods_id_hided)
        bs_score = page.ele("text:宝石修炼评分").ele('.span').inner_html
        price = int(account.find('div', {'item-opr'}).find('p', {'price'}).text[1:])
        print(goods_id, mp, eq_score, bs_score, left_time, favor, detail_url, price)
        insert_sql = f"INSERT INTO {tb_name}(商品id, 关注数, 门派, 剩余时间, 装备评分,宝石评分, 价格, 详情链接) VALUES (?,?,?,?,?,?,?,?)"
        print(insert_sql)
        cursor.execute(insert_sql, (goods_id, favor, mp, left_time, eq_score, bs_score, price, detail_url))
        conn.commit()
        time.sleep(5)

# 由于关注数是调用的js获取的，所以需要额外去查询
def get_favor(goods_id_hided):
    goods_id = goods_id_hided
    now_timestamp = int(datetime.now().timestamp() * 1000)
    url_check_favor = f"http://tl.cyg.changyou.com/goods/checkisfavor?goods_id={goods_id}&t={now_timestamp}"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"}
    resp = requests.get(url_check_favor, headers=headers)
    # 返回的数据为字符串，且不符合json格式，不能直接进行json(),取text替换串和空格后取值
    resp_text = resp.text.replace("'", "\"")
    resp_text = resp_text.replace(" ", "")
    resp_json = json.loads(resp_text)
    favor = resp_json.get("count")
    return favor


if __name__ == '__main__':
    # 连接数据库，获取操作数据库对象
    conn, cursor = get_sqlite_conn()
    # 创建数据表，并得到表名
    tb_name = sqlite_create_table()
    # 循环导出每一页数据
    page_num = 1
    while True:
        get_account(page_num)
        print(f"导出第{page_num}页完成")
        page_num = page_num + 1
