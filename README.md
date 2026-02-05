# Jewelry AI Showcase Generator

基于远程 API 的珠宝电商展示图生成工具。将珠宝照片转换为专业的电商产品展示图。

## ✨ 特性

- 🎯 **通用提示词** - 适配所有珠宝类型（项链、耳环、手链、手环、戒指）
- 📐 **保持原图角度** - 自动识别并保持输入图片的拍摄角度
- 🖼️ **专业电商风格** - 纯白背景、深焦距、均匀照明
- 🚀 **批量测试** - 支持批量测试和对比查看
- 🔄 **API 驱动** - 使用远程 API，无需本地 GPU

## 📋 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API

复制配置模板并填写你的 API 信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```python
# API 配置
models = ["gpt-image-1.5", "nano-banana-2-2k-vip"]
base_url = https://api.tu-zi.com
api_keys = YOUR_API_KEY_HERE  # 替换为你的实际 API Key
```

### 3. 生成图片

**单张图片生成**：

```bash
python main.py --image path/to/jewelry.jpg --output result.png
```

## 🛠️ 使用工具

### 单图测试

使用指定提示词生成：

```bash
python tools/quick_prompt_test.py \
  --image "数据/项链/image_1.jpeg" \
  --prompt_file prompts/versions/v2.1_ecommerce_universal.txt \
  --model nano-banana-2-2k-vip \
  --outdir output
```

### 批量测试

测试所有珠宝类型（每类5张图片）：

```bash
python quick_final_test.py
```

随机10张图片测试：

```bash
python quick_random_test.py
```

### 原图 vs 生成图对比

并排查看原图和生成图的效果对比：

```bash
python view_comparison.py
```

**操作说明**：
- `Enter` - 下一张
- `b` - 上一张
- `r` - 重新打开当前对
- `q` - 退出

## 📁 项目结构

```
├── main.py                    # 主程序入口
├── api_client.py              # API 客户端
├── config.py                  # 配置管理
├── utils.py                   # 工具函数
│
├── quick_final_test.py        # 批量测试（4类×5张）
├── quick_random_test.py       # 随机测试（10张）
├── view_comparison.py         # 原图vs生成图对比工具
│
├── tools/
│   ├── quick_prompt_test.py   # 单图测试后端
│   └── batch_prompt_test.py   # 批量提示词测试
│
└── prompts/
    ├── base_prompt.txt        # 基础提示词
    └── versions/
        ├── v2.1_ecommerce_universal.txt  # 当前使用的通用提示词
        ├── v2.0_ecommerce_flat.txt       # 平视角度版本
        └── v1.0_base_threequarter.txt    # 三分角度版本
```

## 🎨 提示词版本说明

### v2.1 通用电商提示词（推荐）

**文件**: `prompts/versions/v2.1_ecommerce_universal.txt`

**核心特性**：
- 保持原图角度（自动适配所有珠宝类型）
- 完整展示，10% 边距，防裁切
- 深焦距，前后景都清晰
- 纯白背景，专业电商风格

**适用场景**：
- 项链（三分角度 → 三分角度）
- 耳环（正面视角 → 正面视角）
- 手链（俯视平铺 → 俯视平铺）
- 其他珠宝类型

### 其他版本

- **v2.0**: 强制正面平视角度
- **v1.0**: 三分角度（可能导致透视模糊）

## 🔧 常用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--image` | 输入图片路径 | 必填 |
| `--model` | 模型名称 | `nano-banana-2-2k-vip` |
| `--control_strength` | 控制强度（0.4-1.0） | `1.0` |
| `--steps` | 生成步数 | `40` |
| `--output` | 输出路径 | `output.png` |
| `--outdir` | 输出目录 | `outputs/` |

## ⚠️ 注意事项

### 控制强度 (control_strength)

- **1.0**（推荐）：最稳定，保持原图特征
- **0.6-0.8**：中等变化，可能改善构图
- **0.4**：大幅变化，可能改变原图风格

### 执行方式

批量测试使用**串行执行**（避免 API 并发冲突）：
```python
MAX_WORKERS = 1  # quick_final_test.py 和 quick_random_test.py
```

### API 配置

- 确保 `.env` 文件不提交到版本控制
- 参考使用 `.env.example` 作为模板
- 保护好 API Key，避免泄露

## 📊 测试结果

当前配置测试通过率：

| 测试类型 | 样本数 | 成功率 |
|---------|--------|--------|
| 分类测试（4类×5张） | 20 | 100% |
| 随机测试 | 10 | 100% |

## 🔗 相关链接

- API 文档：查看对应 API 服务商文档
- 提示词版本历史：查看 `prompts/CHANGELOG.md`

## 📝 License

MIT License
