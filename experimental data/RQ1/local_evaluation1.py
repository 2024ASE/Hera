import subprocess
import sys
import json
import pickle



def install_pip_package(package_name, version):
    package_name = package_name.replace('python3-','')
    try:
        #temp = os.popen('pip install -i https://mirrors.cloud.tencent.com/pypi/simple {0}=={1}'.format(package_name,version)).readlines()
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name+"=="+str(version), "-i", "https://mirrors.cloud.tencent.com/pypi/simple"])
        return True
    except subprocess.CalledProcessError as e:

        return False

def install_apt_package(package_name):
    try:
        subprocess.check_call(['sudo', 'apt', 'install', '-y', package_name])
        # print("success")
        return True
    except subprocess.CalledProcessError as e:
        return False

# 尝试导入包
def try_import_apt_package(package_name):
    package_name = package_name.replace('python3-','')
    package_name = package_name.replace('-','_')
    try:
        result = subprocess.run([sys.executable, 'import_test.py', package_name], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == "Success":
            # print("success")
            return True
        else:
            # print("fail")
            return False
    except subprocess.CalledProcessError as e:
        return False
    
def try_import_pip_package(package_name):
    package_name = package_name.replace('python3-','')
    package_name = package_name.replace('-','_')
    try:
        result = subprocess.run([sys.executable, 'import_test.py', package_name], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() == "Success":
            # print("success")
            return True, ''
        else:
            # print("fail")
            return False, str(result.stdout)
    except subprocess.CalledProcessError as e:
        return False, str(e)

# 使用 pip 卸载包
def uninstall_pip_package(package_name):
    package_name = package_name.replace('python3-','')
    try:
        #temp = os.popen('pip uninstall -y {0}'.format(package_name)).readlines()
        subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', '-y', package_name])
    except subprocess.CalledProcessError as e:
        pass

# 使用 apt 卸载包
def uninstall_apt_package(package_name):
    if package_name == 'python3-pip':
        return
    try:
        #temp = os.popen('sudo apt purge -y {0}'.format(package_name)).readlines()
        subprocess.check_call(['sudo', 'apt', 'purge', '-y', package_name])
    except subprocess.CalledProcessError as e:
        subprocess.check_call(['sudo', 'apt', 'reinstall', '-y', 'python3-octavia-dashboard'])

# 处理包的主要函数
def process_packages(graph):
    packages = []
    with open("package_with_dep.txt", "r") as file:
        for line in file:
            line = str(line.strip())
            packages.append(line)
    #print(packages)
    #packages = ["python3-networkx","python3-amp"]
    #for package in graph.nodes():
    #error_packages = []
    for package in packages:
        print(f"running>>>>>>>>>>>>>>>>>>{package}>>>>>>>>>>>>>>>>>>>>>>>>")
        for dep in graph.successors(package):
                if dep != '':
                    uninstall_pip_package(dep)
        if install_apt_package(package) and try_import_apt_package(package):
            for dep in graph.successors(package):
                if dep != '':
                    dep_info = graph.nodes[dep]
                    if dep_info.get('pip_info', False):
                        version = dep_info.get('pip_versions')[-1]
                        if version and install_pip_package(dep, version):
                            second_try, error = False, ''
                            second_try, error = try_import_pip_package(package)
                            if not second_try:
                                #error_packages.append((package, dep, error))
                                # error_info = f"{package}\t{dep}\t{error}"
                                # with open("./error.txt", "a") as file:
                                #     file.write(error_info)
                                file = []
                                with open('traceback.json', 'r') as f:
                                    file = json.load(f)
                                file.append({
                                    'package':package,
                                    'dep':dep,
                                    'error':error})
                                with open('traceback.json', 'w') as f:
                                    json.dump(file, f, indent=4)
                        # 卸载 pip 安装的依赖项
                        uninstall_pip_package(dep)
        for dep in graph.successors(package):
                if dep != '':
                    uninstall_pip_package(dep)
        uninstall_apt_package(package)
    return "success"



if __name__ == '__main__':
    package_name = "networkx"
    with open("dependency_graph_new.pkl", "rb") as file:
        dependency_graph = pickle.load(file)

    inconsistencies = process_packages(dependency_graph)

