import config
import rpc

def swap_in_erc20(mvs_rpc, eth_rpc, tx_hash):
    '''
    eth ERC20 token -> mvs "ERC20." prefixed asset
    '''
    eth_rpc.wait_confirm(tx_hash)

    contract_name, from_addr, (amount, max_supply, decimal) = eth_rpc.get_transaction(tx_hash)
    to_addr = eth_rpc.get_map_addr(from_addr)
    if not to_addr:
        print('Invalid bind for[%s, %s]' % (tx_hash, from_addr))
        return

    asset_name = config.ERC20_PREFIX + contract_name
    balance = mvs_rpc.get_asset_balance(asset_name)
    if balance == None: # not issued
        issue_tx_hash = mvs_rpc.issue_asset(asset_name, max_supply, decimal)
        mvs_rpc.wait_confirm(issue_tx_hash)
        balance = max_supply

    if balance < amount: # secondery issue is required
        issue2nd_tx_hash = mvs_rpc.secondery_issue_asset(asset_name, max_supply)
        mvs_rpc.wait_confirm(issue2nd_tx_hash)
        balance += max_supply

    send_tx_hash = mvs_rpc.send_asset(asset_name, to_addr, amount, 'token droplet:%s'%tx_hash)
    mvs_rpc.wait_confirm(send_tx_hash)
    return send_tx_hash

def swap_out_erc20(mvs_rpc, eth_rpc, tx_hash):
    '''
    mvs "ERC20." prefixed asset -> eth ERC20 token
    '''
    em = mvs_rpc.wait_confirm(tx_hash)
    if em:
        print('Failed to wait_confirm [%s]' % em)
        return

    asset_name, to_addr, amount = mvs_rpc.get_transaction(tx_hash)
    if not asset_name.startswith(config.ERC20_PREFIX):
        print('Invalid asset_name for[%s]' % tx_hash)
        return
    contract_name = asset_name[len(config.ERC20_PREFIX):]
    balance = eth_rpc.get_asset_balance(contract_name)
    if balance < amount:
        print("Not enough balance[%s < %s] for [%s]" % (balance, amount, tx_hash))
        return
    send_tx_hash = eth_rpc.send_asset(contract_name, to_addr)
    eth_rpc.wait_confirm(send_tx_hash)
    return send_tx_hash

def swap_in_coin(mvs_rpc, eth_rpc, tx_hash):
    pass

def swap_out_coin(mvs_rpc, eth_rpc, tx_hash):
    pass

if __name__ == '__main__':
    mvs_rpc = rpc.MVSRPC('Alice', 'A123456')
    rpc.ETHRPC.load_contracts()
    eth_rpc = rpc.ETHRPC()
    swap_in_erc20(mvs_rpc, eth_rpc, '0x9120f96b1221360d19fc298d888387dece5058d8376c62f45c60850651ca6b5a')