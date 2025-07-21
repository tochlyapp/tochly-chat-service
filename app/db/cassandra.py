import time
from cassandra.cluster import Cluster
from cassandra.cluster import NoHostAvailable

_session = None

def get_cassandra_session(max_retries=10, delay=5):
    global _session
    if _session is not None:
        return _session

    for attempt in range(1, max_retries + 1):
        try:
            cluster = Cluster(['cassandra'])  # Optionally use env var
            session = cluster.connect()
            session.set_keyspace('tochly')
            _session = session
            print("[Cassandra] Connected successfully.")
            return _session
        except NoHostAvailable as e:
            print(f"[Cassandra Retry {attempt}] No host available: {e}")
        except Exception as e:
            print(f"[Cassandra Retry {attempt}] Unexpected error: {e}")
        time.sleep(delay)

    raise Exception("Cassandra not reachable after multiple retries")
