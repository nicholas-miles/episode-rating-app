import os
import psycopg2
import boto3
import json
from tqdm import tqdm
from dev.omdb_scraper import get_omdb_data

class TVShowDatabase():

    def __init__(self):
        is_prod = os.environ.get('IS_HEROKU', None)
        pg_pwd = os.environ.get('pgpwd', None)
        if is_prod:
            DATABASE_URL = os.environ.get('DATABASE_URL')
            self.conn = psycopg2.connect(DATABASE_URL, sslmode='require', user='postgres', password=pg_pwd)
        
        else:
            self.conn = psycopg2.connect(dbname='imdb_data', user='postgres', password=pg_pwd)
        self.c = self.conn.cursor()

        self.TABLES = [
            {
                'name':         "shows",
                'source_data':  "showdata.json",
                'ddl':          '''
                                    CREATE TABLE IF NOT EXISTS shows 
                                    (
                                        imdb_id text,
                                        title text,
                                        genre text,
                                        poster text,
                                        show_rating real
                                    )  
                                ''',
                'load_func':    self.load_shows_tbl
            },
            {
                'name':         "episodes",
                'source_data':  "episodedata.json",
                'ddl':          '''
                                    CREATE TABLE IF NOT EXISTS episodes
                                    (
                                        imdb_id text,
                                        season integer,
                                        ep_num integer,
                                        ep_name text,
                                        ep_page text,
                                        ep_rating real
                                    )
                                ''',
                'load_func':    self.load_episodes_tbl
            }
        ]


    def init_tables(self, replace=True):
        for table in self.TABLES:
            if replace == True:
                self.c.execute("DROP TABLE IF EXISTS " + table['name'])
                self.c.execute(table['ddl'])

            else:
                self.c.execute("""DELETE FROM """ + table['name'])

            table['load_func'](table['source_data'])


    def get_s3_data(self, filename):
        client = boto3.client('s3')
        obj = client.get_object(Bucket='imdb-episode-data', Key=filename)

        return obj['Body']


    def load_shows_tbl(self, fp):
        shows = json.load(self.get_s3_data(fp))
        for i in tqdm(shows):
            sql = """ INSERT INTO shows VALUES(%s, %s, %s, %s, %s) """
            imdb_id = i['imdb_id']
            omdb_data = get_omdb_data(imdb_id)
            
            if omdb_data and omdb_data['Response'] == 'True':
                if omdb_data['imdbRating'] == 'N/A':
                    omdb_data['imdbRating'] = None
                omdb_data = (
                                imdb_id, 
                                omdb_data['Title'],
                                omdb_data['Genre'],
                                omdb_data['Poster'],
                                omdb_data['imdbRating']
                            )

                self.c.execute(sql, omdb_data)

            self.conn.commit()

        self.c.execute("""SELECT COUNT(*) FROM shows""")
        print("loaded {} rows into SHOWS".format(self.c.fetchone()[0]))


    def load_episodes_tbl(self, fp):
        episodes = json.load(self.get_s3_data(fp))
        sql = """INSERT INTO episodes VALUES (%s,%s,%s,%s,%s,%s)"""
        for i in tqdm(episodes):
            ep_data = (
                            i['imdb_id'],
                            i['season'],
                            i['ep_num'],
                            i['ep_name'],
                            i['ep_page'],
                            i['ep_rating']
                      )
            self.c.execute(sql, ep_data)

        self.conn.commit()

        self.c.execute("""SELECT COUNT(*) FROM episodes""")
        print("loaded {} rows into EPISODES".format(self.c.fetchone()[0]))

    


if __name__ == "__main__":
    db = TVShowDatabase()
    db.init_tables()
    print(db.c)
    raise SystemExit