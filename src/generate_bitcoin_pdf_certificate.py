import hashlib
import os
import re
import subprocess
import shutil
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv
from pathlib import Path

parent_dir = Path(__file__).parent.parent
env_path = parent_dir / '.env'
load_dotenv(dotenv_path=env_path)

RPC_USER = os.getenv('RPC_USER')
RPC_PASSWORD = os.getenv('RPC_PASSWORD')


def is_ots_done(ots_file_path: str) -> bool:
    """Checks if the block hash can be extracted from the .ots file."""
    try:
        upgrade_command = f"ots --bitcoin-node http://{RPC_USER}:{RPC_PASSWORD}@127.0.0.1:8332/ upgrade {ots_file_path}"
        subprocess.run(
            upgrade_command, shell=True, check=True, text=True, capture_output=True
        )
        verify_command = f"ots --bitcoin-node http://{RPC_USER}:{RPC_PASSWORD}@127.0.0.1:8332/ verify {ots_file_path}"
        verify_result = subprocess.run(
            verify_command, shell=True, check=True, text=True, capture_output=True
        )
        block_height = re.search(r"Bitcoin block (\d+)", verify_result.stderr)
        return block_height is not None
    except subprocess.CalledProcessError as e:
        print(f"Failed to process: {e}")
        return False

def get_ots_blockhash(ots_file_path: str) -> str:
    """Extracts the block hash from the .ots file verification process."""
    try:
        upgrade_command = f"ots --bitcoin-node http://{RPC_USER}:{RPC_PASSWORD}@127.0.0.1:8332/ upgrade {ots_file_path}"
        subprocess.run(
            upgrade_command, shell=True, check=True, text=True, capture_output=True
        )
        verify_command = f"ots --bitcoin-node http://{RPC_USER}:{RPC_PASSWORD}@127.0.0.1:8332/ verify {ots_file_path}"
        verify_result = subprocess.run(
            verify_command, shell=True, check=True, text=True, capture_output=True
        )
        block_height = re.search(r"Bitcoin block (\d+)", verify_result.stderr).group(1)
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
    Compiles a .tex file to PDF using lualatex twice. If successful, returns True.
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
            return True
        print(f"PDF not produced after two passes.")
        return False
    
    except subprocess.CalledProcessError as e:
        print(f"Error running lualatex: {e}")
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

def clean_bak_files(folder_path: str) -> None:
    """
    Remove all .bak files in the specified folder.
    
    Args:
        folder_path: Path to the folder to clean
    """
    for file in os.listdir(folder_path):
        if file.endswith('.bak'):
            file_path = os.path.join(folder_path, file)
            try:
                os.remove(file_path)
                print(f"Removed backup file: {file}")
            except OSError as e:
                print(f"Error removing {file}: {e}")

if __name__ == "__main__":
    bcert_path = "../../planB-premium-content/bcert/editions/"
    for edition_folder in sorted(os.listdir(bcert_path)):
        edition_path = os.path.join(bcert_path, edition_folder)
        if os.path.isdir(edition_path):
            print(f"\nProcessing edition: {edition_folder}")
            result_folder = os.path.join(edition_path, "results")
            if os.path.exists(result_folder):
                subfolders = [f for f in os.listdir(result_folder) if os.path.isdir(os.path.join(result_folder, f))]
                subfolders = sorted(subfolders)
                for subfolder in sorted(subfolders):
                    result_folder_path = os.path.join(result_folder, subfolder)
                    ots_file = os.path.join(result_folder_path, "bitcoin_certificate-signed.txt.ots")
                    pdf_file = os.path.join(result_folder_path, "bitcoin_certificate-signed.pdf")
                    if os.path.exists(ots_file) and not os.path.exists(pdf_file):
                        print(f"Processing {subfolder}..")
                        if is_ots_done(ots_file):
                            signed_txt_path = ots_file.removesuffix(".ots")
                            txid_1, txid_2 = split_and_format_hash(get_ots_blockhash(ots_file))
                            hash_1, hash_2 = split_and_format_hash(compute_sha256(signed_txt_path))

                            certificate_data = {
                                "fullname": extract_property(signed_txt_path, "Display name"),
                                "date": format_date(extract_property(signed_txt_path, "Date of completion")),
                                "hash1": hash_1,
                                "hash2": hash_2,
                                "txid1": txid_1,
                                "txid2": txid_2,
                            }

                            pending_folder = "../pending"
                            tex_template_path = '../templates/pbn_bitcoin_certificate.tex'
                            temp_tex_path = os.path.join(pending_folder, "bitcoin_certificate-signed.tex")
                            temp_pdf_path = os.path.join(pending_folder, "bitcoin_certificate-signed.pdf")
                            
                            modify_and_save_tex(tex_template_path, temp_tex_path, certificate_data)
                            compile_tex_to_pdf(temp_tex_path)
                            if os.path.exists(temp_pdf_path):
                                target_pdf_path = os.path.join(result_folder_path, "bitcoin_certificate-signed.pdf")
                                shutil.move(temp_pdf_path, target_pdf_path)
                                print(f"PDF Certificate generated and moved to target folder")
                                # Clean .bak files in the processed subfolder
                                clean_bak_files(result_folder_path)
                            else:
                                print(f"Failed to generate PDF certificate")
                        else:
                            print("Timestamp not ready yet..")
                        print()
            print("==============")
    print("All pending Certificates that were timestamped were generated!")
