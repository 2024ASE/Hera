import subprocess
import sys

packages_file = 'local.txt'

analysis_script = 'extract_members.py'

def install_package(package_name, version):
    full_package_name = f"python3-{package_name}"
    subprocess.run(['sudo', 'apt', 'install', '-y', full_package_name], check=True)

def uninstall_package(package_name):
    full_package_name = f"python3-{package_name}"
    subprocess.run(['sudo', 'apt', 'remove', '-y', full_package_name], check=True)
    subprocess.run(['sudo', 'apt', 'autoremove', '-y'], check=True)

def analyze_package(package_name, version):
    subprocess.run([sys.executable, analysis_script, package_name, version], check=True)

def handle_error(package_name, version, error):
    print(f"An error occurred with package {package_name}, version {version}: {error}", file=sys.stderr)

def main():
    with open(packages_file, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) != 2:
                print(f"Invalid line format: {line}", file=sys.stderr)
                continue

            package_name, version = parts
            try:
                print(f"Installing {package_name} version {version}...")
                install_package(package_name, version)
                
                print(f"Analyzing {package_name} version {version}...")
                analyze_package(package_name, version)
                
                print(f"Uninstalling {package_name}...")
                uninstall_package(package_name)
            except subprocess.CalledProcessError as e:
                handle_error(package_name, version, e)
            except Exception as e:
                handle_error(package_name, version, e)

if __name__ == '__main__':
    #main()\
    package_name, version = "amp", "0.6.1"
    try:
        print(f"Installing {package_name} version {version}...")
        install_package(package_name, version)
        
        print(f"Analyzing {package_name} version {version}...")
        analyze_package(package_name, version)
        
        print(f"Uninstalling {package_name}...")
        uninstall_package(package_name)
    except subprocess.CalledProcessError as e:
        handle_error(package_name, version, e)
    except Exception as e:
        handle_error(package_name, version, e)