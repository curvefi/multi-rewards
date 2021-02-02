# @version 0.2.8
"""
@notice Mock non-standard ERC20 for testing
"""

event Transfer:
    _from: indexed(address)
    _to: indexed(address)
    _value: uint256

event Approval:
    _owner: indexed(address)
    _spender: indexed(address)
    _value: uint256


name: public(String[64])
symbol: public(String[32])
decimals: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)


@external
def __init__(_name: String[64], _symbol: String[32], _decimals: uint256):
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals


@external
def transfer(_to : address, _value : uint256){return_type}:
    if self.balanceOf[msg.sender] < _value:
        {fail_statement}
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(msg.sender, _to, _value)
    {return_statement}


@external
def transferFrom(_from : address, _to : address, _value : uint256){return_type}:
    if self.balanceOf[_from] < _value:
        {fail_statement}
    if self.allowance[_from][msg.sender] < _value:
        {fail_statement}
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    self.allowance[_from][msg.sender] -= _value
    log Transfer(_from, _to, _value)
    {return_statement}


@external
def approve(_spender : address, _value : uint256){return_type}:
    self.allowance[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    {return_statement}


@external
def _mint_for_testing(_target: address, _value: uint256):
    self.totalSupply += _value
    self.balanceOf[_target] += _value
    log Transfer(ZERO_ADDRESS, _target, _value)
