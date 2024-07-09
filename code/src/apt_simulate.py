import os
def openreadtxt(file_name):
    data = []
    file = open(file_name,'r')  
    file_data = file.readlines() 
    for row in file_data:
        data.append(row) 
    return data

def write_data(res,name):
    output = open('./apt_depends_data.txt','a',encoding='utf-8-sig')
    output.write(str(name).replace('\n','')+':')
    pkg_row = []
    flag = False
    for i in range(len(res)):
        if res[i] == "The following additional packages will be installed:\n":
           flag = True
           continue
        if res[i] == "Suggested packages:\n" or res[i] == "The following NEW packages will be installed:\n":
           flag = False
           continue
        if flag and res[i] != '\n':
            pkg_row.append(res[i])
    if len(pkg_row) == 0:
        #output.write("None")
        output.write('\n')
        output.close()
    else:
        for row in pkg_row:
            row.replace("\n",'')
            pkg_list = row.split(' ')
            for pkg in pkg_list:
                if "python3-" in str(pkg) and not("libpython3-" in str(pkg)):
                    output.write(str(pkg).replace("\n",''))
                    output.write(',')
        output.write('\n')
        output.close()

def simulate(list):
    a = 1
    for name in list:
        tow = os.popen('apt install -s {0}'.format("python3-"+name)).readlines()
        write_data(tow,name)
        print(a)
        a = a + 1

if __name__=="__main__":
    list = openreadtxt("./aptPkgName.txt")
    simulate(list)