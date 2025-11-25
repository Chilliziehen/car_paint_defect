"""Image enhancement interfaces for car paint defect images."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

# Type alias for image-like objects we might support
ImageLike = Union[np.ndarray, "PIL.Image.Image"]


@dataclass
class EnhancementConfig:
    """Common configuration parameters shared by image enhancement techniques.

    Attributes
    ----------
    input_size:
        Expected width and height (W, H) of the input image after optional
        resizing. ``None`` means keep the original size.
    normalize:
        Whether to normalize image pixel values (e.g. to [0, 1]).
    color_space:
        Color space used during processing, such as ``"RGB"`` or ``"BGR"``.
    clip_range:
        Optional value range ``(min, max)`` to clip pixel intensities after
        enhancement.
    metadata:
        A free-form dictionary for additional algorithm-specific parameters
        that should still be tracked in a structured way.
    """

    input_size: Optional[Tuple[int, int]] = None
    normalize: bool = True
    color_space: str = "RGB"
    clip_range: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseImageEnhancer(ABC):
    """Abstract base class for JPG image enhancers.

    The enhancer follows a simple lifecycle:

    1. Bind an image via :meth:`bind_image`.
    2. Optionally update shared parameters via :meth:`set_config` or the
       individual property setters.
    3. Call :meth:`enhance` to obtain the processed image.

    Implementations should focus on car‑paint defect images but remain
    generic enough to be reusable for other JPG inputs.
    """

    def __init__(self, config: Optional[EnhancementConfig] = None) -> None:
        self._config: EnhancementConfig = config or EnhancementConfig()
        self._image: Optional[ImageLike] = None
        self._image_path: Optional[Path] = None

    # ------------------------------------------------------------------
    # Image binding
    # ------------------------------------------------------------------
    def bind_image(self, image: Optional[ImageLike] = None, *, path: Optional[Union[str, Path]] = None) -> None:
        """Bind a JPG image to this enhancer.

        Parameters
        ----------
        image:
            Image object already loaded in memory (e.g. ``numpy.ndarray`` or
            ``PIL.Image.Image``). If provided, ``path`` is optional.
        path:
            Filesystem path to a JPG image. Implementations may lazily load
            the image on first access.

        At least one of ``image`` or ``path`` must be provided.
        """

        if image is None and path is None:
            raise ValueError("Either 'image' or 'path' must be provided to bind_image().")

        self._image = image
        self._image_path = Path(path) if path is not None else None

    @property
    def image(self) -> Optional[ImageLike]:
        """Return the currently bound image object, if any.

        Concrete subclasses may override this to apply lazy loading when an
        image path is available but the in-memory image is not yet loaded.
        """

        return self._image

    @property
    def image_path(self) -> Optional[Path]:
        """Path of the currently bound image, if bound via path."""

        return self._image_path

    # ------------------------------------------------------------------
    # Shared configuration (getters / setters)
    # ------------------------------------------------------------------
    @property
    def config(self) -> EnhancementConfig:
        """Full configuration object used by the enhancer."""

        return self._config

    def set_config(self, config: EnhancementConfig) -> None:
        """Replace the entire configuration with a new one."""

        self._config = config

    @property
    def input_size(self) -> Optional[Tuple[int, int]]:
        return self._config.input_size

    @input_size.setter
    def input_size(self, value: Optional[Tuple[int, int]]) -> None:
        self._config.input_size = value

    @property
    def normalize(self) -> bool:
        return self._config.normalize

    @normalize.setter
    def normalize(self, value: bool) -> None:
        self._config.normalize = bool(value)

    @property
    def color_space(self) -> str:
        return self._config.color_space

    @color_space.setter
    def color_space(self, value: str) -> None:
        self._config.color_space = str(value)

    @property
    def clip_range(self) -> Optional[Tuple[float, float]]:
        return self._config.clip_range

    @clip_range.setter
    def clip_range(self, value: Optional[Tuple[float, float]]) -> None:
        self._config.clip_range = value

    @property
    def metadata(self) -> Dict[str, Any]:
        """Free-form dictionary for algorithm-specific shared parameters."""

        return self._config.metadata

    # ------------------------------------------------------------------
    # Core behaviour
    # ------------------------------------------------------------------
    @abstractmethod
    def enhance(self) -> ImageLike:
        """Run the enhancement algorithm on the currently bound image.

        Returns
        -------
        ImageLike
            The enhanced image. The concrete type is implementation specific
            but should be documented by subclasses.
        """

        raise NotImplementedError

    def reset(self) -> None:
        """Reset internal state while keeping the current configuration.

        Subclasses may override to clear caches or intermediate results.
        """

        self._image = None
        self._image_path = None

