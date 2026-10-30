// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import "forge-std/Test.sol";
import "../src/Targets.sol";
interface ICount { function count() external view returns (uint); function run(uint) external; }
contract AddTest is Test {
  function _p(address c, uint i) internal { uint b = ICount(c).count(); try ICount(c).run(i) { assertGe(ICount(c).count(), b); } catch {} }
  function check_AddV(uint i) public { _p(address(new AddV()), i); }
  function check_AddF(uint i) public { _p(address(new AddF()), i); }
  function check_AddM_unchecked(uint i) public { _p(address(new AddM_unchecked()), i); }
  function testFuzz_AddV(uint i) public { _p(address(new AddV()), i); }
}
contract SubTest is Test {
  function _p(address c, uint i) internal { uint b = ICount(c).count(); try ICount(c).run(i) { assertLe(ICount(c).count(), b); } catch {} }
  function check_SubV(uint i) public { _p(address(new SubV()), i); }
  function check_SubF(uint i) public { _p(address(new SubF()), i); }
  function check_SubM_relop(uint i) public { _p(address(new SubM_relop()), i); }
}
contract MulTest is Test {
  function _p(address c, uint i) internal { uint b = ICount(c).count(); try ICount(c).run(i) { if (i != 0) assertEq(ICount(c).count() / i, b); } catch {} }
  function check_MulV(uint i) public { _p(address(new MulV()), i); }
  function check_MulF(uint i) public { _p(address(new MulF()), i); }
}
interface IX { function mint(address,uint) external; function transfer(address,uint) external; function balanceOf(address) external view returns(uint); }
contract XferTest is Test {
  // conservation: sum of sender+receiver balances unchanged (distinct addrs)
  function _p(address c, address a, address b, uint x, uint y, uint v) internal {
    vm.assume(a != b); IX t = IX(c); t.mint(a,x); t.mint(b,y);
    unchecked { vm.assume(x + y >= x); }
    vm.prank(a); try t.transfer(b,v) { assertLe(t.balanceOf(a), x); assertGe(t.balanceOf(b), y); } catch {}  // no-inflation (v1 used modular conservation: too weak, see README)
  }
  function check_XferV(address a,address b,uint x,uint y,uint v) public { _p(address(new XferV()),a,b,x,y,v); }
  function check_XferF(address a,address b,uint x,uint y,uint v) public { _p(address(new XferF()),a,b,x,y,v); }
  function check_XferM_delreq(address a,address b,uint x,uint y,uint v) public { _p(address(new XferM_delreq()),a,b,x,y,v); }
}
interface IW { function deposit(uint) external; function refund() external; function paidIn() external view returns(uint); function paidOut() external view returns(uint); }
contract WalletTest is Test {
  // solvency over a 2-call sequence: paidOut <= paidIn
  function _p(address c, uint v, uint k) internal { IW w = IW(c); w.deposit(v); w.refund(); if (k % 2 == 0) w.refund(); else w.deposit(0); assertLe(w.paidOut(), w.paidIn()); }
  function check_WalletV(uint v, uint k) public { _p(address(new WalletV()), v, k); }
  function check_WalletF(uint v, uint k) public { _p(address(new WalletF()), v, k); }
}
interface IB { function add() external payable; function withdraw() external; }
contract Attacker { IB t; uint public n; constructor(IB _t){t=_t;} function go() external payable { t.add{value:msg.value}(); t.withdraw(); }
  receive() external payable { if (n++ < 1 && address(t).balance >= msg.value) t.withdraw(); } }
contract BankTest is Test {
  // attacker cannot extract more than it deposited (victim has `other` from honest user)
  function _p(address c, uint dep, uint other) internal {
    vm.assume(dep > 0 && dep < 1e30 && other < 1e30);
    vm.deal(address(0xBEEF), other); vm.prank(address(0xBEEF)); IB(c).add{value: other}();
    Attacker at = new Attacker(IB(c)); vm.deal(address(this), dep);
    try at.go{value: dep}() { assertLe(address(at).balance, dep); } catch {}
  }
  function check_BankV(uint d, uint o) public { _p(address(new BankV()), d, o); }
  function check_BankF(uint d, uint o) public { _p(address(new BankF()), d, o); }
}
contract Reverter { fallback() external { revert(); } }
interface IR { function run(address) external; function done() external view returns(uint); }
contract RetTest is Test {
  function _p(address c) internal { address r = address(new Reverter()); try IR(c).run(r) { assertEq(IR(c).done(), 0); } catch {} }
  function check_RetV() public { _p(address(new RetV())); }
  function check_RetF() public { _p(address(new RetF())); }
}
