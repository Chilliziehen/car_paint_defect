# 噪声方差分析器（NoiseVarianceAnalyzer）

对应实现文件：`src/main/distortion_component/noise_variance.py`

## 指标定义

- **噪声强度近似指标**：

  \[
  \text{NoiseLevel} \approx \operatorname{Var}(I)
  \]

  使用图像灰度强度的整体方差作为噪声强度的**简单近似**。

- 说明：
  - 严格意义上的噪声估计需要区分纹理结构与随机噪声，这里采用全局方差作为快速近似指标，适合做粗略的质量监控或相对比较。

## 主要类与接口

### `NoiseVarianceResult`

- 字段：
  - `variance: float` — 灰度图像像素的方差。

### `NoiseVarianceAnalyzer`

- 职责：
  - 绑定一张图像；
  - 转换为灰度；
  - 计算像素强度方差，作为噪声强度近似指标。

- 关键方法：

  - `bind_image(image: Optional[np.ndarray] = None, *, path: Optional[Union[str, Path]] = None) -> None`
    - 绑定待分析图像，可以传入：
      - 已加载的 `numpy.ndarray` 图像；
      - 或者图像文件路径。

  - `analyze() -> NoiseVarianceResult`
    - 将图像转为灰度后，计算整幅图的像素方差并返回。

  - `result: Optional[NoiseVarianceResult]`
    - 最近一次的分析结果缓存。

## 使用建议

- 适合在以下场景中作为参考：
  - 采集环境突然变差（噪声增大）；
  - 相机增益/ISO 调整导致噪声变化；
  - 单批次/多批次样本之间的质量对比。

- 注意事项：
  - 当场景纹理非常丰富时，结构本身也会增加方差，因此该指标更适合于**相对比较**（同一场景不同参数/不同时间）。
