from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from mage_integrations.connections.base import Connection


class Couchbase(Connection):
    def __init__(
        self,
        bucket: str,
        scope: str,
        connection_string: str,
        password: str,
        username: str,
    ):
        super().__init__()
        self.bucket = bucket
        self.scope = scope
        self.connection_string = connection_string
        self.password = password
        self.username = username

    def get_bucket(self):
        auth = PasswordAuthenticator(self.username, self.password)
        cluster = Cluster(self.connection_string, ClusterOptions(auth))
        return cluster.bucket(self.bucket)

    def get_scope(self):
        return self.get_bucket().scope(self.scope)

    def get_all_collections(self):
        collection_manager = self.get_bucket().collections()

        scopes = collection_manager.get_all_scopes()
        for scope in scopes:
            if scope.name == self.scope:
                return [c.name for c in scope.collections]

        raise ValueError(f'Couchbase scope {self.scope!r} does not exist in the selected bucket.')

    def load(self, query):
        return list(self.get_scope().query(query).rows())
