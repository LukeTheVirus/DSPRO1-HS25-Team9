from markitdown import MarkItDown
from pathlib import Path
from preprocessing_scripts.pdf_to_md_converter import write_markdown_file


def mark_any_down(file_path: Path, output_dir: Path):
    md = MarkItDown()
    md_file_name = file_path.stem + ".md"
    md_path = output_dir / md_file_name

    try:
        # Convert the Path object to a string for compatibility
        temp = md.convert(str(file_path))
        write_markdown_file(md_path, temp.text_content)
        print(f"Successfully converted: {file_path.name} -> {md_file_name}")
    except Exception as e:
        print(f"Error converting {file_path.name}: {str(e)}")


if __name__ == '__main__':
    sample_file = Path("../Docs/sample-1.pptx")
    output_dir = Path("../src/md_versions")
    mark_any_down(sample_file, output_dir)
