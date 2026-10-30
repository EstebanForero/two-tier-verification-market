// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
// Stateful targets with a uniform interface for depth-bounded sequence checking.
// op(a, x): a = action selector, x = argument. Property: inv() must stay true.
interface ISeq { function op(uint a, uint x) external; function inv() external view returns (bool); }

// SmartBugs access_control/wallet_02_refund_nosub (bug needs >=3 txs: deposit, refund, refund)
contract SWalletV is ISeq { mapping(uint=>uint) b; uint pin; uint pout;
  function op(uint a, uint x) external { uint u = x % 2; if (a%2==0) { x = x % 1e30; b[u]+=x; pin+=x; } else { pout += b[u]; } }
  function inv() external view returns (bool) { return pout <= pin; } }
contract SWalletF is ISeq { mapping(uint=>uint) b; uint pin; uint pout;
  function op(uint a, uint x) external { uint u = x % 2; if (a%2==0) { x = x % 1e30; b[u]+=x; pin+=x; } else { pout += b[u]; b[u]=0; } }
  function inv() external view returns (bool) { return pout <= pin; } }
// SmartBugs arithmetic/integer_overflow_multitx_multifunc_feasible (init then run; 2 txs)
contract SMultiV is ISeq { uint init_=1; uint count=1; bool bad;
  function op(uint a, uint x) external { if (a%2==0) init_=0; else if (init_==0) { unchecked { uint c=count; count -= x; if (count > c) bad=true; } } }
  function inv() external view returns (bool) { return !bad; } }
contract SMultiF is ISeq { uint init_=1; uint count=1; bool bad;
  function op(uint a, uint x) external { if (a%2==0) init_=0; else if (init_==0) { if (x>count) return; unchecked { uint c=count; count -= x; if (count > c) bad=true; } } }
  function inv() external view returns (bool) { return !bad; } }
// Injected depth-gated mutants of a fixed counter (operator GATE_d): guard disabled only after d ticks.
contract GateF is ISeq { uint n; uint public bal=100; bool bad;
  function op(uint a, uint x) external { if (a%2==0) n++; else { if (x <= bal) bal -= x; } }
  function inv() external view returns (bool) { return !bad && bal <= 100; } }
contract GateM3 is ISeq { uint n; uint bal=100; bool bad;
  function op(uint a, uint x) external { if (a%2==0) n++; else { if (x <= bal || n >= 2) { unchecked { bal -= x; } } } }
  function inv() external view returns (bool) { return bal <= 100; } }
contract GateM6 is ISeq { uint n; uint bal=100;
  function op(uint a, uint x) external { if (a%2==0) n++; else { if (x <= bal || n >= 5) { unchecked { bal -= x; } } } }
  function inv() external view returns (bool) { return bal <= 100; } }
contract GateM10 is ISeq { uint n; uint bal=100;
  function op(uint a, uint x) external { if (a%2==0) n++; else { if (x <= bal || n >= 9) { unchecked { bal -= x; } } } }
  function inv() external view returns (bool) { return bal <= 100; } }
