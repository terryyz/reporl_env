import json
import re
import os
from collections import defaultdict

def read_jsonl(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            yield json.loads(line)

def count_dependencies(jsonl_file):
    dependency_count = defaultdict(int)
    # Regular expression to match valid package names
    package_name_pattern = re.compile(r'^[a-zA-Z0-9\-_]+$')
    # List of keywords to exclude
    exclude_keywords = ['torch', 'tensorflow', 'cudnn', 'cuda', 'cupy', 'mxnet', 'chainer', 'pytorch', 'onnx', 'nvidia', 'jax']

    for obj in read_jsonl(jsonl_file):
        requirements = obj.get('requirements', '')
        dependencies = requirements.split('\n')
        for dep in dependencies:
            if dep:  # Ensure the dependency is not an empty string
                package_name = dep.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
                # Check if package name contains any of the exclude keywords
                if any(keyword in package_name for keyword in exclude_keywords):
                    continue
                match = package_name_pattern.match(package_name)
                if match:
                    package_name = match.group(0)
                    dependency_count[package_name] += 1
    
    return dependency_count

def write_requirements(dependency_count, output_file, min_count=50):
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as file:
        for dep, count in dependency_count.items():
            if count >= min_count:
                file.write(f"{dep}\n")

def filter_and_write_repos(jsonl_file, requirements_file, output_jsonl_file):
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_jsonl_file), exist_ok=True)
    
    # Read the final requirements from the requirements.txt file
    with open(requirements_file, 'r') as file:
        final_requirements = set(line.strip() for line in file if line.strip())

    with open(jsonl_file, 'r') as infile, open(output_jsonl_file, 'w') as outfile:
        for line in infile:
            obj = json.loads(line)
            # Get requirements and filter out empty strings immediately
            requirements = [req for req in obj.get('requirements', '').split('\n') if req.strip()]
            # Filter out requirements that are not in the final list
            filtered_requirements = [req for req in requirements if req.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip() in final_requirements]
            if len(filtered_requirements) == len(requirements) and requirements:
                # Write the repo name and filtered requirements to the new JSONL file
                json.dump({"repo_name": obj["repo_name"], "requirements": filtered_requirements}, outfile)
                outfile.write('\n')

def main():
    N = 50
    jsonl_file = 'repo_names_dedup_20250203_requirements.jsonl'  # Replace with your JSONL file path
    output_file = f'{N}/requirements.txt'
    output_jsonl_file = f'{N}/repos.jsonl'
    
    dependency_count = count_dependencies(jsonl_file)
    write_requirements(dependency_count, output_file, N)
    filter_and_write_repos(jsonl_file, output_file, output_jsonl_file)

if __name__ == "__main__":
    main()