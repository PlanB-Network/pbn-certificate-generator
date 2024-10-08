import hashlib
import os
import re
import subprocess
from typing import Optional


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


def modify_and_save_tex(template_path, new_tex_path, fullname, completion_date, hash_value_1, hash_value_2, txid_1, txid_2):
    """Modifies the LaTeX template and saves it to a new .tex file."""
    with open(template_path, "r") as file:
        content = file.read()
    content = content.replace("{fullname}", fullname)
    content = content.replace("{completion_date}", completion_date)
    content = content.replace("{certificate-part1}", hash_value_1)
    content = content.replace("{certificate-part2}", hash_value_2)
    content = content.replace("{timestamp-part1}", txid_1)
    content = content.replace("{timestamp-part2}", txid_2)
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



def process_files(template_path, directory):
    """Processes each matching .txt file in the directory."""
    for filename in os.listdir(directory):
        if filename.startswith("PlanB-BizSchool-diploma") and filename.endswith(
            "-signed.txt"
        ):
            print(filename)
            pathfile = os.path.join(directory, filename)
            ots_file_path = f"{pathfile}.ots"
            fullname = extract_fullname(pathfile)
            hash_1, hash_2 = split_and_format_hash(compute_sha256(pathfile))
            txid_1, txid_2 = split_and_format_hash(get_ots_blockhash(ots_file_path))

            if fullname:
                new_tex_name = filename.replace(".txt", ".tex")
                modify_and_save_tex(
                    template_path,
                    os.path.join(directory, new_tex_name),
                    fullname,
                    hash_1,
                    hash_2,
                    txid_1,
                    txid_2,
                )
                print(f"Generated .tex file for: {filename}")


template_path = "./planb-bizschool-template.tex"
directory_path = "./"  # Adjust to your directory as needed
process_files(template_path, directory_path)

if __name__ == "__main__":
    pending_path = "../pending"
    filenames = sorted(os.listdir(pending_path))
    for filename in filenames:
        if filename.startswith("course_") and filename.endswith(".ots"):
            pathfile = os.path.join(pending_path, filename)
            if is_ots_done(pathfile):
                txid_1, txid_2 = split_and_format_hash(get_ots_blockhash(ots_file_path))
                signed_txt_path = pathfile.removesuffix(".ots")
                fullname = extract_property(signed_txt_path, "fullname")
                #TODO: write for the other properties needed in the pdf file
                hash_1, hash_2 = split_and_format_hash(compute_sha256(pathfile))




            

