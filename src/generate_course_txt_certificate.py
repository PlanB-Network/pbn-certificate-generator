import os
import csv
import requests
import yaml
from datetime import date
import subprocess

def get_course_input(file_path: str) -> tuple[str, str, str]:
    """Reads the CSV file and extracts the username, fullname, and course ID from the first row."""
    with open(file_path, "r") as file:
        csv_reader = csv.reader(file, delimiter=",")
        first_row = next(csv_reader)
    
    username = first_row[0]
    fullname = first_row[1]
    course_id = first_row[2]
    
    return username, fullname, course_id

def get_latest_block_header() -> str:
    """Fetches the latest block header from the mempool.space API using curl."""
    try:
        height_command = "curl -sSL 'https://mempool.space/api/blocks/tip/height'"
        height_result = subprocess.run(
            height_command, shell=True, check=True, text=True, capture_output=True
        )
        current_height = height_result.stdout.strip()
        print(current_height)

        header_command = (
            f"curl -sSL 'https://mempool.space/api/block-height/{current_height}'"
        )
        header_result = subprocess.run(
            header_command, shell=True, check=True, text=True, capture_output=True
        )
        current_header = header_result.stdout.strip()
        print(current_header)

        return current_header
    except subprocess.CalledProcessError as e:
        return f"Failed to fetch block data: {e}"

def get_last_commit_hash(repo_owner: str, repo_name: str, file_path: str) -> str:
    """Fetches the last commit hash for a specific file in a GitHub repository."""
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits?path={file_path}"
    response = requests.get(api_url)
    commits = response.json()
    last_commit_hash = commits[0]["sha"]
    return last_commit_hash

def generate_certificate(username: str, fullname: str, course_id: str) -> None:
    """Generates a certificate for the given user and course."""
    course_url = f"https://raw.githubusercontent.com/PlanB-Network/bitcoin-educational-content/mainnet/courses/{course_id}/course.yml"
    response = requests.get(course_url)
    course_data = yaml.safe_load(response.text)

    level = course_data["level"]
    duration = course_data["hours"]

    en_url = f"https://raw.githubusercontent.com/PlanB-Network/bitcoin-educational-content/mainnet/courses/{course_id}/en.md"
    response = requests.get(en_url)
    en_content = response.text

    header_start = en_content.find("---")
    header_end = en_content.find("---", header_start + 1)
    header_content = en_content[header_start + 3:header_end].strip()
    header_data = yaml.safe_load(header_content)
    course_name = header_data["name"]
    goal = header_data["goal"]

    repo_owner = "PlanB-Network"
    repo_name = "bitcoin-educational-content"
    file_path = f"courses/{course_id}/en.md"
    last_commit_hash = get_last_commit_hash(repo_owner, repo_name, file_path)

    completion_date = date.today().strftime("%Y-%m-%d")

    last_block_header = get_latest_block_header()

    template_folder = "../templates"
    template_file = "pbn_course_certificate.txt"
    template_path = os.path.join(template_folder, template_file)
    with open(template_path, "r") as file:
        template_content = file.read()

    certificate_content = template_content.format(
        username=username,
        fullname=fullname,
        course_name=course_name,
        course_id=course_id.upper(),
        level=level,
        goal=goal,
        duration=duration,
        last_commit_hash=last_commit_hash,
        date=completion_date,
        last_block_header=last_block_header
    )

    file_name = f"course_certificate_{username}_{course_id}.txt"

    pending_folder = "../pending"
    os.makedirs(pending_folder, exist_ok=True)
    file_path = os.path.join(pending_folder, file_name)
    with open(file_path, "w") as file:
        file.write(certificate_content)

    print(f"Certificate generated: {file_path}")
    signed_file = sign_certificate(file_path)
    print(f"Certificate signed: {signed_file}")

    os.remove(file_path)

    timestamp_file(signed_file)
    print(f"Certificate timestamped: {signed_file}")

def sign_certificate(file_path: str) -> str:
    """Signs the certificate file using GPG."""
    signed_file = f"{file_path[:-4]}-signed.txt"
    sign_command = f'gpg --default-key admin@planb.network --output "{signed_file}" --clearsign "{file_path}"'
    subprocess.run(sign_command, shell=True, check=True)
    return signed_file

def timestamp_file(file_path: str) -> None:
    """Timestamps the signed file using OpenTimestamps."""
    timestamp_command = f'ots stamp "{file_path}"'
    subprocess.run(timestamp_command, shell=True, check=True)

if __name__ == "__main__":
    inputs_path = "../inputs"
    
    for filename in os.listdir(inputs_path):
        if filename.startswith("course") and filename.endswith(".csv"):
            file_path = os.path.join(inputs_path, filename)
            username, fullname, course_id = get_course_input(file_path)
            generate_certificate(username, fullname, course_id)
            os.remove(file_path)
