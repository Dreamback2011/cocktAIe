# 中文字体设置说明

为了在名片上使用中文钢笔字书法字体，系统会尝试按以下顺序加载字体：

## 字体加载优先级

1. **项目字体目录** (`backend/fonts/chinese-calligraphy.ttf`)
   - 如果存在，优先使用此字体

2. **系统字体（Windows）**
   - `C:/Windows/Fonts/STXINGKA.TTF` (华文行楷)
   - `C:/Windows/Fonts/STKAITI.TTF` (华文楷体)
   - `C:/Windows/Fonts/STLITI.TTF` (华文隶书)
   - `C:/Windows/Fonts/FZSTK.TTF` (方正舒体)
   - `C:/Windows/Fonts/FZXINGK.TTF` (方正行楷)

3. **备选字体**
   - Windows: `C:/Windows/Fonts/simhei.ttf` (黑体)
   - macOS: `/System/Library/Fonts/PingFang.ttc` (苹方)

## 如何下载并添加项目字体（可选）

如果您想使用自定义的中文书法字体：

1. 下载中文字体文件（.ttf格式）
   - 推荐字体：华文行楷、方正行楷等
   - 确保字体授权允许商业使用

2. 将字体文件命名为 `chinese-calligraphy.ttf`

3. 放置到以下目录之一：
   - `backend/fonts/chinese-calligraphy.ttf`
   - 或项目根目录的 `fonts/chinese-calligraphy.ttf`

## 字体推荐资源

- **开源字体**: 文泉驿字体项目
- **Windows自带字体**: 华文行楷、华文楷体等（通常已安装在系统中）
- **免费商用字体**: 请确保字体许可允许商用

## 注意事项

- 如果系统已安装书法字体（如华文行楷），程序会自动使用，无需额外下载
- 如果没有找到合适的书法字体，系统会回退到黑体或默认字体
- 字体文件大小通常为2-5MB
