// SPDX-License-Identifier: MIT
// Minimal 0.8 ports of SmartBugs Curated contracts. V=original bug (unchecked to keep 0.4 wrap semantics),
// F=fixed, M*=mutants of F produced by documented pattern operators (see README).
pragma solidity ^0.8.24;

// --- arithmetic/integer_overflow_add.sol
contract AddV { uint public count = 1; function run(uint i) public { unchecked { count += i; } } }
contract AddF { uint public count = 1; function run(uint i) public { count += i; } }
contract AddM_unchecked { uint public count = 1; function run(uint i) public { unchecked { count += i; } } } // op UNCHK
// --- arithmetic/integer_overflow_minimal.sol
contract SubV { uint public count = 1; function run(uint i) public { unchecked { count -= i; } } }
contract SubF { uint public count = 1; function run(uint i) public { require(i <= count); unchecked { count -= i; } } }
contract SubM_relop { uint public count = 1; function run(uint i) public { require(i <= count + 1); unchecked { count -= i; } } } // op RELOP(off-by-one)
// --- arithmetic/integer_overflow_mul.sol
contract MulV { uint public count = 2; function run(uint i) public { unchecked { count *= i; } } }
contract MulF { uint public count = 2; function run(uint i) public { count *= i; } }
// --- arithmetic/insecure_transfer.sol
contract XferV { mapping(address=>uint) public balanceOf;
  function mint(address a, uint v) public { balanceOf[a] = v; }
  function transfer(address to, uint v) public { require(balanceOf[msg.sender] >= v); unchecked { balanceOf[msg.sender] -= v; balanceOf[to] += v; } } }
contract XferF { mapping(address=>uint) public balanceOf;
  function mint(address a, uint v) public { balanceOf[a] = v; }
  function transfer(address to, uint v) public { require(balanceOf[msg.sender] >= v); balanceOf[msg.sender] -= v; balanceOf[to] += v; } }
contract XferM_delreq { mapping(address=>uint) public balanceOf;
  function mint(address a, uint v) public { balanceOf[a] = v; }
  function transfer(address to, uint v) public { unchecked { balanceOf[msg.sender] -= v; } balanceOf[to] += v; } } // op DELREQ
// --- access_control/wallet_02_refund_nosub.sol (accounting only; transfer modelled as counter)
contract WalletV { mapping(address=>uint) public balances; uint public paidOut; uint public paidIn;
  function deposit(uint v) public { balances[msg.sender] += v; paidIn += v; }
  function refund() public { paidOut += balances[msg.sender]; } }
contract WalletF { mapping(address=>uint) public balances; uint public paidOut; uint public paidIn;
  function deposit(uint v) public { balances[msg.sender] += v; paidIn += v; }
  function refund() public { uint b = balances[msg.sender]; balances[msg.sender] = 0; paidOut += b; } }
// --- reentrancy/etherbank.sol
contract BankV { mapping(address=>uint) public bal;
  function add() public payable { bal[msg.sender] += msg.value; }
  function withdraw() public { uint a = bal[msg.sender]; (bool ok,) = msg.sender.call{value:a}(""); require(ok); bal[msg.sender] = 0; } }
contract BankF { mapping(address=>uint) public bal;
  function add() public payable { bal[msg.sender] += msg.value; }
  function withdraw() public { uint a = bal[msg.sender]; bal[msg.sender] = 0; (bool ok,) = msg.sender.call{value:a}(""); require(ok); } }
// --- unchecked_low_level_calls/unchecked_return_value.sol (property: failed callee => caller reverts)
contract RetV { uint public done; function run(address c) public { c.call(""); done++; } }
contract RetF { uint public done; function run(address c) public { (bool ok,) = c.call(""); require(ok); done++; } }
