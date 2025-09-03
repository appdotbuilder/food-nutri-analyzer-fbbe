import pytest
from pathlib import Path
from PIL import Image
from io import BytesIO
from app.services.file_service import FileService


@pytest.fixture
def file_service():
    return FileService()


@pytest.fixture
def sample_image_bytes():
    """Create a sample JPEG image as bytes."""
    img = Image.new("RGB", (100, 100), color="red")
    byte_arr = BytesIO()
    img.save(byte_arr, format="JPEG")
    return byte_arr.getvalue()


@pytest.fixture
def large_image_bytes():
    """Create a large image that should be resized."""
    img = Image.new("RGB", (3000, 2000), color="blue")
    byte_arr = BytesIO()
    img.save(byte_arr, format="JPEG")
    return byte_arr.getvalue()


def test_validate_image_file_valid(file_service, sample_image_bytes):
    """Test validation of valid image file."""
    assert file_service.validate_image_file(sample_image_bytes, "test.jpg")
    assert file_service.validate_image_file(sample_image_bytes, "test.jpeg")
    assert file_service.validate_image_file(sample_image_bytes, "test.png")


def test_validate_image_file_invalid_extension(file_service, sample_image_bytes):
    """Test validation rejects invalid extensions."""
    assert not file_service.validate_image_file(sample_image_bytes, "test.txt")
    assert not file_service.validate_image_file(sample_image_bytes, "test.pdf")
    assert not file_service.validate_image_file(sample_image_bytes, "test.doc")


def test_validate_image_file_too_large(file_service):
    """Test validation rejects files that are too large."""
    # Create content larger than max size
    large_content = b"x" * (file_service.MAX_FILE_SIZE + 1)
    assert not file_service.validate_image_file(large_content, "test.jpg")


def test_validate_image_file_corrupted_data(file_service):
    """Test validation rejects corrupted image data."""
    corrupted_data = b"not an image"
    assert not file_service.validate_image_file(corrupted_data, "test.jpg")


def test_save_image_success(file_service, sample_image_bytes):
    """Test successful image saving."""
    filename, file_path, file_size, width, height = file_service.save_image(sample_image_bytes, "original.jpg")

    # Check return values
    assert filename.endswith(".jpg")
    assert len(filename) == 36  # UUID hex + extension
    assert Path(file_path).exists()
    assert file_size > 0
    assert width == 100
    assert height == 100

    # Cleanup
    Path(file_path).unlink()


def test_save_image_resizes_large_images(file_service, large_image_bytes):
    """Test that large images are resized."""
    filename, file_path, file_size, width, height = file_service.save_image(large_image_bytes, "large.jpg")

    # Should be resized to fit within max dimensions
    assert width <= file_service.MAX_IMAGE_SIZE[0]
    assert height <= file_service.MAX_IMAGE_SIZE[1]
    assert Path(file_path).exists()

    # Cleanup
    Path(file_path).unlink()


def test_save_image_converts_rgba(file_service):
    """Test that RGBA images are converted to RGB."""
    # Create PNG with transparency
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    byte_arr = BytesIO()
    img.save(byte_arr, format="PNG")
    png_bytes = byte_arr.getvalue()

    filename, file_path, file_size, width, height = file_service.save_image(png_bytes, "transparent.png")

    # Verify the saved image
    saved_img = Image.open(file_path)
    assert saved_img.mode == "RGB"

    # Cleanup
    Path(file_path).unlink()


def test_delete_image_success(file_service, sample_image_bytes):
    """Test successful image deletion."""
    filename, file_path, _, _, _ = file_service.save_image(sample_image_bytes, "delete_test.jpg")

    # Verify file exists
    assert Path(file_path).exists()

    # Delete file
    assert file_service.delete_image(file_path)

    # Verify file is deleted
    assert not Path(file_path).exists()


def test_delete_image_nonexistent(file_service):
    """Test deletion of nonexistent file."""
    assert file_service.delete_image("/nonexistent/path/file.jpg")


def test_get_image_path_exists(file_service, sample_image_bytes):
    """Test getting path of existing image."""
    filename, file_path, _, _, _ = file_service.save_image(sample_image_bytes, "path_test.jpg")

    retrieved_path = file_service.get_image_path(filename)
    assert retrieved_path == file_path
    assert Path(retrieved_path).exists()

    # Cleanup
    Path(file_path).unlink()


def test_get_image_path_nonexistent(file_service):
    """Test getting path of nonexistent image."""
    path = file_service.get_image_path("nonexistent.jpg")
    assert path is None


def test_upload_directory_creation():
    """Test that upload directory is created if it doesn't exist."""
    file_service = FileService()

    # Directory should be created during initialization
    assert file_service.UPLOAD_DIR.exists()
    assert file_service.UPLOAD_DIR.is_dir()
