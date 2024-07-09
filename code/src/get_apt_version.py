import apt
import importlib
# import apt_pkg
import subprocess
import re


def install_package(package_name):
    with apt.Cache() as cache:
        pkg = cache[str("python3-" + package_name)]

        if pkg.is_installed:
            print(f"{package_name} is already installed.")
        else:
            pkg.mark_install()

        cache.commit()


def get_package_info(package_name):
    version = "$"
    top_module = "$"
    try:
        pkg = importlib.import_module(package_name.replace("-", "_"))
    except Exception as e:
        version = "#"
        top_module = "#"

    try:
        version = pkg.__version__
    except Exception as e:
        try:
            output = subprocess.check_output(
                ["pip", "show", package_name]).decode("utf-8")
            version_pattern = r"Version:\s+(\S+)"
            match = re.search(version_pattern, output)
            if match:
                version = match.group(1)
                print(f"The version of {package_name} is {version}")
            else:
                print(f"Failed to extract the version of {package_name}")
        except Exception as e:
            pass

    try:
        top_module = pkg.__name__.split('.')[0]
    except Exception as e:
        pass

    print(f"Package: {package_name}")
    print(f"Version: {version}")
    print(f"Top-level Module: {top_module}")
    return package_name, str(version), top_module


def uninstall_package(package_name):
    with apt.Cache() as cache:
        pkg = cache[str("python3-" + package_name)]

        if pkg.is_installed:
            pass
            # pkg.mark_delete()
            subprocess.call(["apt-get", "purge", "-y",
                            str("python3-" + package_name)])

        cache.commit()

    # apt_pkg.init()
    # apt_pkg.config.set("APT::Get::Purge", "true")
    # cache.commit()

flag = 0
with open('~/aptPkgName4.txt', 'r') as file:
    packages = file.readlines()
    packages = [package.strip() for package in packages]

with open('~/aptPkgVersion4.txt', 'r') as file:
    versions = file.readlines()
    versions = [version.strip() for version in versions]

# mongn_client = pymongo.MongoClient('mongodb://localhost:27017')
# db = mongn_client.get_database("Apt_versions")
# collection = db.get_collection("apt_versions")

with open('~/package_info4.txt', 'a') as file:

    for package in packages:
        package = package.replace('\ufeff', '')
        try:
            install_package(package)
        except Exception as e:
            package_info = package, "&", "&"
            file.write("\t".join(package_info) + "\t" + versions[flag] + "\n")
            flag = flag + 1
            uninstall_package(package)
            continue

        package_info = get_package_info(package)
        file.write("\t".join(package_info) + "\t" + versions[flag] + "\n")
        # collection.insert_one({
        #     "Package Name": package_info[0],
        #     "Version": package_info[1],
        #     "Top-level Module": package_info[2],
        #     "Apt_version": versions[flag]})
        # sheet.append(package_info)
        if package == "apt":
            flag = flag + 1
            print("=" * 20)
            continue
        try:
            uninstall_package(package)
        except Exception as e:
            flag = flag + 1
            continue
        print("Package removed.")
        flag = flag + 1
        print("=" * 20)
        if flag == 300:
            break
print("Package information has been appended to package_info.txt.")
# workbook.save("./package_info.xlsx")
