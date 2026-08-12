# PyFireCA

**面向林火蔓延模拟的模块化、可扩展 Python 元胞自动机框架。**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](#安装)
[![CI](https://github.com/hujinghaoabcd/PyFireCA/actions/workflows/ci.yml/badge.svg)](https://github.com/hujinghaoabcd/PyFireCA/actions/workflows/ci.yml)
[![Status](https://img.shields.io/badge/status-early%20development-orange)](#项目状态)

[English](README.md) · [总体设计](docs/DESIGN.md) · [开发说明](docs/DEVELOPMENT.md) · [验证方案](docs/VALIDATION.md) · [交接文档](docs/HANDOFF.md)

## 为什么做 PyFireCA？

许多林火 CA 实现会把火行为公式、邻域遍历、栅格状态、GIS 输入输出、模拟控制和实验代码混在一起，导致一旦修改 CA 的状态、邻域或转移规则，就需要连带修改大量无关代码。

PyFireCA 从一开始就把研究中最可能持续变化的 **状态、邻域、转移规则和时间推进机制** 与火行为计算、GIS 数据处理分离。早期版本优先保证 NumPy 参考实现清晰、结果可复现、科学验证充分、接口可扩展，而不是过早追求 GPU 或复杂抽象。

## 设计目标

- **以 CA 为核心**：明确使用元胞自动机表达林火空间传播。
- **可扩展**：替换邻域或转移规则时，不重写模拟主循环。
- **火行为解耦**：Rothermel、FBP 等火行为模型与 CA 传播规则分开。
- **GIS 原生意识**：CRS、分辨率、Transform、Extent、NoData 等属于正式数据契约。
- **可复现**：显式随机数生成器、配置、回归测试和验证案例。
- **现代科研软件工程**：`src/` 布局、类型提示、测试、Ruff、pre-commit、CI、设计文档与交接文档从开发第一天维护。

## 架构

```text
GIS / 环境数据
      ↓
     Grid
      ↓
     State
      ↓
 Neighborhood
      ↓
火行为 → Transition Rule
      ↓
  Simulation
      ↓
    Metrics
```

详细设计见 [`docs/DESIGN.md`](docs/DESIGN.md)。

## 安装

当前处于早期开发阶段，建议源码安装：

```bash
git clone https://github.com/hujinghaoabcd/PyFireCA.git
cd PyFireCA
python -m pip install -e ".[dev]"
```

## 快速开始

当前首先建立最小 CA 基础契约，完整林火传播示例将在参考规则验证后加入。

```python
from pyfireca.neighborhood import MooreNeighborhood
from pyfireca.state import FireState

neighborhood = MooreNeighborhood(radius=1)
print(neighborhood.offsets())
print(FireState.BURNING)
```

## 第一阶段科学范围

- 栅格林火 CA；
- 可替换邻域；
- 可替换转移规则；
- 确定性与随机 CA；
- Rothermel / FBP 风格火行为接口；
- 静态与动态环境图层；
- GeoTIFF GIS 工作流；
- NumPy 参考实现，性能剖析后再局部引入 Numba；
- Monte Carlo 与科学验证。

第一阶段明确不做：可微 CA、PyTorch/JAX backend、Level Set、Front Tracking、CFD、城市模拟、Web UI 和分布式服务。

## 开发阶段文档

以下文档必须与代码同步维护：

- [`docs/DESIGN.md`](docs/DESIGN.md)：架构、职责、扩展边界、设计决策；
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)：开发路线和开发规则；
- [`docs/STATUS.md`](docs/STATUS.md)：当前状态、已完成与进行中事项；
- [`docs/HANDOFF.md`](docs/HANDOFF.md)：下一次开发可直接接手的详细交接；
- [`docs/VALIDATION.md`](docs/VALIDATION.md)：科学与数值验证计划。

## 项目状态

当前处于 **Early Development**。第一个里程碑为 `v0.1.0`：先建立小而可靠的 CA reference core，再逐步实现完整林火传播模型。
