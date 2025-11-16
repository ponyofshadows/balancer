[English](https://github.com/ponyofshadows/balancer/blob/master/README.md) | 中文文档

# reaction-balancer
balancer 是一款用于材料科学与凝聚态物理实验的**精确化学方程式配平工具**。  
它从 Markdown 输入文件中解析反应式，使用精确有理数运算和 CIAAW 2024 原子质量表进行计算，并自动生成可直接打印的 Excel 配料表。

---

## 功能特点

### 1. 高精度科学计算
- 使用 **CIAAW (2024)** 最新相对原子质量。  
- 全程采用 **sympy.Rational** 运算，无任何浮点误差。  
- 基于线性代数的求解器确保**配平正确**；若无法配平，会给出清晰的诊断信息。

### 2. 灵活的输入语法
支持括号、分数下标、小数下标，例如：  
- `Ni(NO3)2(H2O)6`  
- `Fe7/8Se`
- `La1.8Sr0.2CuO4.12`  

支持可选的 basis 标签（如 `<BaTiO>`）用于**部分元素配平**，适合溶胶–凝胶及氧化物前驱体路线。

### 3. 自动生成 Excel 配料表
- 自动输出 **可直接打印的 xlsx 表格**，格式整洁。  
- 列宽、样式、对齐方式全部自动调整，无需手动编辑。

### 4. 便于复现与记录
输入文件为 Markdown，可记录：  
- 样品编号  
- 炉温程序  
- 实验细节

如果您用支持Markdown渲染的编辑器，输入文件可以作为简易的电子实验记录本使用。

### 5. 专为材料合成设计
适用于：  
- 固相法  
- 助熔剂（flux）法  
- 水热 / 溶胶–凝胶前驱体路线  
- 铜基 / 铁基 / 镍基 / 硫属化物及各类无机材料的反应式配平

---

## 安装

```bash
pip install balancer
```
或者使用uv:
```bash
uv tool install balancer
```

## 使用方法
在某个目录中运行：
```bash
python -m balancer
# 或使用 uv:
# uv run balancer
```
如果该目录下没有 input.md，程序会自动生成模板文件。

您也可以指定具体路径：
```bash
balancer <filepath>
```
