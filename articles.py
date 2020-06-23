from datetime import datetime
from bs4 import BeautifulSoup
from flask import request

import requests
import html
# import json
import mysql.connector
from constance import *

BASE_URL = "https://vnexpress.net"
PATH = "/tin-nong"


def crawNewsData(baseUrl, url):
    deleleOutdateArticles()
    response = requests.get(url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    titles = soup.findAll('h3', class_='title-news')
    links = [link.find('a').attrs["href"] for link in titles]
    data = []

    for link in links:
        # check video
        if link.find("video") != -1:
            continue

        news = requests.get(link)
        if news.status_code != 200:
            continue

        soup = BeautifulSoup(news.content, "html.parser")
        soup = html.unescape(soup)

        # get title
        try:
            title = soup.find(
                "h1", class_="title-detail").text.replace("'", '')
        except:
            continue
        # get category
        try:
            category = soup.find("ul", class_="breadcrumb")
            category = category.find("a").text
        except:
            category = ""
        # get time
        try:
            time = soup.find("span", class_="date").text
            time = time[0:-8]
        except:
            continue
        # get location
        try:
            location = soup.find("span", class_="location-stamp").text
        except:
            location = ""
        # get description
        try:
            description = soup.find("p", class_="description")
            if location != "":
                description.find(
                    "span", class_="location-stamp").decompose()
                description.find("p", class_="description")

        except:
            continue
        # get listContent
        try:
            contents = soup.find("article", class_="fck_detail").findAll()

            check_video = ""
            check_video = soup.findAll("div", class_="box_embed_video")
            if check_video != []:
                continue

            check_live = ""
            check_live = soup.findAll("article", id="content-live")
            if check_live != []:
                continue

            check_player = ""
            check_player = soup.findAll("div", {"data-oembed-url": True})
            if check_player != []:
                continue

            check_lightgallery = soup.findAll("article", id="lightgallery")
            if check_lightgallery != []:
                continue

            check_lightgallery2 = soup.findAll("div", class_="width-detail-photo")
            if check_lightgallery2 != []:
                continue

            listContent = []

            for obj in contents:
                obj_info = ""
                obj_type = ""
                try:
                    nameclass = ""
                    if obj.name == "p":
                        nameclass = ' '.join(map(str, obj['class']))
                        if nameclass == "Image":
                            obj_info = obj.text
                            obj_type = "img_des"
                        else:
                            obj_info = obj.text
                            obj_type = "text"

                    if obj.name == "img":
                        obj_info = obj.attrs["data-src"]
                        obj_type = "image"
                    if obj_info != "" and obj_type != "":
                        listContent.append({
                            "info": obj_info,
                            "type": obj_type
                        })
                except:
                    continue
            # get author
            author = ""
            if len(listContent[-1]["info"]) <= 40:
                author = listContent[-1]["info"].replace(
                    "* Tiếp tục cập nhật.", '')
                listContent = listContent[0:-1]
        except:
            listContent = ""
            author = ""
        data.append({
            "link": link,
            "category": category,
            "title": title,
            "time": time,
            "location": location,
            "description": description.text,
            "content": listContent,
            "author": author,
        })
    return data


def saveArticles():
    data = crawNewsData(BASE_URL, BASE_URL + PATH)
    if data == []:
        return 1
    number_saved = 0
    # save json
    # listToJson("one_day ", data)

    # Open database connection
    db = mysql.connector.connect(user=constance.USERNAME, password=constance.PASSWORD,
                                 host=constance.HOST,
                                 database=constance.DATABASE)
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    # save db
    for index, item in enumerate(data[::-1]):
        check = 0
        _link = item["link"]
        time = item["time"]
        category = item["category"]
        title = item["title"]
        location = item["location"]
        description = item["description"]
        author = item["author"]
        content = item["content"]
        query = "INSERT INTO articles(link, time, category, title, location, description, author, created_at) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', {})".format(
            _link, time, category, title, location, description, author, 'NOW()')
        try:
            cursor.execute(query)
            # Commit your changes in the database
            db.commit()
            number_saved = number_saved + 1
            check = 1
        except:
            check = 0
            query = "ALTER TABLE articles AUTO_INCREMENT = {}".format(
                getLastId())
            cursor.execute(query)
            db.commit()
            db.rollback()
        if check == 1:
            query = "SELECT MAX(id) FROM articles"
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                articles_id = result[0]
                # print(articles_id)
            except:
                db.rollback()
                # on error set the articles_id to -1
                articles_id = -1
            # save content
            for index2, item2 in enumerate(content):
                info = item2["info"]
                type = item2["type"]
                query = "INSERT INTO contents(articles_id, info, type, created_at) VALUES ('{}', '{}', '{}', {})".format(
                    articles_id, info, type, 'NOW()')
                # print(query)
                try:
                    cursor.execute(query)
                    db.commit()
                except:
                    db.rollback()
            content = []

    db.close()
    # saveAllToJson()
    print("Number news save to db: ", number_saved)


# delete after "number" of days


def deleleOutdateArticles():
    db = mysql.connector.connect(user=constance.USERNAME, password=constance.PASSWORD,
                                 host=constance.HOST,
                                 database=constance.DATABASE)

    cursor = db.cursor()
    sqlquery = "delete FROM articles where DATE_SUB(now(), INTERVAL {} DAY) > created_at".format(
        constance.DELETE_AFTER)
    try:
        cursor.execute(sqlquery)
        db.commit()
    except:
        db.rollback()
    db.close()


# get articles from end_id back to end_id - NEWS_PER_LOAD


def getNewsFromId(end):
    db = mysql.connector.connect(user=constance.USERNAME, password=constance.PASSWORD,
                                 host=constance.HOST,
                                 database=constance.DATABASE)
    cursor = db.cursor()
    query = "SELECT * FROM articles where {}<=id && id<={}".format(
        end - constance.ARTICLES_PER_LOAD, end)
    dataNews = []
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        for row in records:
            dataNews.append({
                "id": row[0],
                "link": row[1],
                "time": row[2],
                "category": row[3],
                "title": row[4],
                "location": row[5],
                "description": row[6],
                "content": getContentsById(row[0]),
                "author": row[7],
            })
        db.commit()
    except:
        db.rollback()
    db.close()
    return dataNews


def getContentsById(articles_id):
    db = mysql.connector.connect(user=constance.USERNAME, password=constance.PASSWORD,
                                 host=constance.HOST,
                                 database=constance.DATABASE)

    cursor = db.cursor()
    query = "SELECT * FROM contents where articles_id={}".format(
        articles_id)
    dataContents = []
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        for row in records:
            dataContents.append({
                "id": row[0],
                "articles_id": row[1],
                "info": row[2],
                "type": row[3],
            })
        db.commit()
    except:
        db.rollback()
    db.close()
    return dataContents


# def listToJson(str, data):
#     now = datetime.now()
#     dt_string = now.strftime("%d%m%Y %H%M%S")
#     path = "{}{}.json".format(str, dt_string)
#     with open(path, 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=4)

def getLastId():
    db = mysql.connector.connect(user=constance.USERNAME, password=constance.PASSWORD,
                                 host=constance.HOST,
                                 database=constance.DATABASE)
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    query = "SELECT MAX(id) FROM articles"
    result = -1
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        for index in records:
            result = index[0]
            break
        db.commit()
    except:
        db.rollback()
    db.close()
    return 0 if result is None else result

# def saveAllToJson():
#     all_data = getNewsFromId(1, getLastId())
#     listToJson("All database ", all_data)


# if __name__ == "__main__":
# for index in range(1,200):
#     link="https://vnexpress.net/thoi-su-p{}".format(index)
#     saveNews(crawNewsData("https://vnexpress.net",link))
#     saveArticles()
# deleleOutdateArticles(0)
# b=getLastId()
# aaa=getNewsById(90-15,90)
# print(aaa)