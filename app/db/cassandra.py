import time
from cassandra.cluster import Cluster



def get_cassandra_session():
    for _ in range(10):
        try:
            cluster = Cluster(['cassandra'])
            return cluster.connect()
        except Exception as e:
            print("Cassandra not ready yet:", e)
            time.sleep(5)
        raise RuntimeError("Cassandra failed after multiple retries")

# def get_cassandra_session():
#     cluster = Cluster(['cassandra'])
#     session = cluster.connect()
#     session.set_keyspace('tochly')
#     return session

# Global session instance
session = get_cassandra_session()
