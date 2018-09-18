import time
import re
from mvs_rpc import mvs_api as mvs_rpc
import config

from web3 import Web3
from web3.contract import ConciseContract
web3 = Web3(Web3.HTTPProvider(config.ETHEREUM_WALLET_URL, request_kwargs={'timeout': 60}))

class RPCBase:
    SLEEP_PERIOD = 10 # second
    TX_CONFIRM_HEIGHT = 10 # 10 blocks to confirm
    @classmethod
    def get_transaction(cls, tx_hash):
        raise Exception("Not Implement")

    @classmethod
    def wait_confirm(cls, tx_hash, timeout=5*60):
        raise Exception("Not Implement")

    @classmethod
    def get_asset_balance(cls, asset_name):
        raise Exception("Not Implement")

    def issue_asset(self, asset_name, max_supply, decimal):
        raise Exception("Not Implement")

    def secondery_issue_asset(self, asset_name, max_supply):
        raise Exception("Not Implement")

    def send_asset(self, asset_name, to_addr, amount, memo=None):
        raise Exception("Not Implement")

class MVSRPC(RPCBase):
    SCAN_ADDRESS = [i['address'] for i in mvs_rpc.getdid(config.SCAN_DID)[1] if i['status'] == 'current'][0]
    COMMUNITY_ADDRESS = [i['address'] for i in mvs_rpc.getdid(config.COMMUNITY_DID)[1] if i['status'] == 'current'][0]
    def __init__(self, account, password, url=None):
        self.url = url
        self.account = account
        self.password = password

    @classmethod
    def wait_confirm(cls, tx_hash, timeout=10*60):
        timecounter, tx_height = 0, 0
        for i in range(0, timeout, cls.SLEEP_PERIOD):
            em, tx = mvs_rpc.gettx(tx_hash)
            if em != None:
                return 'failed to gettx(%s):%s' % (tx_hash, em)

            tx_height = tx.get('height', 0)
            if tx_height:
                timecounter = i
                break

            time.sleep(cls.SLEEP_PERIOD)
        else:
            #timeout
            return "wait for tx[%s] mined timeout" % tx_hash

        for i in range(timecounter, timeout, cls.SLEEP_PERIOD):
            em, latest_height = mvs_rpc.getheight()
            if em != None:
                return 'failed to getheight(%s):%s' % (tx_hash, em)

            if latest_height - tx_height > cls.TX_CONFIRM_HEIGHT:
                break

            time.sleep(cls.SLEEP_PERIOD)
        else:
            # timeout
            return "wait for tx[%s] block depth timeout" % tx_hash

        #check the tx not be forked
        em, tx = mvs_rpc.gettx(tx_hash)
        if em != None:
            return 'failed to gettx(%s):%s, forked?' % (tx_hash, em)

        assert( tx['height'] )

    @classmethod
    def parse_utxo(cls, utxo):
        address = utxo['address']
        type = utxo['attachment']['type']

        if type == 'etp':
            amount = utxo['value']
            return (address, 'etp', amount)
        elif type == "asset-transfer":
            amount = utxo['attachment']["quantity"]
            asset_name = utxo['attachment']["symbol"]
            return (address, asset_name, amount)
        elif type == "message":
            message = utxo['attachment']["content"]
            eth_address_pattern = '"(0x[0-9a-fA-F]+)"'

            m = re.search(eth_address_pattern, message)
            if not m:
                return address, "message", message
            return address, None, m.groups()[0]

            assert( False )

    @classmethod
    def get_transaction(cls, tx_hash):
        em, tx = mvs_rpc.gettx(tx_hash)
        assert( em == None )

        tx_from = []

        for input in tx['inputs']:
            prev_tx_hash = input['previous_output']['hash']
            index = input['previous_output']['index']
            em, prev_tx = mvs_rpc.gettx(prev_tx_hash)
            assert (em == None)
            utxo = prev_tx['outputs'][index]
            tx_from.append( cls.parse_utxo(utxo) )
        for address, asset_name, amount in tx_from:
            if address == cls.SCAN_ADDRESS:
                raise Exception('Scan Address cannot be one of the from address for[%s]' % tx_hash)

        tx_to = []
        for utxo in tx['outputs']:
            tx_to.append(cls.parse_utxo(utxo))

        swap ={} # asset_name -> amount
        swap_fee = {}  # asset_name -> amount
        to_address = []
        for address, asset_name, amount in tx_to:
            if address == cls.SCAN_ADDRESS:
                if asset_name:
                    swap[asset_name] = swap.get(asset_name, 0) + amount
                else:
                    to_address.append(amount)
            elif address == cls.COMMUNITY_ADDRESS:
                swap_fee[asset_name] = swap_fee.get(asset_name, 0) + amount

        if len(swap) != 1:
            raise Exception('Unexpect swap assert count for[%s]' % tx_hash)
        asset_name = list(swap.keys())[0]
        asset_amount = swap[asset_name]

        if len(swap_fee) != 1 or 'etp' not in swap_fee:
            raise Exception('Unexpect swap fee for[%s]' % tx_hash)

        if len(to_address) != 1:
            raise Exception('Unexpect to_address for[%s]' % tx_hash)
        return  asset_name, to_address[0], asset_amount, swap_fee['etp']

    @classmethod
    def get_asset_balance(cls, asset_name):
        em, result = mvs_rpc.getasset(asset_name)
        assert (em == None)
        if not result:
            return None
        #decimal_number = result[0]['decimal_number']
        em, result = mvs_rpc.getaddressasset(cls.SCAN_ADDRESS, symbol=asset_name)
        assert (em == None)
        quantity = 0
        for i in result:
            if i["status"] == 'unspent':
                quantity += i["quantity"]
        return quantity

    def issue_asset(self, asset_name, max_supply, decimal):
        em, result = mvs_rpc.createasset(self.account, self.password, asset_name, config.SCAN_DID, max_supply, rate=-1, decimalnumber=decimal, description="Crosschain asset of ERC20 token %s" % asset_name[len(config.ERC20_PREFIX):])
        if em != None:
            raise Exception('Failed to create asset[%s] for: %s' % (asset_name, em))
        em, result = mvs_rpc.issue(self.account, self.password, asset_name)
        if em != None:
            mvs_rpc.deletelocalasset(self.account, self.password, asset_name)
            raise Exception('Failed to issue asset[%s] for: %s' % (asset_name, em))
        return result['hash']

    def secondery_issue_asset(self, asset_name, max_supply):
        em, result = mvs_rpc.secondaryissue(self.account, self.password, config.SCAN_DID, asset_name, max_supply)
        if em != None:
            raise Exception('Failed to secondary issue asset[%s] for: %s' % (asset_name, em))
        return result['hash']

    def send_asset(self, asset_name, to_addr, amount, memo=None):
        em, result = mvs_rpc.sendasset(self.account, self.password, to_addr, asset_name, amount, memo=memo)
        if em != None:
            raise Exception('Failed to secondary issue asset[%s] for: %s' % (asset_name, em))
        return result['hash']

class ETHRPC(RPCBase):
    etpmap_contract = None
    erc20_contracts = {} # address : contract_obj
    def __init__(self):
        pass

    @classmethod
    def load_contracts(cls):
        cls.etpmap_contract = web3.eth.contract(address=config.CONTRACT_ETPMAP['address'],
                                            abi=config.CONTRACT_ETPMAP['abi'],
                                            ContractFactoryClass=ConciseContract)

        for contract_address in config.CONTRACT_ERC20_LST:
            contract = web3.eth.contract(address=contract_address,
                                            abi=config.CONTRACT_ERC20_LST[contract_address]['abi'],
                                            ContractFactoryClass=ConciseContract)
            cls.erc20_contracts[contract_address] = contract
            cls.erc20_contracts[contract.symbol()] = contract

    @classmethod
    def get_map_addr(cls, eth_address):
        return cls.etpmap_contract.get_address(eth_address)

    @classmethod
    def wait_confirm(cls, tx_hash, timeout=10 * 60):
        t0 = time.time()
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash, timeout=timeout)
        t1 = time.time()
        timeout -= int(t1 - t0)
        tx_height = tx_receipt['blockNumber']

        for i in range(0, timeout, cls.SLEEP_PERIOD):
            latest_height = web3.eth.blockNumber

            if latest_height - tx_height > cls.TX_CONFIRM_HEIGHT:
                break

            time.sleep(cls.SLEEP_PERIOD)
        else:
            # timeout
            return "wait for tx[%s] block depth timeout" % tx_hash
        #avoid the chain fored during the previous for circle
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        assert (tx_receipt['blockNumber'])

    @classmethod
    def Wei2Satoshi(cls, value, decimals):
        if decimals > 8:
            delta = decimals - 8
            return int(value / (10 ** delta)), 8
        return value, decimals

    @classmethod
    def Satoshi2Wei(cls, value, decimals):
        if decimals > 8:
            delta = decimals - 8
            return int(value * (10 ** delta)), 8
        return value, decimals

    @classmethod
    def get_transaction(cls, tx_hash):
        tx = web3.eth.getTransaction(tx_hash)

        contract = cls.erc20_contracts.get(tx.to, None)
        if contract == None:
            raise Exception('Not supported contract address for swap:%s' % tx.to)

        contract_instance = web3.eth.contract(address=tx.to,
                                        abi=config.CONTRACT_ERC20_LST[tx.to]['abi'])
        func, paras = contract_instance.decode_function_input(tx.input)

        if str(func) != '<Function transfer(address,uint256)>':
            raise Exception('Unexpect contract method for %s' % tx_hash)

        if paras['_to'].lower() != config.ETHEREUM_SCAN_ADDRESS.lower():
            raise Exception('Unexpect reveive address for %s' % tx_hash)

        amount, decimals = cls.Wei2Satoshi(paras['_value'], contract.decimals())
        totalSupply, _ = cls.Wei2Satoshi(contract.totalSupply(), contract.decimals())
        if totalSupply > 0xFFFFFFFFFFFFFFFF:
            totalSupply = 0xFFFFFFFFFFFFFFFF

        return contract.symbol(), tx['from'], (amount, totalSupply, decimals)

    @classmethod
    def get_asset_balance(cls, contract_name):
        contract = cls.erc20_contracts.get(contract_name, None)
        if contract == None:
            raise Exception('Not supported contract name for swap:%s' % contract_name)
        return cls.Wei2Satoshi( contract.balanceOf(config.ETHEREUM_SCAN_ADDRESS), contract.decimals())[0]

    def send_asset(self, contract_name, to_addr, amount, memo=None):
        contract = self.erc20_contracts.get(contract_name, None)
        if contract == None:
            raise Exception('Not supported contract name for swap:%s' % contract_name)

        return contract.transfer(to_addr, self.Satoshi2Wei(amount, contract.decimals())[0])