# Prompts Changelog

## Version History

### v1.0 - base_prompt.txt (原始版本)
**用途**: 参考理想效果图的基础提示词
**特点**: 三分角度、艺术感、微距特写

```
关键特征:
- Angle: three-quarter screen left angle
- Style: Extreme close-up, Macro shot
- Focus: Shallow depth of field
```

**问题**:
- ❌ 透视导致远处部分模糊
- ❌ 特写裁切导致产品展示不完整

---

### v2.0 - ecommerce_flat_view.txt (电商版本)
**创建时间**: 2026-02-03
**用途**: 电商平台商品展示图

#### 修改内容

| 维度 | v1.0 (base) | v2.0 (ecommerce) | 解决原理 |
|------|-------------|------------------|---------|
| **角度** | `three-quarter screen left angle` | `Front-facing, straight-on view` | 平视减少透视变形，所有部分距离镜头接近，清晰度一致 |
| **景深** | `shallow depth of field` | `Deep focus (large depth of field)` | 大景深确保前后都清晰 |
| **构图** | `Extreme close-up` | `Complete product display, NO cropping` | 明确禁止裁切 |
| **边距** | 无要求 | `minimum 10% frame space` | 强制留白 |
| **光照** | `focused studio lighting` | `Even, balanced studio lighting from multiple directions` | 多角度均匀光照，消除阴影区 |

#### 为什么可以解决透视问题

**透视模糊的根本原因**:
```
三分角度拍摄时，物体各部分距离镜头不同:
近处部分 → 距离近 → 清晰
远处部分 → 距离远 → 在浅景深下模糊
```

**v2.0 解决方案**:
1. **角度改为平视** - 物体各部分距离镜头基本相等
2. **景深改为深** - Deep focus 确保整个物体都在清晰范围内
3. **光照均匀化** - 多方向照明消除局部暗区

#### 仍未解决的问题

**裁切问题分析**:
- 提示词中已明确要求 `NO cropping` 和 `complete edges visible`
- 但可能的原因:
  1. ControlNet/Image-to-Image 模型倾向于保持原图构图比例
  2. 提示词权重不足，被原图的构图信息压制
  3. `control_strength=1.0` 过高，模型严格遵循原图布局

**进一步解决方案**:
1. 降低 `control_strength` 到 0.6-0.8
2. 增加负面提示词: `cropped, close-up, zoomed in, partial view`
3. 调整输入图片预处理: 强制添加 padding

---

## 待测试方向

### v2.1 - 降低控制强度
```python
control_strength = 0.7  # 从 1.0 降低
```

### v2.2 - 添加负面提示词
在发送给 API 前，给图片添加 10-15% 的白色边框