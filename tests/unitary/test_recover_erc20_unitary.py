#recoverERC20
import brownie
from brownie_tokens.template import ERC20

# Does the ERC20 recovery function produce expected behavior?
def test_recovery(multi, reward_token, alice, issue):
    multi.recoverERC20(reward_token, 10 ** 10, {"from": alice})
    final_amount = reward_token.balanceOf(alice)
    assert final_amount == issue + (10 ** 10)


# ERC20 function should fail on non-owner
def test_recovery_onlyowner(multi, reward_token, alice, bob, chain, issue):
    with brownie.reverts():
        multi.recoverERC20(reward_token, 10 ** 10, {"from": bob})


# Cannot withdraw the base token from ERC20 function
def test_no_withdraw_staking_token(multi, base_token, alice):
    with brownie.reverts():
        multi.recoverERC20(base_token, 10 ** 10, {"from": alice})

# Reward tokens can be withdrawn only by owner
def test_erc20_only_callable_owner(multi, reward_token, issue, alice, charlie):
    with brownie.reverts("Only the contract owner may perform this action"):
        multi.recoverERC20(reward_token, 10 ** 18, {'from': charlie})
    tx = multi.recoverERC20(reward_token, 10 ** 18, {'from': alice})
    assert tx.events['Recovered'].values()[0] == reward_token


# Assigned distributor cannot recover 
def test_erc20_distributor_nonrecoverable(multi, reward_token, alice, bob):
    reward_token.approve(multi, 10 ** 18, {"from": alice})
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": bob})

    with brownie.reverts("Only the contract owner may perform this action"):
        multi.recoverERC20(reward_token, 10 ** 10, {'from': bob})
    tx = multi.recoverERC20(reward_token, 10 ** 18, {'from': alice})
    assert tx.event['Recovered'].values()[0] == reward_token


# Can withdraw reward tokens 
def test_erc20_distributor_nonrecoverable(multi, reward_token, alice, bob):
    multi.setRewardsDistributor(reward_token, bob, {"from": alice})
    reward_token.approve(multi, 10 ** 10, {"from": bob})
    multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": bob})

    with brownie.reverts("Only the contract owner may perform this action"):
        multi.recoverERC20(reward_token, 10 ** 10, {'from': bob})
    tx = multi.recoverERC20(reward_token, 10 ** 18, {'from': alice})
    assert tx.events['Recovered'].values()[0] == reward_token

# Can be used to withdraw random tokens
def test_transfer_random_tokens(multi, alice):
    random_token = ERC20()
    random_token._mint_for_testing(alice, 10 ** 18, {'from': alice})
    random_token.transfer(multi, 10 ** 18, {'from': alice})
    assert random_token.balanceOf(alice) == 0
    multi.recoverERC20(random_token, 10 ** 18, {'from': alice})
    assert random_token.balanceOf(alice) == 10 ** 18


# Fail on nonexistent tokens 
def test_fail_nonexistent_tokens(multi, alice):
    random_token = ERC20()
    random_token._mint_for_testing(alice, 10 ** 18, {'from': alice})
    with brownie.reverts():
        multi.recoverERC20(random_token, 10 ** 18, {'from': alice})
        multi.recoverERC20(None, 10 ** 18, {'from': alice})
        multi.recoverERC20(None, None, {'from': alice})
