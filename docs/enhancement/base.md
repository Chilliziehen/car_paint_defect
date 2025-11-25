# JPG 图像增强器基类（抽象接口）

该文档简要说明在 `src/main/enhancement.py` 中定义的 JPG 图像增强器抽象接口及其使用方式。

## 设计目标

- 面向 **JPG 车漆缺陷图像** 的通用增强接口。
- 可以 **绑定一张待处理的图像**（内存对象或文件路径）。
- 通过 **统一的配置对象** 和 **属性 getter/setter** 访问、设置所有增强算法可能共享的参数。
- 为具体增强算法（如去噪、对比度增强、伽马校正等）提供清晰的基类约定。

## 核心类型

### `EnhancementConfig`

一个数据类，描述所有增强器都可能共用的配置参数：

- `input_size: Optional[Tuple[int, int]]`
  - 期望的输入图像尺寸 `(width, height)`，`None` 表示保持原尺寸。
- `normalize: bool`
  - 是否对像素值做归一化（例如缩放到 `[0, 1]`）。
- `color_space: str`
  - 图像处理时使用的颜色空间，例如 `"RGB"` 或 `"BGR"`。
- `clip_range: Optional[Tuple[float, float]]`
  - 在增强完成后对像素值进行裁剪的范围 `(min, max)`，`None` 表示不裁剪。
- `metadata: Dict[str, Any]`
  - 预留的扩展字段，用于存放具体算法的额外公共参数（例如噪声强度、对比度系数等），但又希望能被结构化地追踪。

### `BaseImageEnhancer`

`BaseImageEnhancer` 是所有 JPG 图像增强器的**抽象基类**，主要职责：

1. 提供 **图像绑定接口**：
   - `bind_image(image: Optional[ImageLike] = None, *, path: Optional[Union[str, Path]] = None) -> None`
   - `image`：已经加载在内存中的图像对象（如 `numpy.ndarray` 或 `PIL.Image.Image`）。
   - `path`：JPG 图像的文件路径。
   - `image` 和 `path` 至少需要提供一个。

2. 提供 **共享配置的统一访问入口**：
   - `config: EnhancementConfig`：完整配置对象。
   - `input_size` / `normalize` / `color_space` / `clip_range` / `metadata`：
     通过 Python 属性的 getter/setter 访问，对所有增强器保持一致的参数命名和类型约定。

3. 定义 **核心抽象方法**：
   - `enhance() -> ImageLike`
     - 执行具体的增强算法，返回增强后的图像对象。
     - 具体返回类型由子类决定（通常是 `numpy.ndarray` 或 `PIL.Image.Image`），并在子类中注明。

4. 生命周期辅助方法：
   - `reset() -> None`
     - 重置当前绑定的图像和内部状态，但保留当前的配置对象，可由子类重写以清理缓存等。

## 典型使用流程

1. 创建一个具体的增强器子类（例如 `ContrastEnhancer`），继承自 `BaseImageEnhancer` 并实现 `enhance()`：
   - 在子类中只关注具体算法逻辑。
   - 通过 `self.config` 或属性（如 `self.input_size`）读取/修改通用参数。

2. 在业务代码中使用：

   1. 实例化增强器，并视需要传入 `EnhancementConfig`：
      - 不传入时会使用默认配置。
   2. 通过 `bind_image(...)` 绑定一张待增强的图像（路径或内存对象）。
   3. 根据需要通过属性或 `set_config(...)` 调整共享参数。
   4. 调用 `enhance()` 获得增强后的图像结果。

## 子类实现建议

- 在实现 `enhance()` 时，可以：
  - 使用 `self.image` 获取当前绑定的图像；
  - 根据 `self.input_size` 决定是否缩放图像；
  - 根据 `self.normalize` / `self.clip_range` 控制归一化与值裁剪；
  - 在 `self.metadata` 中约定并读取特定算法需要的共用参数（例如 `gamma`、`alpha` 等）。
- 如需延迟加载文件：
  - 可以在子类中重写 `image` 属性，当 `self._image` 为空但 `self._image_path` 有值时，再进行磁盘读取并缓存。

通过该基类，项目中所有针对车漆缺陷 JPG 图像的增强算法都可以在统一接口下实现和调用，便于后续在训练/推理管线中进行组合和替换。
