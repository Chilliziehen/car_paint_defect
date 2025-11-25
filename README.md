# car_paint_defect

基于图像处理的车漆缺陷检测程序（阶段性成果记录）。

## 当前阶段性成果

### 1. 图像增强接口（Enhancement）

位置：`src/main/enhancement.py`

- 定义了 **JPG 图像增强器的抽象基类**：`BaseImageEnhancer`
- 支持：
  - 绑定待处理图像：
    - 通过内存图像对象（`numpy.ndarray` 或 `PIL.Image.Image`）
    - 或通过文件路径（惰性加载）
  - 统一管理、访问所有增强算法可能共用的参数：
    - 输入尺寸 `input_size`
    - 是否归一化 `normalize`
    - 颜色空间 `color_space`
    - 值裁剪范围 `clip_range`
    - 可扩展公共参数字典 `metadata`
- 通用配置通过 `EnhancementConfig` 数据类封装，方便子类重用与追踪参数。

接口说明文档：`docs/enhancement/base.md`

---

### 2. 图像失真分析组件（Distortion Components）

位置：`src/main/distortion_component/`

已实现的失真参数分析器：

1. `blur_sharpness.py`
   - 模糊 / 清晰度分析器 `BlurSharpnessAnalyzer`
   - 指标：
     - \( \text{Sharpness} = \operatorname{Var}(\nabla^2 I) \)
     - 使用灰度图的拉普拉斯方差评价图像清晰度（值越大越清晰）。

2. `noise_variance.py`
   - 噪声方差分析器 `NoiseVarianceAnalyzer`
   - 指标：
     - 以灰度图整体方差作为噪声强度的近似指标（快速粗略评估）。

3. `illumination_uniformity.py`
   - 光照均匀性分析器 `IlluminationUniformityAnalyzer`
   - 指标：
     - \( U = \sigma_L / \mu_L \)
     - \(L\) 为灰度亮度，\(\sigma_L\) 为标准差，\(\mu_L\) 为均值，值越大说明光照越不均匀。

4. `overexposure_ratio.py`
   - 过曝像素占比分析器 `OverExposureAnalyzer`
   - 指标：
     - 过曝像素占比 = 亮度值大于等于阈值 `T` 的像素数 / 总像素数
     - 默认阈值 `T = 250`（适用于 8-bit 图像）。

每个组件均支持：
- 绑定图像（内存或路径，内部用 OpenCV 读取）
- 调用 `analyze()` 返回对应的结果数据类（包含指标数值）

文档位置：`docs/distortion/`
- `blur_sharpness.md`
- `noise_variance.md`
- `illumination_uniformity.md`
- `overexposure_ratio.md`

---

### 3. 图像失真分析器（DistortionAnalyzer）

位置：`src/main/distortion_analyser.py`

- 高层封装类：`DistortionAnalyzer`
- 聚合上面的 4 个失真分析组件，面向单张图像输出统一的失真指标：
  - 清晰度 `sharpness`
  - 噪声方差 `noise_variance`
  - 光照不均匀度 `illumination_uniformity`
  - 过曝像素占比 `overexposure_ratio`
- 提供的核心接口：
  - `bind_image(image: np.ndarray = None, *, path: str | Path = None)`
    - 绑定待分析图像（内存或路径二选一）。
  - `analyze() -> DistortionMetrics`
    - 调用所有子分析器，返回 `DistortionMetrics` 数据类实例。
  - `metrics_vector() -> np.ndarray`
    - 以固定顺序返回 4 维失真向量：
      - `[sharpness, noise_variance, illumination_uniformity, overexposure_ratio]`
  - `metrics_names() -> Sequence[str]`
    - 返回与向量顺序一一对应的指标名称列表。

详细文档：`docs/distortion/distortion_analyser.md`

---

### 4. 失真分析可视化测试脚本

位置：`src/test/test_distortion_analyser.py`

功能：
- 从数据集中随机抽取测试图片，计算失真向量并**直接绘制到图像左上角**，便于肉眼快速检查。

具体行为：
1. 从 `data/car_paint_defect/test/images` 目录中随机选取 5 张图像。
2. 对每张图像：
   - 使用 `DistortionAnalyzer` 计算失真向量；
   - 将 4 个失真分量按如下形式叠放在左上角：
     - 绿色文字
     - 每个分量单独一行，从上到下排列
     - 无实心背景矩形（底部为原图像，相当于“透明底部”）
3. 将处理后的图像输出到：`test_out/distortion/` 目录。

运行方式（Windows / cmd）：

```bat
cd /d D:\Repositories\ImageProcessing\car_paint_defect
python src\test\test_distortion_analyser.py
```

运行成功后，可以在 `test_out\distortion` 目录查看结果图像，每张图左上角会有类似：

```text
sharpness=123.456
noise_variance=7.890
illumination_uniformity=0.123
overexposure_ratio=0.001
```
