# QuanSim
**Founder:** [@quantumnewbie](https://github.com/zhangxin20121923)  <br/>
**Contributors:** [@quantumnewbie](https://github.com/zhangxin20121923)  <br/>
**Institution:** Key laboratory of CPS-DSC, Chongqing University
## Introduction
QuanSim is a platform of quantum programming. QuanSim是一款量子编程平台，它包含量子仿真器，
## QuanSim
### Architecture
![](https://raw.githubusercontent.com/zhangxin20121923/QuanSim/master/pic/QuanSim-FrameWork.png) 
We should point out that "Decohenerce Simulator", "Quantum Program Control-flow" and "Analysis and Verification of Quantum program" are still under development. And we will release them in the future.

### Data Type
There are four kinds of data types in QuanSim: Bit, Qubit, Qubits and Circuit. Bit means one classical bit, and the value of this type is either 0 or 1. Qubit is the most basic type in quantum computing, which can be in 0 and 1 simultaneously. Qubits will be generated when Qubit is entangled with other Qubit. And Circuit is the basic executable unit. Please note that each experiment and each circuit is a one-to-one correspondence.<br/>
The relation of these data types are shown as follow.
![](https://raw.githubusercontent.com/zhangxin20121923/QuanSim/master/pic/QuanSim-datatype.png) 

### Quantum Gate
For now, the supported quantum gates include: single-qubit gate (that is, H-gate, X-gate, Y-gate, Z-gate, S-gate, T-gate, $S^dagger$-gate and $T^dagger$-gate) and double-qubit gate (that is, CNOT). And it's clearly that the set of these gates are universal. 

## How to Use It
### Start
You can run QuanSim in the following two ways:<br/>
* 1.<br/>
* 2.<br/>

### About Configuration Files

### Design Your Own Code

## Development Plan