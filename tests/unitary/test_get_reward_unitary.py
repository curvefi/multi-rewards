#getReward

# Can user retrieve reward after a time cycle?
def test_get_reward(multi, base_token, reward_token, alice, issue, chain):
    amount = 10 ** 10
    init_reward_balance = reward_token.balanceOf(alice)
    base_token.approve(multi, amount, {'from': alice})
    multi.stake(amount, {"from": alice})

    chain.mine(timedelta=60)
   
    earnings = multi.earned(alice, reward_token)
    assert earnings > 0

    multi.getReward({"from": alice})
    final_reward_balance = reward_token.balanceOf(alice)
    assert final_reward_balance - init_reward_balance  == earnings


# Reward per token over many cycles?
def test_multiuser_reward_per_token_paid(multi, reward_token, alice, chain):
    reward_token._mint_for_testing(alice, 10 ** 18, {'from': alice})
    reward_token.approve(multi, 10 ** 18, {"from": alice})
    multi.setRewardsDistributor(reward_token, alice, {"from": alice})
    multi.stake(10 ** 10, {"from": alice})

    for i in range(5):
        last_val = multi.userRewardPerTokenPaid(alice, reward_token)
        multi.notifyRewardAmount(reward_token, 10 ** 10, {"from": alice})
        chain.mine(timedelta=60)
        earnings = multi.earned(alice, reward_token)
        tx = multi.getReward()
        assert multi.userRewardPerTokenPaid(alice, reward_token) > last_val
        assert tx.events['RewardPaid'].values()[2] == earnings


# User should not be able to withdraw a reward if empty
def test_cannot_get_empty_reward(multi, reward_token, alice, chain):
    init_amount = reward_token.balanceOf(alice)
    chain.mine(timedelta=60)
    multi.getReward({"from": alice})
    final_amount = reward_token.balanceOf(alice)
    assert init_amount == final_amount


# User should not be able to withdraw a reward if empty
def test_no_action_on_empty_reward(multi, reward_token, charlie):
    tx = multi.getReward({'from': charlie})
    assert "RewardPaid" not in tx.events 

# Call from a user who is staked should receive the correct amount of tokens
def test_staked_token_value(multi, reward_token, base_token, alice, charlie, issue, chain):
    amount = base_token.balanceOf(charlie)
    reward_init_bal = reward_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {'from': charlie})
    assert base_token.balanceOf(charlie) == 0
    assert multi.balanceOf(charlie) == amount

    chain.mine(timedelta=60)
    reward_per_token = multi.rewardPerToken(reward_token)
    earned_calc = reward_per_token * amount // 10 ** 18
    assert earned_calc == multi.earned(charlie, reward_token)
    
    tx = multi.getReward({'from': charlie}) 
    assert tx.events['RewardPaid'].values()[2] == earned_calc
    assert reward_token.balanceOf(charlie) - reward_init_bal == earned_calc


# Call from a user who is staked should receive the correct amount of tokens
def test_staked_token_value(multi, reward_token, base_token, alice, charlie, issue, chain):
    amount = base_token.balanceOf(charlie)
    reward_init_bal = reward_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {'from': charlie})
    assert base_token.balanceOf(charlie) == 0
    assert multi.balanceOf(charlie) == amount

    chain.mine(timedelta=60)
    reward_per_token = multi.rewardPerToken(reward_token)
    earned_calc = reward_per_token * amount // 10 ** 18
    assert earned_calc == multi.earned(charlie, reward_token)
    
    tx = multi.getReward({'from': charlie}) 
    assert tx.events['RewardPaid'].values()[2] == earned_calc
    assert reward_token.balanceOf(charlie) - reward_init_bal == earned_calc

# Call from a user who is staked should receive the correct amount of tokens
# Also confirm earnings at various stages
def test_staked_tokens_multi_durations(multi, reward_token, slow_token, base_token, alice, charlie, issue, chain):
    reward_init_bal = reward_token.balanceOf(charlie)
    slow_init_bal = slow_token.balanceOf(charlie)

    # Earned Unstaked
    assert multi.earned(charlie, reward_token) == 0 
    amount = base_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {'from': charlie})

    # Earned Staked + No Action
    assert multi.earned(charlie, reward_token) == 0 
    assert base_token.balanceOf(charlie) == 0
    assert multi.balanceOf(charlie) == amount
    paid_slow = 0
    paid_reward = 0
    for i in range(5):
        chain.mine(timedelta=30 )
        mine_timestamp= chain.time()
        reward_per_token = multi.rewardPerToken(reward_token)
        earned_calc = (amount * (reward_per_token - multi.userRewardPerTokenPaid(charlie, reward_token))) // 10 ** 18

        # Earned Staked + Unclaimed
        assert earned_calc == multi.earned(charlie, reward_token)

        reward_per_slow_token = multi.rewardPerToken(slow_token)
        slow_earned_calc = (amount * (reward_per_slow_token - multi.userRewardPerTokenPaid(charlie, slow_token))) // 10 ** 18
        assert slow_earned_calc == multi.earned(charlie, slow_token)

        multi.getReward({'from': charlie}) 
        # Earned Claimed
        assert multi.earned(charlie, reward_token) == 0
        if chain.time() == mine_timestamp:
            assert reward_token.balanceOf(charlie) - reward_init_bal == earned_calc
            assert slow_token.balanceOf(charlie) - slow_init_bal == slow_earned_calc
        else:
            assert reward_token.balanceOf(charlie) - reward_init_bal >= earned_calc
            assert slow_token.balanceOf(charlie) - slow_init_bal >= slow_earned_calc
            assert slow_token.balanceOf(charlie) - slow_init_bal <= slow_earned_calc * 1.05
 
        reward_init_bal = reward_token.balanceOf(charlie)
        slow_init_bal = slow_token.balanceOf(charlie)

    multi.withdraw(multi.balanceOf(charlie), {'from': charlie})
    assert multi.earned(charlie, reward_token) == 0

# A user that has withdrawn should still be able to claim their rewards
def test_withdrawn_user_can_claim(multi, reward_token, base_token, alice, charlie, issue, chain):
    amount = base_token.balanceOf(charlie)
    reward_init_bal = reward_token.balanceOf(charlie)
    base_token.approve(multi, amount, {"from": charlie})
    multi.stake(amount, {'from': charlie})
    assert base_token.balanceOf(charlie) == 0
    assert multi.balanceOf(charlie) == amount

    chain.mine(timedelta=60)
    reward_per_token = multi.rewardPerToken(reward_token)
    earned_calc = reward_per_token * amount // 10 ** 18
    assert earned_calc == multi.earned(charlie, reward_token)
    
    multi.withdraw(amount, {'from': charlie})
    assert multi.balanceOf(charlie) == 0

    tx = multi.getReward({'from': charlie}) 
    assert tx.events['RewardPaid'].values()[2] == earned_calc
    assert reward_token.balanceOf(charlie) - reward_init_bal == earned_calc


