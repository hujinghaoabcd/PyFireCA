# PyFireCA

**面向林火蔓延模拟的模块化、经过验证、GIS 就绪的 Python 元胞自动机框架。**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](#安装)
[![CI](https://github.com/hujinghaoabcd/PyFireCA/actions/workflows/ci.yml/badge.svg)](https://github.com/hujinghaoabcd/PyFireCA/actions/workflows/ci.yml)
[![Status](https://img.shields.io/badge/status-alpha-orange)](#项目状态)

[English](README.md) · [运行模拟器](docs/RUNNING_SIMULATOR.md) · [总体设计](docs/DESIGN.md) · [验证方案](docs/VALIDATION.md) · [当前状态](docs/STATUS.md) · [交接文档](docs/HANDOFF.md)

## 为什么做 PyFireCA？

许多林火 CA 实现会把火行为公式、栅格几何、传播逻辑、GIS 输入输出和实验代码耦合在一起。PyFireCA 将这些职责拆开，使火行为模型、传播语义、空间数据契约和用户工作流可以分别验证、维护和扩展。

当前优先级非常明确：**先把一个简单、完整、现代化、可复现的林火模拟器基线做扎实；新的 PyFireCA 自研 CA 方法先记录，不混入默认实现。**

## 当前基线能力

PyFireCA 已经具备一条端到端静态栅格工作流：

```text
YAML 配置 + 对齐 GeoTIFF + 点火事件
                ↓
             输入验证
                ↓
        已审计标准燃料模型
                ↓
    Albini-adjusted Rothermel
                ↓
 Behave/Catchpole 方向性表面火传播
                ↓
       物理最早到达时间传播
                ↓
 arrival / state / burned footprint
                ↓
   配置、环境、哈希与运行元数据
```

当前已经实现：

- 经固定 Behave 参考验证的 Rothermel 火行为链；
- 风、坡度、动态草本 curing 和可选 wind-speed limit；
- Behave/Catchpole 椭圆及 `FromIgnitionPoint` 非主传播方向 ROS；
- 已审计 Anderson **FM1–FM13** 与 Scott–Burgan **GR1 (101)**；
- 静态空间异质栅格环境；
- 单点、多点以及延迟点火；
- Moore-8 baseline 下的物理最早到达时间传播；
- arrival/state/burned-mask GeoTIFF；
- WGS84 burned-footprint GeoJSON；
- resolved config、输入 SHA-256、燃料 provenance、运行环境、metrics 和 log；
- Python API 与 `pyfireca validate/run` CLI；
- Python 3.11–3.13、GIS、回归与 Behave reference CI。

## 安装

运行文件型 GIS 模拟器：

```bash
git clone https://github.com/hujinghaoabcd/PyFireCA.git
cd PyFireCA
python -m pip install -e ".[gis]"
```

开发环境：

```bash
python -m pip install -e ".[dev,gis]"
```

## 快速开始

以 [`examples/static_run.yml`](examples/static_run.yml) 为配置模板，将路径替换为十个已经对齐的 GeoTIFF，然后先验证：

```bash
pyfireca validate examples/static_run.yml
```

通过后运行：

```bash
pyfireca run examples/static_run.yml
```

输出目录：

```text
runs/static-example/
├── config.resolved.yml
├── metadata.json
├── environment.json
├── metrics.json
├── log.txt
└── outputs/
    ├── arrival_time.tif
    ├── state.tif
    ├── burned_mask.tif
    └── perimeter.geojson
```

输入单位、NoData 语义、点火配置和输出说明见 [`docs/RUNNING_SIMULATOR.md`](docs/RUNNING_SIMULATOR.md)。

## 科学架构

```text
GIS / EnvironmentalData
          ↓
      LandscapeInput
          ↓
   每个格点 Rothermel inputs
          ↓
     FireBehaviorModel
          ↓
     方向性表面火 ROS
          ↓
 edge travel time = distance / ROS
          ↓
     earliest arrival
          ↓
   FireState / GIS outputs
```

项目仍保留原始同步 CA reference path，用于验证 CA 架构和离散规则；它不会被偷偷赋予一个物理 `dt`，也不会替代当前经过验证的物理 arrival baseline。

详细设计见 [`docs/DESIGN.md`](docs/DESIGN.md)。

## 输入数据契约

第一版文件工作流要求所有栅格满足：north-up、方形像元、米制 cell size、完全一致的 shape/CRS/affine alignment。

十个输入层及单位：

```text
fuel model                   整数代码
1-h dead moisture            fraction
10-h dead moisture           fraction
100-h dead moisture          fraction
live herbaceous moisture     fraction
live woody moisture          fraction
midflame wind speed          m/s
meteorological wind-from     degrees
slope                        degrees
aspect                       degrees
```

PyFireCA 不会静默把百分比湿度、百分比坡度、10 m 风、弧度或错位栅格自动转换成“看起来能跑”的输入。

## 验证

科学验证是项目一级能力。当前固定参考包括 USFS Fire Lab Behave 的基础 Rothermel ROS、风坡组合、GR1 动态 curing 以及 off-axis directional spread。外部 reference 保存固定上游 revision 和证据等级。

见 [`docs/VALIDATION.md`](docs/VALIDATION.md) 与 [`docs/ROTHERMEL_REFERENCE.md`](docs/ROTHERMEL_REFERENCE.md)。

## 论文创新线

格网方向偏差、扩展/动态邻域、异质介质 interface coupling 等潜在论文方向已经单独保存到 [`docs/FUTURE_RESEARCH.md`](docs/FUTURE_RESEARCH.md)，**当前只记录，不继续实现**。

当前开发优先级见 [`docs/SIMULATOR_ROADMAP.md`](docs/SIMULATOR_ROADMAP.md)：先完成并冻结简单 simulator baseline，再回来开展自己的 CA 创新。

## 开发阶段文档

以下文档持续与代码同步：

- [`docs/DESIGN.md`](docs/DESIGN.md)：架构与设计决策；
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)：开发路线；
- [`docs/STATUS.md`](docs/STATUS.md)：当前仓库真实状态；
- [`docs/HANDOFF.md`](docs/HANDOFF.md)：详细开发交接；
- [`docs/SESSION_LOG.md`](docs/SESSION_LOG.md)：阶段开发记录；
- [`docs/VALIDATION.md`](docs/VALIDATION.md)：科学与数值验证；
- [`docs/FUTURE_RESEARCH.md`](docs/FUTURE_RESEARCH.md)：暂缓实施的论文创新线。

## 引用

软件引用元数据见 [`CITATION.cff`](CITATION.cff)。

## 项目状态

PyFireCA 当前为 **Alpha research software**。静态 baseline simulator 已能够从 YAML + GeoTIFF 完成端到端模拟；当前剩余工作集中在文档、release-quality 集成检查和少量 baseline polish，然后冻结第一版简单模拟器。

动态天气/WRF、crown fire、spotting、suppression、Monte Carlo、FBP、GPU backend 以及 PyFireCA 自研新 CA 方法都不属于当前 baseline release 的阻塞项。
