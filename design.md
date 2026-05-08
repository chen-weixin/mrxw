---
name: Warm China Finance
description: 中国市场财经新闻视频设计系统 — 琥珀金主调 + 深炭灰底
type: design
origin: custom
---

## 调色板

```yaml
colors:
  primary:      "#D4A853"   # 琥珀金 — 代表财富、权威、温暖
  on-primary:   "#1A1A1A"
  background:   "#0F0E0B"   # 深炭灰 — 中国财经媒体惯用深底
  surface:      "#1C1917"   # 卡片层
  surface-alt:  "#252220"   # 次级卡片
  accent-amber:"#E8B84A"   # 亮金 — 高亮强调
  accent-red:  "#C53D3D"   # 中国红 — 下跌/负面指示
  accent-sage: "#4A7C59"   # 翠绿 — 上涨/正面指示
  accent-blue: "#4A6FA5"   # 钴蓝 — 持平/中性
  text-primary:"#F5F0E8"   # 暖白
  text-muted:  "#8A8278"   # 次要文字
  divider:     "rgba(212,168,83,0.15)"  # 金色分隔线

typography:
  headline:
    fontFamily: "Georgia", "STKaiti", serif
    fontSize: 72px
    fontWeight: 700
    lineHeight: 1.1
    color: "#D4A853"
  subheadline:
    fontFamily: "Georgia", "STKaiti", serif
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif
    fontSize: 32px
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "SF Mono", "Menlo", monospace
    fontSize: 20px
    fontWeight: 500
    letterSpacing: 3px
  stat:
    fontFamily: "SF Mono", "Menlo", monospace
    fontSize: 80px
    fontWeight: 900
    fontVariantNumeric: tabular-nums

motion:
  energy: medium
  easing:
    entry: "power3.out"
    exit: "power3.in"
    ambient: "sine.inOut"
  duration:
    entrance: 0.5
    hold: 2.0
    transition: 0.5

rounded:
  sm: 4px
  md: 12px
  lg: 20px

spacing:
  sm: 16px
  md: 32px
  lg: 60px
```

## 视觉语言

**关键词：** 财富感、权威感、温暖、克制、中国市场

**背景构成：**
- 深炭灰底色 (#0F0E0B)
- 左上/右上/左下角暖金色径向渐变光晕（opacity 15-25%）
- 背景网格线（1px，金色 5% 透明度，60px 间距）
- 右上角 ghost type（大号新闻编号，opacity 8%）

**卡片风格：**
- 深色卡片 (surface: #1C1917)
- 1-2px 金色描边 (rgba(212,168,83,0.2))
- 12px 圆角
- 内填充 32px

**装饰元素：**
- 金色左边缘强调线（4px 宽，accent-amber）
- 底部 ticker 条（深色底，实时行情展示）
- 顶部数据栏（时间、来源标签）

**字体配对：**
- 标题：Georgia / STKaiti（中文衬线）
- 正文：PingFang SC / Microsoft YaHei
- 数据/标签：SF Mono / Menlo
