

class RPCBase:
    @classmethod
    def get_transaction(cls, tx_hash):
        raise Exception("Not Implement")

    @classmethod
    def wait_confirm(cls, tx_hash, timeout=5*60):
        raise Exception("Not Implement")

    def get_asset_balance(self, asset_name):
        raise Exception("Not Implement")

    def issue_asset(self, asset_name, max_supply):
        raise Exception("Not Implement")

    def secondery_issue_asset(self, asset_name, max_supply):
        raise Exception("Not Implement")

    def send_asset(self, asset_name, to_addr):
        raise Exception("Not Implement")

class MVSRPC(RPCBase):
    def __init__(self, url, account, password):
        self.url = url
        self.account = account
        self.password = password

class ETHRPC(RPCBase):
    def get_bind_addr(self):
        pass
