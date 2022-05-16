// SPDX-License-Identifier: Apache-2.0
pragma solidity >=0.4.9 <0.9.0;
pragma experimental ABIEncoderV2;

import "./IHederaTokenService.sol";
import "./HederaTokenService.sol";
import "./HederaResponseCodes.sol";

contract RicardianContract is HederaTokenService {

    address owner;
    address tokenAddress;
    int64 multiple;
    mapping(address => int64) public balances;
    string docHash;
    string paramHash;
    string linkHash;

    constructor (address token, int64 _multiple, string memory _docHash, string memory _paramHash, string memory _linkHash) public {
        owner = msg.sender;
        tokenAddress = token;
        multiple = _multiple;
        docHash = _docHash;
        paramHash = _paramHash;
        linkHash = _linkHash;
    }

    modifier isOwner() {
        require(msg.sender == owner, "Not Owner");
        _;
    }

    modifier hasBalance(){
        require(balances[msg.sender]>0, "No Balance");
        _;
    }

    function getAddress() public view returns(address){
        return tokenAddress;
    }

    function getDocHash() public view returns (string memory){
        return docHash;
    }

    function getParamHash() public view returns (string memory){
        return paramHash;
    }

    function getLinkHash() public view returns (string memory){
        return linkHash;
    }

    function getBalance() public view hasBalance returns (int64) {
        return balances[msg.sender];
    } 

    function tokenAssociate(address sender) public {
        int response = HederaTokenService.associateToken(sender, tokenAddress);
        if (response != HederaResponseCodes.SUCCESS) {
            revert ("Associate Failed");
        }
    }

    function transfer(address _sender, address _receiver, int64 _amount) public {        
        int response = HederaTokenService.transferToken(tokenAddress, _sender, _receiver, _amount);
        if (response != HederaResponseCodes.SUCCESS) {
            revert ("Transfer Failed");
        }
        balances[_receiver] += _amount;
    }

    function gift(address _receiver, int64 _amount) public isOwner {
        int response = HederaTokenService.transferToken(tokenAddress, owner, _receiver, _amount);
        if (response != HederaResponseCodes.SUCCESS) {
            revert ("Gift Failed");
        }
    }

    function deposit(address _sender, int64 _amount) public {
        int response = HederaTokenService.transferToken(tokenAddress, _sender, owner, _amount);
        if (response != HederaResponseCodes.SUCCESS) {
            revert ("Deposit Failed");
        }
        balances[msg.sender] += _amount;
    }
    function payout(address _receiver) public isOwner {
        require(balances[_receiver]>0, "Address has no balance");
        int response = HederaTokenService.transferToken(tokenAddress, owner, _receiver, multiple*balances[_receiver]);
        if (response != HederaResponseCodes.SUCCESS) {
            revert ("Payout Failed");
        }
        balances[_receiver] = 0;
    } 
}