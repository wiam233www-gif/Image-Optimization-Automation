from pathlib import Path
from PIL import Image, ImageOps
import re

# Project folders
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input_images"
OUTPUT_DIR = BASE_DIR / "output_images"
NAMES_FILE = BASE_DIR / "names.txt"

SUPPORTED_FORMATS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}


def safe_folder_name(name):
    """Clean folder or file names."""
    name = re.sub(r'[<>:"|?*]', "_", name)
    return name.strip(" .")


def unique_path(path):
    """Avoid overwriting existing files."""
    original = path
    counter = 1

    while path.exists():
        path = original.with_name(
            f"{original.stem}_{counter}{original.suffix}"
        )
        counter += 1

    return path


def process_images(
    names_file,
    input_dir,
    output_dir,
    target_size=None,
    quality=85,
    convert_to_webp=False
):
    names_file = Path(names_file)
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not names_file.is_file():
        print("Error: names.txt file was not found.")
        return False

    if not input_dir.is_dir():
        print("Error: input_images folder was not found.")
        return False

    if not 1 <= quality <= 100:
        print("Error: quality must be between 1 and 100.")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    with names_file.open("r", encoding="utf-8") as file:
        names = [line.strip() for line in file if line.strip()]

    images = sorted(
        [
            file for file in input_dir.iterdir()
            if file.is_file()
            and file.suffix.lower() in SUPPORTED_FORMATS
        ],
        key=lambda x: x.name.lower()
    )

    if len(images) != len(names):
        print("Error: Number of names does not match images.")
        print(f"Images: {len(images)} | Names: {len(names)}")
        return False

    successful = 0
    failed = 0

    for image_path, new_name in zip(images, names):

        try:
            # Allow optional subfolders in names.txt
            clean_name = new_name.replace("\\", "/")
            parts = clean_name.split("/")

            if any(part in ("", ".", "..") for part in parts):
                raise ValueError("Invalid folder or file name.")

            parts = [safe_folder_name(part) for part in parts]

            if any(not part for part in parts):
                raise ValueError("Empty or invalid file name.")

            filename = parts[-1]

            # Remove a supplied image extension, if present
            for ext in SUPPORTED_FORMATS:
                if filename.lower().endswith(ext):
                    filename = filename[:-len(ext)]
                    break

            if not filename:
                raise ValueError("Invalid output filename.")

            destination_folder = output_dir.joinpath(*parts[:-1])
            destination_folder.mkdir(parents=True, exist_ok=True)

            if convert_to_webp:
                extension = ".webp"
            else:
                extension = image_path.suffix.lower()

            output_path = unique_path(
                destination_folder / f"{filename}{extension}"
            )

            with Image.open(image_path) as img:
                # Work with the first frame of static images
                img = ImageOps.exif_transpose(img)
                img.load()

                # Preserve aspect ratio when resizing
                if target_size:
                    img.thumbnail(
                        target_size,
                        Image.Resampling.LANCZOS
                    )

                # JPEG does not support transparency
                if extension in (".jpg", ".jpeg"):
                    if img.mode not in ("RGB", "L"):
                        img = img.convert("RGB")

                elif extension in (".png", ".webp"):
                    if img.mode not in ("RGB", "RGBA", "L", "LA"):
                        img = img.convert("RGBA")

                save_options = {"optimize": True}

                if extension in (".jpg", ".jpeg", ".webp"):
                    save_options["quality"] = quality

                if extension == ".png":
                    save_options["compress_level"] = 9

                img.save(output_path, **save_options)

            successful += 1
            print(f"Done: {image_path.name} -> {output_path.name}")

        except Exception as error:
            failed += 1
            print(f"Failed: {image_path.name}: {error}")

    print("\nProcessing finished.")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    return failed == 0


if __name__ == "__main__":

    process_images(
        names_file=NAMES_FILE,
        input_dir=INPUT_DIR,
        output_dir=OUTPUT_DIR,
        target_size=(1000, 1000),
        quality=80,
        convert_to_webp=False
    )

