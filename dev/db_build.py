import os
import psycopg2
import json
from tqdm import tqdm
from dev.omdb_scraper import get_omdb_data

class TVShowDatabase():

    def __init__(self):

        # DATABASE_URL = os.environ['DATABASE_URL']
        # self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.conn = psycopg2.connect(dbname='imdb_data')
        self.c = self.conn.cursor()

        self.TABLES = [
            {
                'name':         "shows",
                'source_data':  "./imdbscraper/imdbscraper/data/showdata.json",
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
                'source_data':  "./imdbscraper/imdbscraper/data/episodedata.json",
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


    def init_tables(self, replace=False):
        for table in self.TABLES:
            if replace == True:
                self.c.execute("DROP TABLE IF EXISTS " + table['name'])
                self.c.execute(table['ddl'])

            else:
                self.c.execute("""DELETE FROM """ + table['name'])

            table['load_func'](table['source_data'])


    def load_shows_tbl(self, fp):
        shows = json.load(open(fp))
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
        episodes = json.load(open(fp))
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