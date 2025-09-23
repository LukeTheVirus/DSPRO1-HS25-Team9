import logging
from pathlib import Path
import argparse
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def html_table_to_markdown(html: str) -> str:
    """
    Convert an HTML table to Markdown format.
    Extracts rows and cells with BeautifulSoup and builds a Markdown table.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return html  # Return original HTML if no table found

    rows = table.find_all("tr")
    markdown_lines = []
    for i, row in enumerate(rows):
        cells = row.find_all(["th", "td"])
        cell_texts = [cell.get_text(strip=True) for cell in cells if cell.get_text(strip=True)]
        if not cell_texts:
            continue
        row_md = "| " + " | ".join(cell_texts) + " |"
        markdown_lines.append(row_md)
        if i == 0:  # Add divider after header row
            divider = "| " + " | ".join(["---"] * len(cell_texts)) + " |"
            markdown_lines.append(divider)
    return "\n".join(markdown_lines)

def convert_file_to_markdown(input_file: Path, output_file: Path) -> None:
    """
    Convert a single file (pdf, docx, html, txt, pptx, etc.) to Markdown.
    Uses the unstructured.partition module to process the file content.
    """
    try:
        logging.info(f"Processing file: {input_file}")
        extension = input_file.suffix.lower()

        # Dynamically select partition function based on file extension
        if extension == ".pdf":
            from unstructured.partition.pdf import partition_pdf
            elements = partition_pdf(
                filename=str(input_file),
                infer_table_structure=True,
                strategy="hi_res"
            )
        elif extension == ".docx":
            from unstructured.partition.docx import partition_docx
            elements = partition_docx(filename=str(input_file))
        elif extension in [".html", ".htm"]:
            from unstructured.partition.html import partition_html
            elements = partition_html(filename=str(input_file))
        elif extension == ".txt":
            from unstructured.partition.text import partition_text
            elements = partition_text(filename=str(input_file))
        elif extension == ".pptx":
            from unstructured.partition.pptx import partition_pptx
            elements = partition_pptx(filename=str(input_file))
        else:
            from unstructured.partition.auto import partition
            elements = partition(filename=str(input_file))

        markdown_content = []
        for elem in elements:
            if elem.category == "Table":
                if hasattr(elem, "metadata") and hasattr(elem.metadata, "text_as_html") and elem.metadata.text_as_html:
                    md_table = html_table_to_markdown(elem.metadata.text_as_html)
                    markdown_content.append(md_table)
                else:
                    markdown_content.append(elem.text)
            else:
                if hasattr(elem, "to_markdown"):
                    markdown_content.append(elem.to_markdown())
                else:
                    markdown_content.append(elem.text)

        final_markdown = "\n\n".join(markdown_content)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(final_markdown, encoding="utf-8")
        logging.info(f"Saved converted Markdown to: {output_file}")
    except Exception as e:
        logging.error(f"Error processing {input_file}: {e}")

def convert_folder(input_folder: Path, output_folder: Path,
                   supported_extensions=(".pdf", ".docx", ".html", ".htm", ".txt", ".pptx")) -> None:
    """
    Convert all files with supported extensions in the input_folder to Markdown,
    saving the results in output_folder.
    """
    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    for input_file in input_folder.glob("*"):
        if input_file.suffix.lower() in supported_extensions:
            output_file = output_folder / (input_file.stem + ".md")
            convert_file_to_markdown(input_file, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert files to Markdown format.")
    parser.add_argument("input", type=str, help="Input file or folder path")
    parser.add_argument("output", type=str, help="Output file or folder path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_dir():
        convert_folder(input_path, output_path)
    else:
        convert_file_to_markdown(input_path, output_path)
