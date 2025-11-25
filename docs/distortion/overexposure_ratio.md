# 过曝像素占比分析器（OverExposureAnalyzer）

对应实现文件：`src/main/distortion_component/overexposure_ratio.py`
# 模糊 / 清晰度分析器（BlurSharpnessAnalyzer）
## 指标定义

- **过曝像素占比**：

  \[
  \text{OverExposureRatio} = \frac{\#\{I(x) \ge T\}}{N}
  \]

  其中：
  - \(I(x)\)：灰度图像中像素 \(x\) 的亮度值；
  - \(T\)：过曝阈值（默认 250，适用于 8-bit 图像）；
  - \(N\)：总像素数；
  - \(\#\{I(x) \ge T\}\)：亮度大于等于阈值的像素个数。

- 含义：
  - 指标越大说明画面中饱和的高亮区域越多，更有可能严重过曝。

## 主要类与接口

### `OverExposureResult`

- 字段：
  - `ratio: float` — 过曝像素占比；
  - `threshold: float` — 使用的过曝阈值。

### `OverExposureAnalyzer`

- 初始化参数：
  - `threshold: int = 250`
    - 过曝判定阈值，默认为 250（适用于 0–255 的 8-bit 图像）。

- 关键方法：

  - `bind_image(image: Optional[np.ndarray] = None, *, path: Optional[Union[str, Path]] = None) -> None`
    - 绑定待分析图像。

  - `analyze() -> OverExposureResult`
    - 将图像转为灰度；
    - 统计 `I(x) >= threshold` 的像素数量并除以总像素数得到占比。
    - 若总像素数为 0，则返回 `ratio = 0.0`。

  - `result: Optional[OverExposureResult]`

## 使用建议

- 与其他指标结合使用：
  - 若过曝占比高，同时清晰度高，但噪声和光照不均匀指标正常，往往说明曝光参数设置不合理；
  - 可用于自动曝光系统的质量监控或报警。

- 阈值调整：
  - 对于不同相机/伽马曲线/后处理流程，可以适当调整阈值 `T`，例如 245、250、252 等。

对应实现文件：`src/main/distortion_component/blur_sharpness.py`

## 指标定义

- **模糊 / 清晰度指标**：

  \[
  \text{Sharpness} = \operatorname{Var}(\nabla^2 I)
  \]

  其中 \(\nabla^2 I\) 为图像灰度强度的拉普拉斯（Laplacian）。

- 直观含义：
  - 值越大，说明图像高频成分越多，边缘更清晰，图像越“锐利”；
  - 值越小，说明图像细节较少，更容易是模糊图像。

## 主要类与接口

### `BlurSharpnessResult`

- 字段：
  - `sharpness: float` — 拉普拉斯响应的方差。

### `BlurSharpnessAnalyzer`

- 职责：
  - 绑定一张图像；
  - 将图像转换为灰度；
  - 计算拉普拉斯；
  - 输出清晰度指标 `sharpness`。

- 关键方法：

  - `bind_image(image: Optional[np.ndarray] = None, *, path: Optional[Union[str, Path]] = None) -> None`
    - 绑定待分析图像，可以传入：
      - 已加载的 `numpy.ndarray` 图像（BGR / RGB 或灰度）；
      - 或者图像文件路径（从磁盘以 BGR 读入）。
    - `image` 和 `path` 至少二选一。

  - `analyze() -> BlurSharpnessResult`
    - 对当前绑定的图像执行分析：
      1. 若为彩色图，则转为灰度；
      2. 使用 OpenCV `cv2.Laplacian` 计算拉普拉斯；
      3. 计算其方差作为清晰度指标。

  - `result: Optional[BlurSharpnessResult]`
    - 最近一次分析结果的缓存，若尚未调用 `analyze()` 则为 `None`。

## 使用建议

- 该指标可以用于：
  - 筛选过于模糊的样本；
  - 监控采集系统焦距/抖动问题；
  - 作为图像质量控制的一个维度，与噪声、曝光等指标结合使用。

- 阈值选择：
  - 不同相机和场景下数值尺度可能不同，通常需要在业务数据上统计分布后再设定“模糊/清晰”的判断阈值。
