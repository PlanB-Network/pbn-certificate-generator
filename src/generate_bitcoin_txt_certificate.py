import os
import yaml
import subprocess

def load_yaml_file(file_path):
    """Load and return the contents of a YAML file."""
    with open(file_path, 'r') as yaml_file:
        return yaml.safe_load(yaml_file)

def get_latest_block_header():
    """Fetches the latest block header from the mempool.space API using curl."""
    try:
        height_command = "curl -sSL 'https://mempool.space/api/blocks/tip/height'"
        height_result = subprocess.run(
            height_command, shell=True, check=True, text=True, capture_output=True
        )
        current_height = height_result.stdout.strip()
        print(f"Current block height: {current_height}")

        header_command = f"curl -sSL 'https://mempool.space/api/block-height/{current_height}'"
        header_result = subprocess.run(
            header_command, shell=True, check=True, text=True, capture_output=True
        )
        current_header = header_result.stdout.strip()
        print(f"Current block header: {current_header}")

        return current_header
    except subprocess.CalledProcessError as e:
        return f"Failed to fetch block data: {e}"

def sign_certificate(file_path):
    """Signs the certificate file using GPG."""
    signed_file = f"{file_path[:-4]}-signed.txt"
    sign_command = f'gpg --default-key admin@planb.network --output "{signed_file}" --clearsign "{file_path}"'
    subprocess.run(sign_command, shell=True, check=True)
    return signed_file

def timestamp_file(file_path):
    """Timestamps the signed file using OpenTimestamps."""
    timestamp_command = f'ots stamp "{file_path}"'
    subprocess.run(timestamp_command, shell=True, check=True)

def get_total_score(result_data):
    """
    Calculate the total score by summing all scores in the categories.

    :param result_data: Dictionary containing the exam results
    :return: Total score as an integer
    """
    if 'categories' not in result_data:
        print("No 'categories' found in result data")
        return 0

    total_score = sum(result_data['categories'].values())
    return total_score

def generate_certificate(edition_data, result_data, result_folder_path):
    """Generate a certificate using the edition and result data."""
    print("Generating certificate...")

    username = result_data.get('username', 'Unknown')
    fullname = result_data.get('display_name', 'Unknown')
    total_score = get_total_score(result_data)
    exam_id = edition_data.get('exam_id', 'Unknown')
    location = edition_data.get('location', 'Unknown')
    date = edition_data.get('date')

    last_block_header = get_latest_block_header()

    template_folder = "../templates"
    template_file = "pbn_bitcoin_certificate.txt"
    template_path = os.path.join(template_folder, template_file)
    with open(template_path, "r") as file:
        template_content = file.read()

    certificate_content = template_content.format(
        username=username,
        fullname=fullname,
        total_score=total_score,
        exam_id=exam_id,
        location=location,
        date=date,
        last_block_header=last_block_header
    )

    file_name = f"bitcoin_certificate.txt"

    file_path = os.path.join(result_folder_path, file_name)
    with open(file_path, "w") as file:
        file.write(certificate_content)

    print(f"Certificate generated: {file_path}")
    signed_file = sign_certificate(file_path)
    print(f"Certificate signed: {signed_file}")

    os.remove(file_path)

    timestamp_file(signed_file)
    print(f"Certificate timestamped: {signed_file}")

def process_result(edition_data, result_folder, subfolder):
    """Process a single result subfolder."""
    result_yml_path = os.path.join(result_folder, subfolder, "result.yml")
    if not os.path.exists(result_yml_path):
        print(f"result.yml not found in {os.path.join(result_folder, subfolder)}")
        return

    result_data = load_yaml_file(result_yml_path)
    print(f"Processing result for: {result_data.get('username', 'Unknown')}")

    total_score = get_total_score(result_data)
    print(f"Generating certificate for user with score: {total_score}")
    result_folder_path = os.path.join(result_folder, subfolder)

    ots_file = os.path.join(result_folder_path, "bitcoin_certificate-signed.txt.ots")
    if os.path.exists(ots_file):
        print(f"Certificate already generated for {result_data.get('username', 'Unknown')}")
    else:
        print(f"Generation in progress..")
        generate_certificate(edition_data, result_data, result_folder_path)
    print()

def process_edition(edition_path):
    """Process a single edition folder."""
    edition_data_path = os.path.join(edition_path, "bcert.yml")
    edition_data = load_yaml_file(edition_data_path)

    result_folder = os.path.join(edition_path, "results")
    if not os.path.exists(result_folder):
        print(f"Results folder not found in {edition_path}")
        return

    subfolders = [f for f in os.listdir(result_folder) if os.path.isdir(os.path.join(result_folder, f))]
    subfolders = sorted(subfolders)
    if not subfolders:
        print(f"No subfolders found in {result_folder}")
        return

    for subfolder in sorted(subfolders):
        process_result(edition_data, result_folder, subfolder)

def select_editions_interactively(bcert_path):
    """Display editions and let user select which ones to process."""
    # Get all edition folders
    all_editions = []
    for edition_folder in sorted(os.listdir(bcert_path)):
        edition_path = os.path.join(bcert_path, edition_folder)
        if os.path.isdir(edition_path):
            all_editions.append((edition_folder, edition_path))

    if not all_editions:
        print("No editions found!")
        return []

    # Display available editions
    print("\n=== Available Editions ===")
    for idx, (edition_name, _) in enumerate(all_editions, 1):
        print(f"{idx}. {edition_name}")
    print(f"{len(all_editions) + 1}. Process ALL editions")
    print("=" * 30)

    # Get user selection
    while True:
        try:
            choice = input("\nEnter edition number to process (or 'q' to quit): ").strip()

            if choice.lower() == 'q':
                print("Exiting...")
                return []

            choice_num = int(choice)

            # Check if user wants all editions
            if choice_num == len(all_editions) + 1:
                return all_editions

            # Validate selection
            if 1 <= choice_num <= len(all_editions):
                selected = all_editions[choice_num - 1]
                print(f"\nSelected: {selected[0]}")
                return [selected]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(all_editions) + 1}")

        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")

def process_all_editions(bcert_path):
    """Process all edition folders in the given path."""
    for edition_folder in sorted(os.listdir(bcert_path)):
        edition_path = os.path.join(bcert_path, edition_folder)
        if os.path.isdir(edition_path):
            print(f"\nProcessing edition: {edition_folder}")
            process_edition(edition_path)

if __name__ == "__main__":
    bcert_path = "../../planB-premium-content/bcert/editions/"

    # Interactive selection
    selected_editions = select_editions_interactively(bcert_path)

    if selected_editions:
        print("\n" + "=" * 50)
        print("Starting certificate generation...")
        print("=" * 50)

        for edition_name, edition_path in selected_editions:
            print(f"\nProcessing edition: {edition_name}")
            process_edition(edition_path)

        print("\n" + "=" * 50)
        print("Certificate generation completed!")
        print("=" * 50)
    else:
        print("No editions selected.")
