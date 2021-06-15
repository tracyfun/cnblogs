import math

import pymysql
from lxml import etree
import requests
import time
import re
import xlwt


class Database(object):
    def __init__(self, host, port, user, pwd, database):
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.database = database

    def conn_mysql(self):
        return pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.pwd,
                               database=self.database, charset="utf8")


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/90.0.4430.212 Safari/537.36 '
}


def get_article_list(url):
    response = requests.get(url, headers=HEADERS)
    html = etree.HTML(response.text)
    article_list = html.xpath('//div[@class="day"]//a[@class="postTitle2 vertical-middle"]/@href')
    return article_list


def get_article_detail(article_url, author_name):
    category_str = ''
    tags_str = ''
    article_detail = []
    response = requests.get(article_url, headers=HEADERS)
    html = etree.HTML(response.text)
    article_title = html.xpath('//h1[@class="postTitle"]//a[@class="postTitle2 vertical-middle"]//span//text()')[0]
    # print("article_title: " + str(article_title))

    article_view_count = html.xpath('//span[@id="post_view_count"]//text()')[0]
    # print("article_view_count: ", str(article_view_count))

    article_comment_count = html.xpath('//span[@id="post_comment_count"]//text()')[0]
    # print("article_comment_count: ", str(article_comment_count))

    # get info from js
    script_content = str(html.xpath('//head//script[1]//text()'))
    # print("script_content: ", str(script_content))
    blog_id = re.findall(r'currentBlogId = (.+?);', script_content)[0]
    post_id = article_url.split("/")[-1].split(".")[0]

    timestamp = int(round(time.time() * 1000))
    category_url = "https://www.cnblogs.com/" + author_name + \
                   "/ajax/CategoriesTags.aspx?blogId=" + blog_id + \
                   "&postId=" + post_id + "&_=" + str(timestamp)
    # print("category_url:", category_url)
    category_resp = requests.get(category_url, headers=HEADERS)
    category_html = etree.HTML(category_resp.text)
    if category_html is not None:
        category = category_html.xpath('//div[@id="BlogPostCategory"]//a//text()')
        # print("category: ", str(category))
        if category is not None:
            for i in range(len(category)):
                if i == len(category) - 1:
                    category_str += category[i]
                else:
                    category_str += category[i] + '; '
        tags = category_html.xpath('//div[@id="EntryTag"]//a//text()')
        # print("tags: ", str(tags))
        if tags is not None:
            for i in range(len(tags)):
                if i == len(tags) - 1:
                    tags_str += tags[i]
                else:
                    tags_str += tags[i] + '; '

    article_detail.append(int(post_id))
    article_detail.append(article_title)
    article_detail.append(article_url)
    article_detail.append(int(article_view_count))
    article_detail.append(int(article_comment_count))
    article_detail.append(category_str)
    article_detail.append(tags_str)

    return article_detail


def mysql_create_table(table_name):
    conn_to_mysql = Database("localhost", 3306, "root", "root", "testdb").conn_mysql()
    cursor = conn_to_mysql.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute('drop table if exists %s' % table_name)
    sql = 'create table %s (' \
          'id int auto_increment primary key comment "id",' \
          'article_id int comment "文章Id",' \
          'article_title varchar (255) not null comment "文章标题",' \
          'article_url varchar (255) not null comment "文章链接",' \
          'article_view_count int comment "浏览次数",' \
          'article_comment_count int comment "评论数",' \
          'category varchar (255) comment "类别",' \
          'tags varchar (255) comment "标签")' % table_name
    cursor.execute(sql)


def save_to_mysql(article_detail, table_name):
    conn_to_mysql = Database("localhost", 3306, "root", "root", "testdb").conn_mysql()
    cursor = conn_to_mysql.cursor(cursor=pymysql.cursors.DictCursor)
    sql = 'insert into %s' % table_name + ' values (null, %s, %s, %s, %s, %s ,%s, %s)'
    cursor.execute(sql, (
        article_detail[0], article_detail[1], article_detail[2], article_detail[3],
        article_detail[4], article_detail[5], article_detail[6]
    ))
    conn_to_mysql.commit()


def save_to_excel(worksheet, article_detail, index):
    for i in range(len(article_detail)):
        worksheet.write(index, i, article_detail[i])


def get_pages(author_name, base_url):
    # 获取文章总条数
    blog_status_url = 'https://www.cnblogs.com/' + author_name + '/ajax/blogStats'
    response = requests.get(blog_status_url, headers=HEADERS)
    html = etree.HTML(response.text)
    status_post = str(html.xpath('//span[@id="stats_post_count"]//text()')[0])
    # print('status_post:', status_post)
    replace = status_post.replace(' ', '')
    status_post_count = int(replace.split('-')[-1])
    # print('status_post_count:', status_post_count)

    # 获取首页文章总条数
    first_page_url = base_url.format(1)
    article_list = get_article_list(first_page_url)
    first_page_count = len(article_list)

    # 获取首页置顶文章条数
    response = requests.get(first_page_url)
    html = etree.HTML(response.text)
    top_list = html.xpath('//a[@class="postTitle2 vertical-middle"]/span/span/text()')
    top_count = len(top_list)
    # print("top_count:", top_count)

    # 减去置顶文章即每页文章条数
    each_page_article_count = first_page_count - top_count
    # print("each_page_article_count:", each_page_article_count)
    # 获取文章页数
    pages = math.ceil(status_post_count / each_page_article_count)
    # print("pages:", pages)
    return pages


def spider_cnblogs():
    # conn_to_mysql = Database("localhost", 3306, "root", "root", "testdb").conn_mysql()
    # cursor = conn_to_mysql.cursor(cursor=pymysql.cursors.DictCursor)

    table_name = input('请输入导出的excel | sql表名：')
    if table_name is None:
        table_name = str(time.time())

    author_name = None
    while author_name is None:
        author_name = input('请输入文章作者【可以通过查看作者首页地址栏得到】：')

    end_page = input('请输入文章结束页【默认10页】：')
    if end_page is None or end_page == '':
        end_page = '10'
    else:
        if int(end_page) <= 0:
            end_page = '10'

    base_url = 'https://www.cnblogs.com/' + author_name + '/default.html?page={}'
    # mysql_create_table(table_name)

    workbook = xlwt.Workbook(encoding='utf-8')
    worksheet = workbook.add_sheet("sheet1")
    fields = ['文章Id', '文章标题', '文章链接', '浏览次数', '评论数', '类别', '标签']
    for i in range(len(fields)):
        worksheet.write(0, i, fields[i])

    # 获取总页数
    pages = get_pages(author_name, base_url)

    if int(end_page) > pages:
        end_page = pages

    sum_len = 0
    for index in range(1, int(end_page) + 1):
        print("start spider of page {}".format(index))
        url = base_url.format(index)
        article_list = get_article_list(url)
        sum_len += len(article_list)
        # print('sum_len:', sum_len)
        for key, article_url in enumerate(article_list):
            # print('index: ' + str(key) + '\narticle_url: ' + article_url)
            print("article_url:", article_url)
            article_detail = get_article_detail(article_url, author_name)
            # print("article_detail:", article_detail)
            # 保存到数据库
            # save_to_mysql(article_detail, table_name)

            # 控制数据写入excel表格位置
            if index > 1:
                key = sum_len - len(article_list) + key
                # print('key:', key)
            save_to_excel(worksheet, article_detail, key + 1)

    print("save success")
    # cursor.close()
    # conn_to_mysql.close()
    workbook.save(table_name + '.xls')


def main():
    # spider test
    # start_time = int(time.time())
    spider_cnblogs()
    # end_time = int(time.time())
    # time_consume = end_time - start_time
    # print("total time: " + str(time_consume) + "s")


if __name__ == '__main__':
    main()
