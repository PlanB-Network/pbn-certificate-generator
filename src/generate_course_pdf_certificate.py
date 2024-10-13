import hashlib
import os
import re
import subprocess
import shutil
from datetime import datetime
from typing import Optional, Dict


def is_ots_done(ots_file_path: str) -> bool:
    """Checks if the block hash can be extracted from the .ots file."""
    try:
        upgrade_command = f"ots --bitcoin-node http://asi0:asi0@127.0.0.1:8332/ upgrade {ots_file_path}"
        subprocess.run(
            upgrade_command, shell=True, check=True, text=True, capture_output=True
        )
        verify_command = f"ots --bitcoin-node http://asi0:asi0@127.0.0.1:8332/ verify {ots_file_path}"
        verify_result = subprocess.run(
            verify_command, shell=True, check=True, text=True, capture_output=True
        )
        print(verify_result)
        block_height = re.search(r"Bitcoin block (\d+)", verify_result.stderr)
        return block_height is not None
    except subprocess.CalledProcessError as e:
        print(f"Failed to process: {e}")
        return False

def get_ots_blockhash(ots_file_path: str) -> str:
    """Extracts the block hash from the .ots file verification process."""
    try:
        upgrade_command = f"ots --bitcoin-node http://asi0:asi0@127.0.0.1:8332/ upgrade {ots_file_path}"
        subprocess.run(
            upgrade_command, shell=True, check=True, text=True, capture_output=True
        )
        verify_command = f"ots --bitcoin-node http://asi0:asi0@127.0.0.1:8332/ verify {ots_file_path}"
        verify_result = subprocess.run(
            verify_command, shell=True, check=True, text=True, capture_output=True
        )
        print(verify_result)
        block_height = re.search(r"Bitcoin block (\d+)", verify_result.stderr).group(1)
        print(block_height)
        header_command = (
            f"curl -sSL 'https://mempool.space/api/block-height/{block_height}'"
        )
        header_result = subprocess.run(
            header_command, shell=True, check=True, text=True, capture_output=True
        )
        return header_result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Failed to process: {e}"
    except AttributeError:
        return "Block height not found in OTS verification output"


def compute_sha256(file_path):
    """Compute the SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def extract_property(txt_file: str, property_name: str) -> Optional[str]:
    """
    Extract a property value from a text file given the property name.
    
    Args:
        txt_file: Path to the text file.
        property_name: Name of the property to extract.
    
    Returns:
        The extracted property value, or None if not found.
    """
    with open(txt_file, "r") as file:
        content = file.read()
    
    pattern = rf"{re.escape(property_name)}:?\s*(.+)"
    match = re.search(pattern, content, re.IGNORECASE)
    
    return match.group(1).strip() if match else None

def modify_and_save_tex(template_path: str, new_tex_path: str, certificate_data: Dict[str, str]) -> None:
    """
    Modifies a LaTeX template with certificate data and saves the result.

    Args:
        template_path: Path to the LaTeX template file.
        new_tex_path: Path to save the modified LaTeX file.
        certificate_data: Dictionary of placeholders and their replacements.

    Replaces {key} placeholders in the template with corresponding values from certificate_data.
    """
    with open(template_path, "r") as file:
        content = file.read()
    
    for key, value in certificate_data.items():
        placeholder = f"{{{key}}}"
        content = content.replace(placeholder, str(value))
    
    with open(new_tex_path, "w") as file:
        file.write(content)

def format_hash(hash_value):
    """Formats the hash value to have a space after every four characters."""
    chunks = [hash_value[i : i + 4] for i in range(0, len(hash_value), 4)]
    formatted_hash = " ".join(chunks)
    return formatted_hash

def split_and_format_hash(hash):
    midpoint = len(hash) // 2
    
    first_half = hash[:midpoint]
    second_half = hash[midpoint:]
    
    return format_hash(first_half), format_hash(second_half)

def compile_tex_to_pdf(tex_filepath: str) -> bool:
    """
    Compiles a .tex file to PDF using lualatex twice and cleans up auxiliary files.
    Args:
        tex_filepath: Path to the .tex file to be compiled.
    Returns:
        bool: True if compilation succeeded, False otherwise.
    """
    folder_path = os.path.dirname(tex_filepath)
    file_name = os.path.splitext(os.path.basename(tex_filepath))[0]
    
    try:
        for _ in range(2):  
            result = subprocess.run(
                ['lualatex', '-interaction=nonstopmode', tex_filepath],
                cwd=folder_path,
                capture_output=True,
                text=True,
                check=True 
            )
        pdf_path = os.path.join(folder_path, f"{file_name}.pdf")
        if os.path.exists(pdf_path):
            for ext in ['.log', '.aux', '.out', '.tex']:
                aux_file = os.path.join(folder_path, f"{file_name}{ext}")
                if os.path.exists(aux_file):
                    os.remove(aux_file)
            return True
        print(f"PDF not produced after two passes.")
        return False
    
    except subprocess.CalledProcessError as e:
        print(f"Error running lualatex: {e}")
        return False

def move_files_to_final(pathfile: str, signed_txt_path: str, pdf_path: str) -> bool:
    """
    Moves specified files to a '../final' folder.

    Args:
        pathfile: Path to the .ots file.
        signed_txt_path: Path to the signed text file.
        pdf_path: Path to the PDF file.

    Returns:
        bool: True if all files were moved successfully, False otherwise.
    """
    current_dir = os.path.dirname(pathfile)
    final_dir = os.path.join(os.path.dirname(current_dir), 'final')

    os.makedirs(final_dir, exist_ok=True)

    files_to_move = [pathfile, signed_txt_path, pdf_path]
    
    try:
        for file_path in files_to_move:
            if os.path.exists(file_path):
                shutil.move(file_path, os.path.join(final_dir, os.path.basename(file_path)))
            else:
                print(f"Warning: File not found: {file_path}")
        return True
    except Exception as e:
        print(f"Error moving files: {e}")
        return False

def format_date(date_string: str) -> str:
    """
    Convert date from YYYY-MM-DD format to Dth Month, YYYY format without leading zero.
    
    Args:
        date_string: A string representing a date in YYYY-MM-DD format.
    
    Returns:
        A string representing the date in Dth Month, YYYY format.
    """
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    
    day = date_obj.day
    
    suffix = "th" if 4 <= day <= 20 or 24 <= day <= 30 else ["st", "nd", "rd"][day % 10 - 1]
    
    return f"{day}{suffix} {date_obj.strftime('%B, %Y')}"

def split_and_format_coursename(coursename: str) -> tuple[str, str]:
    """
    Split a coursename into two halves based on word count.
    
    If the word count is odd, the first half will be smaller.
    
    Args:
        coursename: A string representing the full course name.
    
    Returns:
        A tuple containing two strings: (first_half, second_half).
    """
    words = coursename.split()
    mid = len(words) // 2
    
    first_half = " ".join(words[:mid])
    second_half = " ".join(words[mid:])
    
    return first_half, second_half

if __name__ == "__main__":
    pending_path = "../pending"
    filenames = sorted(os.listdir(pending_path))
    for filename in filenames:
        if filename.startswith("course_") and filename.endswith(".ots"):
            pathfile = os.path.join(pending_path, filename)
            print(pathfile)
            if is_ots_done(pathfile):
                signed_txt_path = pathfile.removesuffix(".ots")

                txid_1, txid_2 = split_and_format_hash(get_ots_blockhash(pathfile))
                hash_1, hash_2 = split_and_format_hash(compute_sha256(signed_txt_path))

                course_name_1, course_name_2 = split_and_format_coursename(extract_property(signed_txt_path, "Course name"))

                certificate_data = {
                    "fullname": extract_property(signed_txt_path, "Full name"),
                    "date": format_date(extract_property(signed_txt_path, "Date of completion")),
                    "course_id": extract_property(signed_txt_path, "Course ID"),
                    "course_name_1": course_name_1,
                    "course_name_2": course_name_2,
                    "duration": extract_property(signed_txt_path, "Duration"),
                    "hash_1": hash_1,
                    "hash_2": hash_2,
                    "txid_1": txid_1,
                    "txid_2": txid_2,
                }
                print(certificate_data)

                tex_filepath = signed_txt_path.replace('.txt', '.tex')
                tex_template_path = '../templates/pbn_course_certificate.tex'
                pdf_filepath = signed_txt_path.replace('.txt', '.pdf')

                modify_and_save_tex(tex_template_path, tex_filepath, certificate_data)
                print(f"{filename} tex file replaced")
                compile_tex_to_pdf(tex_filepath)
                print(f"{filename} pdf file produced")
                move_files_to_final(pathfile, signed_txt_path, pdf_filepath)
                print(f"{filename} files moved")
