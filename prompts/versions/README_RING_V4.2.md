# v4.2 戒指平放俯视提示词 - 生产版本说明

## 版本信息

- **版本号**: v4.2
- **文件**: `prompts/versions/v4.2_ring_flat_texture_aware.txt`
- **词数**: 154 词
- **状态**: ✅ 生产就绪（有限制）
- **测试通过率**: 66.7% (4/6)

## 适用范围

### ✅ 推荐使用

- 素圈戒指
- 简单单钻戒指
- 简单装饰戒指

### ⚠️ 需要人工审核

- 中等复杂度装饰戒指
- 多颗小钻戒指
- 特殊造型戒指

### ❌ 不推荐

- 复杂多钻戒指
- 猎豹等复杂造型戒指
- 高级珠宝款戒指

**建议**: 上述类型使用通用提示词 v2.1（无角度转换）

## 提示词内容

```
I. Texture Preservation (CRITICAL - MAINTAIN EXACT FINISH)

Preserve the EXACT metal finish from input image:
- Carefully observe: is the surface polished (glossy/reflective) or matte/brushed?
- MAINTAIN the same finish type in output - DO NOT change it
- If input is HIGHLY POLISHED/mirror finish → keep reflective glossy finish
- If input is MATTE/BRUSHED/TEXTURED → keep matte texture
- DO NOT convert polished to matte or matte to polished
- DO NOT add reflections that change texture character
- DO NOT smooth out textured surfaces
- Texture consistency is MORE IMPORTANT than lighting uniformity

II. Angle & Composition

Top-down flat lay view (ring parallel to frame):
- Reorient ring to show it from directly above
- Ring should appear parallel to image frame (not at an angle)
- Show complete circumference - no cropping
- Ring lies naturally flat, centered in frame
- Minimum 15% frame padding around entire ring

III. Background & Lighting

Pure white (#FFFFFF) only:
- Remove ALL input background elements
- Studio lighting that preserves (not overpowers) the original texture

IV. Focus

Razor-sharp focus on all details:
- Professional e-commerce quality
```

## 质量控制

### 人工审核清单

对于中等复杂度戒指，生成后检查：

- [ ] 产品类型是否一致
- [ ] 金属颜色是否正确
- [ ] 宝石数量是否准确
- [ ] 装饰细节是否保留
- [ ] 是否为俯视角度

### 常见失败模式

1. **产品类型改变**（最严重）
   - 钻戒 → 素圈
   - 复杂装饰 → 简单款

2. **金属颜色错误**
   - 黄金 → 白金
   - 白金 → 黄金

3. **装饰丢失**
   - 宝石消失
   - 图案丢失

## 版本历史

### v4.2 (当前版本)
- 154 词，简洁指令
- 66.7% 测试通过率
- 生产就绪

### v4.2.1 (已废弃)
- 205 词，增强约束
- 25% 通过率
- 效果更差，不推荐

### v4.2.2 (已废弃)
- 175 词，严格优先级
- 0% 通过率
- 效果更差，不推荐

### v4.2.4 (已废弃)
- 142 词，描述式方法
- 0% 通过率
- 效果更差，不推荐

### v4.3 (已废弃)
- 278 词，采用项链结构
- 0% 通过率
- 项链结构不适用于戒指

## 相关版本

- **v2.1 通用提示词**: 用于不适合角度转换的复杂戒指
- **v4.3, v4.4 侧视/斜角**: 其他戒指角度（开发中）

## 参考资料

- 测试结果: `check/ring_flat_20260302_151055/`
- 评估报告: `check/ring_flat_20260302_151055/evaluation/evaluation_summary.json`
- 部署指南: `check/RING_FLAT_LAY_DEPLOYMENT_GUIDE.md`

---

**创建日期**: 2026-03-02
**最后更新**: 2026-03-02
**维护者**: AI Team
