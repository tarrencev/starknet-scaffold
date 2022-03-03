# Taken from: https://github.com/zorro-project/zorro/blob/b830ee105c215c9e2de81aeb6748dda71dae4f91/chain/test/starknet/conftest.py
# License: MIT

import sys
import os
import time
import asyncio
import pytest
import dill
from types import SimpleNamespace

from starkware.starknet.compiler.compile import compile_starknet_files
from starkware.starknet.testing.starknet import Starknet, StarknetContract
from starkware.starknet.business_logic.state import BlockInfo

from utils.Signer import Signer

# pytest-xdest only shows stderr
sys.stdout = sys.stderr

CONTRACT_SRC = os.path.join(os.path.dirname(__file__), "..", "contracts")


async def build_cache():
    starknet = await Starknet.empty()

    # initialize a realistic timestamp
    set_block_timestamp(starknet.state, round(time.time()))

    # Define contracts
    defs = SimpleNamespace(
        account=compile("Account.cairo"),
        contract=compile("Contract.cairo")
    )

    signers = dict(
        admin=Signer(1),
        unregistered=Signer(2),
        alice=Signer(3),
        bob=Signer(4),
        carol=Signer(5),
        dave=Signer(6),
        eric=Signer(7),
        frank=Signer(8),
        grace=Signer(9),
        hank=Signer(10),
    )

    # Maps from name -> account contract
    accounts = SimpleNamespace(
        **{
            name: (await deploy_account(starknet, signer, defs.account))
            for name, signer in signers.items()
        }
    )

    # Deploy base contracts
    contract = await starknet.deploy(
        contract_def=defs.contract
    )

    consts = SimpleNamespace(
        EXAMPLE_CONSTANT=1,
    )

    return SimpleNamespace(
        starknet=starknet,
        consts=consts,
        signers=signers,
        serialized_contracts=dict(
            admin=serialize_contract(accounts.admin, defs.account.abi),
            alice=serialize_contract(accounts.alice, defs.account.abi),
            bob=serialize_contract(accounts.bob, defs.account.abi),
            carol=serialize_contract(accounts.carol, defs.account.abi),
            dave=serialize_contract(accounts.dave, defs.account.abi),
            eric=serialize_contract(accounts.eric, defs.account.abi),
            frank=serialize_contract(accounts.frank, defs.account.abi),
            grace=serialize_contract(accounts.grace, defs.account.abi),
            hank=serialize_contract(accounts.hank, defs.account.abi),

            # Define contracts on context
            contract=serialize_contract(contract, defs.contract.abi),
        ),
    )

def compile(path):
    return compile_starknet_files(
        files=[os.path.join(CONTRACT_SRC, path)],
        debug_info=True,
    )


def get_block_timestamp(starknet_state):
    return starknet_state.state.block_info.block_timestamp


def set_block_timestamp(starknet_state, timestamp):
    starknet_state.state.block_info = BlockInfo(
        starknet_state.state.block_info.block_number, timestamp
    )


async def deploy_account(starknet, signer, account_def):
    return await starknet.deploy(
        contract_def=account_def,
        constructor_calldata=[signer.public_key],
    )


# StarknetContracts contain an immutable reference to StarknetState, which
# means if we want to be able to use StarknetState's `copy` method, we cannot
# rely on StarknetContracts that were created prior to the copy.
# For this reason, we specifically inject a new StarknetState when
# deserializing a contract.
def serialize_contract(contract, abi):
    return dict(
        abi=abi,
        contract_address=contract.contract_address,
        deploy_execution_info=contract.deploy_execution_info,
    )


def unserialize_contract(starknet_state, serialized_contract):
    return StarknetContract(state=starknet_state, **serialized_contract)


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope="session")
async def copyable_deployment(request):
    CACHE_KEY = "deployment"
    val = request.config.cache.get(CACHE_KEY, None)
    if val is None:
        val = await build_cache()
        res = dill.dumps(val).decode("cp437")
        request.config.cache.set(CACHE_KEY, res)
    else:
        val = dill.loads(val.encode("cp437"))
    return val


@pytest.fixture(scope="session")
async def ctx_factory(copyable_deployment):
    serialized_contracts = copyable_deployment.serialized_contracts
    signers = copyable_deployment.signers
    consts = copyable_deployment.consts

    def make():
        starknet_state = copyable_deployment.starknet.state.copy()
        contracts = {
            name: unserialize_contract(starknet_state, serialized_contract)
            for name, serialized_contract in serialized_contracts.items()
        }

        async def execute(account_name, contract_address, selector_name, calldata):
            return await signers[account_name].send_transaction(
                contracts[account_name],
                contract_address,
                selector_name,
                calldata,
            )

        def advance_clock(num_seconds):
            set_block_timestamp(
                starknet_state, get_block_timestamp(
                    starknet_state) + num_seconds
            )

        return SimpleNamespace(
            starknet=Starknet(starknet_state),
            advance_clock=advance_clock,
            consts=consts,
            execute=execute,
            **contracts,
        )

    return make