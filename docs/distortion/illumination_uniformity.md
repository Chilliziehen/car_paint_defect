# 光照均匀性分析器（IlluminationUniformityAnalyzer）

对应实现文件：`src/main/distortion_component/illumination_uniformity.py`

## 指标定义

- **光照不均匀度指标**：

  \[
  U = \frac{\sigma_L}{\mu_L}
  \]

  其中：
  - \(L\)：图像灰度（亮度）;
  - \(\sigma_L\)：灰度的标准差；
  - \(\mu_L\)：灰度的均值。

- 含义：
  - \(U\) 越大，说明灰度分布在空间上波动越大，光照越不均匀；
  - \(U\) 越小，说明场景亮度分布更均匀。

## 主要类与接口

### `IlluminationUniformityResult`

- 字段：
  - `uniformity: float` — 指标 \(U = \sigma_L / \mu_L\)。

### `IlluminationUniformityAnalyzer`

- 职责：
  - 绑定一张图像；
  - 转为灰度；
  - 计算均值和标准差，并得到光照不均匀度指标 \(U\)。

- 关键方法：

  - `bind_image(image: Optional[np.ndarray] = None, *, path: Optional[Union[str, Path]] = None) -> None`
    - 绑定待分析图像，支持内存对象或文件路径。

  - `analyze() -> IlluminationUniformityResult`
    - 计算灰度图的 mean / std：
      - 若 `mean == 0` 且 `std > 0`，则返回 `uniformity = inf`；
      - 若 `mean == 0` 且 `std == 0`，则返回 `uniformity = 0`；
      - 否则返回 `uniformity = std / mean`。

  - `result: Optional[IlluminationUniformityResult]`

## 使用建议

- 可用于：
  - 监测灯光系统是否稳定；
  - 判断是否出现明显的热点、阴影或梯度光照；
  - 与曝光和清晰度指标结合，用于综合评价图像质量。

- 注意：
  - 对于非常暗的图像，均值可能接近 0，此时指标可能变得不稳定，应结合曝光指标一起分析。
