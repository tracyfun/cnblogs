from pymongo import MongoClient
import pymysql
import redis


class Database(object):
    def __init__(self, host, port, user, pwd, database):
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.database = database

    def conn_mongo(self):
        db = MongoClient(self.host, self.port)[self.database]
        db.authenticate(self.user, self.pwd)
        return db

    def conn_mysql(self):
        return pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.pwd,
                               database=self.database, charset="utf8")

    def conn_redis(self):
        return redis.Redis(host=self.host, port=self.port, db=self.database)


def mongo_test():
    collection = "student"
    student = Database("localhost", 27017, "test2", "test2", "testdb2").conn_mongo()[collection]
    student.insert_one({"name": "student02", "age": 20})


def mysql_test():
    conn = Database("localhost", 3306, "root", "root", "testdb").conn_mysql()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    sql = "insert into testdb.people values (null, %s, %s)"
    name = "man4"
    age = 40

    # noinspection PyBroadException
    try:
        cursor.execute(sql, [name, age])
        conn.commit()
    except Exception as e:
        print(e)
        conn.rollback()
    cursor.close()
    conn.close()


def redis_test():
    conn = Database("localhost", 6379, "", "", 1).conn_redis()
    conn.set("key1", "haha")
    key1 = conn.get("key1")
    print(key1)


def main():
    # mongodb test
    # mongo_test()

    # mysql test
    mysql_test()

    # redis test
    # redis_test()


if __name__ == '__main__':
    main()
