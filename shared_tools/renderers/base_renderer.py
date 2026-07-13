import abc

class BaseRenderer(abc.ABC):
    """
    Abstract base class for all video production renderers.
    """
    @abc.abstractmethod
    def generate_image(self, prompt: str, output_path: str, config: dict, size: str = "1024x768") -> str:
        """
        Generates a static image and saves it to output_path.
        Returns the image URL/ID if needed for the next step.
        """
        pass

    @abc.abstractmethod
    def generate_video(self, source_image: str, prompt: str, output_path: str, config: dict) -> bool:
        """
        Generates a video from the source image and prompt.
        Saves it to output_path. Returns True on success.
        """
        pass
