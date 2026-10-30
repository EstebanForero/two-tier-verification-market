// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
import "forge-std/Test.sol";
import "../src/Seq.sol";
// Sequence harness: up to 12 steps; halmos --loop k bounds the number of steps explored.
abstract contract SeqH is Test {
  function mk() internal virtual returns (ISeq);
  function run(uint ops, uint[12] memory xs, uint len) internal {
    ISeq t = mk();
    for (uint i = 0; i < len; i++) // len is a compile-time bound k = #transactions
      { t.op((ops >> i) & 1, xs[i]); assertTrue(t.inv()); }
  }
  function check_seq_k1(uint ops, uint[12] memory xs) public { run(ops, xs, 1); }
  function check_seq_k2(uint ops, uint[12] memory xs) public { run(ops, xs, 2); }
  function check_seq_k3(uint ops, uint[12] memory xs) public { run(ops, xs, 3); }
  function check_seq_k4(uint ops, uint[12] memory xs) public { run(ops, xs, 4); }
  function check_seq_k6(uint ops, uint[12] memory xs) public { run(ops, xs, 6); }
  function check_seq_k8(uint ops, uint[12] memory xs) public { run(ops, xs, 8); }
}
contract T_SWalletV is SeqH { function mk() internal override returns (ISeq) { return new SWalletV(); } }
contract T_SWalletF is SeqH { function mk() internal override returns (ISeq) { return new SWalletF(); } }
contract T_SMultiV is SeqH { function mk() internal override returns (ISeq) { return new SMultiV(); } }
contract T_SMultiF is SeqH { function mk() internal override returns (ISeq) { return new SMultiF(); } }
contract T_GateF is SeqH { function mk() internal override returns (ISeq) { return new GateF(); } }
contract T_GateM3 is SeqH { function mk() internal override returns (ISeq) { return new GateM3(); } }
contract T_GateM6 is SeqH { function mk() internal override returns (ISeq) { return new GateM6(); } }
contract T_GateM10 is SeqH { function mk() internal override returns (ISeq) { return new GateM10(); } }
