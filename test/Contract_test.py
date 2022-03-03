import pytest
import asyncio

@pytest.mark.asyncio
async def test_contract(ctx_factory):
    ctx = ctx_factory()

    await ctx.execute(
        "alice",
        ctx.contract.contract_address,
        'initialize',
        []
    )

    initialized = await ctx.contract.initialized().call()

    assert initialized.result.res == 1