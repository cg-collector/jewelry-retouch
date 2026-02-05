# Prompts Directory

此目录包含珠宝图片生成的提示词模板。

## 版本管理

### 版本命名规则
```
v{major}.{minor}_{use_case}_{style}.txt

major: 重大改动 (角度/构图原则变更)
minor: 微调优化 (措辞/细节调整)
use_case: 使用场景 (base/ecommerce/studio)
style: 风格描述 (threequarter/flat/macro/etc)
```

### 当前版本

| 版本 | 文件 | 用途 | 状态 |
|------|------|------|------|
| v1.0 | `versions/v1.0_base_threequarter.txt` | 参考效果图基准 | ⚠️ 透视模糊 |
| v2.0 | `versions/v2.0_ecommerce_flat.txt` | 电商平台展示 | ✅ 透视已修复 / ⚠️ 裁切问题 |

### 快速链接

```bash
# 当前推荐版本 (软链接)
ln -s versions/v2.0_ecommerce_flat.txt current.txt

# 查看版本历史
cat CHANGELOG.md

# 切换版本
ln -sf versions/v1.0_base_threequarter.txt current.txt
```

## 使用方式

### 直接指定文件
```bash
python tools/quick_prompt_test.py \
  --image "数据/项链/image_1.jpeg" \
  --prompt_file prompts/versions/v2.0_ecommerce_flat.txt \
  --single
```

### 使用 current.txt (推荐)
```bash
python tools/quick_prompt_test.py \
  --image "数据/项链/image_1.jpeg" \
  --prompt_file prompts/current.txt \
  --single
```

## 待测试版本

- **v2.1**: 降低 control_strength (0.7)
- **v2.2**: 添加负面提示词
- **v2.3**: 图片预处理添加 padding

详见 `CHANGELOG.md`
