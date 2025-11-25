# 图像失真分析器（DistortionAnalyzer）

对应实现文件：`src/main/distortion_analyser.py`

该模块提供一个**高层图像失真分析器**，将多种基础失真指标统一计算并组合为向量，用于车漆缺陷图像等场景的质量评估。

## 聚合的失真指标

DistortionAnalyzer 会调用以下组件分析器：

1. **模糊 / 清晰度**（BlurSharpnessAnalyzer）
   - 指标：`Sharpness = Var(∇² I)`
2. **噪声方差**（NoiseVarianceAnalyzer）
   - 指标：灰度图的全局方差
3. **光照不均匀度**（IlluminationUniformityAnalyzer）
   - 指标：`U = σ_L / μ_L`
4. **过曝像素占比**（OverExposureAnalyzer）
   - 指标：过曝像素占比 = 过曝像素数 / 像素总数

## 核心数据结构

### `DistortionMetrics`

- 字段：
  - `sharpness: float`
  - `noise_variance: float`
  - `illumination_uniformity: float`
  - `overexposure_ratio: float`

- 方法：
  - `as_vector() -> np.ndarray`
    - 以固定顺序返回一维向量：
      - `[sharpness, noise_variance, illumination_uniformity, overexposure_ratio]`
  - `as_dict() -> Dict[str, float>`
    - 返回字典形式的指标。

## DistortionAnalyzer 类

### 初始化

```python
DistortionAnalyzer(overexposure_threshold: int = 250)
```

- 参数：
  - `overexposure_threshold`
    - 传给内部的 `OverExposureAnalyzer`，作为过曝判定阈值。

### 图像绑定

```python
bind_image(image: Optional[np.ndarray] = None, *, path: Optional[Union[str, Path]] = None) -> None
```

- 两种使用方式：
  - 传入已经加载的 `numpy.ndarray` 图像；
  - 或者传入图像的磁盘路径。
- 要求：`image` 与 `path` 至少提供一个。

### 失真分析

```python
analyze() -> DistortionMetrics
```

- 将当前绑定的图像传递给各个组件分析器：
  - `BlurSharpnessAnalyzer`
  - `NoiseVarianceAnalyzer`
  - `IlluminationUniformityAnalyzer`
  - `OverExposureAnalyzer`
- 收集上述结果，构造 `DistortionMetrics` 并返回，同时缓存到 `self._metrics`。

### 指标访问

- `metrics: Optional[DistortionMetrics]`
  - 最近一次分析得到的全部指标；若尚未调用 `analyze()` 则为 `None`。

- `metrics_vector() -> np.ndarray`
  - 返回失真指标的一维向量，顺序为：
    - `['sharpness', 'noise_variance', 'illumination_uniformity', 'overexposure_ratio']`
  - 若尚未有分析结果，会抛出 `RuntimeError`。

- `metrics_names() -> Sequence[str]`
  - 返回与向量顺序对应的指标名称列表。

## 典型使用流程示例

1. **创建分析器实例**

   ```python
   from src.main.distortion_analyser import DistortionAnalyzer

   analyzer = DistortionAnalyzer(overexposure_threshold=250)
   ```

2. **绑定图像**

   - 方式一：从路径绑定

     ```python
     analyzer.bind_image(path="path/to/image.jpg")
     ```

   - 方式二：使用已有的 `numpy.ndarray` 图像

     ```python
     import cv2

     img = cv2.imread("path/to/image.jpg", cv2.IMREAD_COLOR)
     analyzer.bind_image(image=img)
     ```

3. **执行分析**

   ```python
   metrics = analyzer.analyze()
   print(metrics)
   print(metrics.as_dict())
   ```

4. **获取失真向量**

   ```python
   vec = analyzer.metrics_vector()
   names = analyzer.metrics_names()
   print(names)
   print(vec)
   ```

## 应用场景建议

- 在数据采集环节对车漆缺陷图像做质量筛查：
  - 剔除过度模糊/严重过曝/光照极不均匀的样本；
  - 将指标作为数据标注或训练时的过滤条件。
- 在生产线上对相机和光源状态做长期监控：
  - 以失真向量为输入，构建统计监控或异常检测模型；
  - 当某一维度指标发生明显漂移时触发报警或维护。
