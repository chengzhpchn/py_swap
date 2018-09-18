from unittest import TestCase
import rpc
import time

class testMVS:#(TestCase):
    def setUp(self):
        self.rpc = rpc.MVSRPC("test", "123456")

    def tearDown(self):
        pass

    def test_0_wait_confirm(self):
        em, height = rpc.mvs_rpc.getheight()
        self.assertEqual(em, None)

        em, result = rpc.mvs_rpc.getblock(height - rpc.MVSRPC.TX_CONFIRM_HEIGHT -1)
        self.assertEqual(em, None)
        tx_hash = result['transactions'][-1]['hash']
        t0 = time.time()
        em = rpc.MVSRPC.wait_confirm(tx_hash)
        t1 = time.time()
        self.assertEqual(em, None)
        self.assertLess(t1-t0, 1, "wait_confirm cost less than 1s")

        em, height = rpc.mvs_rpc.getheight()
        self.assertEqual(em, None)

        em, result = rpc.mvs_rpc.getblock(height - int(rpc.MVSRPC.TX_CONFIRM_HEIGHT/2))
        self.assertEqual(em, None)
        tx_hash = result['transactions'][-1]['hash']
        t0 = time.time()
        em = rpc.MVSRPC.wait_confirm(tx_hash)
        t1 = time.time()
        self.assertEqual(em, None)
        self.assertLess(t1 - t0, 35*(int(rpc.MVSRPC.TX_CONFIRM_HEIGHT/2)+1), "wait_confirm cost less than 6 block")
        self.assertLess(35 * (int(rpc.MVSRPC.TX_CONFIRM_HEIGHT / 2) - 2), t1 - t0,
                        "wait_confirm more less than 3 block")

    def test_1_get_transaction(self):
        self.assertEqual(('ERC20.EDU', '0x8bB10939a8a36765a082905d4BfE8680F86eBF95', 12100000, 100000000), rpc.MVSRPC.get_transaction("c0a12f546f07c5f0826e37d061f56479046e99a09eb9b09394b4d51392e3b47c"))

    def test_2_issue_asset(self):
        self.rpc.issue_asset('ERC20.EDU', 100, 8)

class testETH(TestCase):
    def setUp(self):
        rpc.ETHRPC.load_contracts()

    def tearDown(self):
        pass

    def test_0_get_map_addr(self):
        self.assertEqual('CZP', rpc.ETHRPC.get_map_addr('0x2D23fDFfE79c9b5769B399cCd0d8C2E46E1aEA26') )
        # not bind
        self.assertEqual('', rpc.ETHRPC.get_map_addr('0x8bB10939a8a36765a082905d4BfE8680F86eBF95'))

    def test_1_wait_confirm(self):
        ret = rpc.ETHRPC.wait_confirm('0x29fb4a7cf9df1d91a28242ffb9a91f002595dc087e0ff0979088d3cb79b6710d')
        print(ret)

    def test_2_get_transaction(self):
        ret = rpc.ETHRPC.get_transaction('0x9120f96b1221360d19fc298d888387dece5058d8376c62f45c60850651ca6b5a')
        print(ret)

    def test_3_get_asset_balance(self):
        ret = rpc.ETHRPC.get_asset_balance('EDU')
        print(ret)

    def test_4_send_asset(self):
        ret = rpc.ETHRPC().send_asset('EDU', '0xe10B56Ce1Ef3060b278A2Bd6A92780a01A4Cc7C9', 1234, None)
        print(ret)