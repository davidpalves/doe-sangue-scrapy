import pymongo

from scrapy.conf import settings
from scrapy.exceptions import DropItem
from scrapy import log
from datetime import datetime
import psycopg2


class NivelSangueHematoPipeline(object):
    def process_item(self, item, spider):
        if item['banco'] == "HEMATO":
            if float(item['nivel_sangue']) > 0.6:
                item['nivel_sangue'] = 'estavel'
            elif float(item['nivel_sangue']) >= 0.4:
                item['nivel_sangue'] = 'alerta'
            else:
                item['nivel_sangue'] = 'critico'

        return item


class MongoDBPipeline(object):
    def __init__(self):
        connection = pymongo.MongoClient(
            settings['MONGODB_SERVER'],
            settings['MONGODB_PORT']
        )
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_COLLECTION']]

    def process_item(self, item, spider):
        valid = True
        for data in item:
            if not data:
                valid = False
                raise DropItem("Faltando {0}!".format(data))
        if valid:
            self.collection.insert(dict(item))
            log.msg("Produto adicionado ao banco de dados.",
                    level=log.DEBUG, spider=spider)
        return item


class PostgreSQLPipeline(object):
    def __init__(self):
        self.connection = psycopg2.connect(
            host=settings['POSTGRES_HOST'],
            database=settings['POSTGRES_DB'],
            user=settings['POSTGRES_USER'],
            password=settings['POSTGRES_PASSWORD'])
        self.cursor = self.connection.cursor()

    def process_item(self, item, spider):
        self.cursor.execute("INSERT INTO nivel_sangue\
         (banco, tipo_sangue, nivel_sangue, url, scrapedAt) \
         VALUES (%s, %s, %s, %s, %s);", [
                item['banco'],
                item['tipo_sangue'],
                item['nivel_sangue'],
                item['url'],
                str(datetime.now())])

        self.connection.commit()

        return item
