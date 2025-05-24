from cassandra.cluster import Cluster

def get_cassandra_session():
    cluster = Cluster(['cassandra'])
    session = cluster.connect()
    session.set_keyspace('tochly')
    return session

# Global session instance
session = get_cassandra_session()
