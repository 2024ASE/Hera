# Hera
ASE2024 submission

This repository contains the code and experimental data of our project. The code mainly consists of building a compatibility database offline and building a system-level PDG online and detecting CC issues. 
  
## Offline phase  
  
Building the compatibility database offline is divided into two main steps: building the dependency table and compatibility table. 
 
### Dependency table
1. analyzing intra-repository dependencies of apt repository:  
   - Simulate apt installation of packages using "apt_simulate.py" to get real package dependencies. 
  
2. Extract all API usages of the library packages:  
   - Execute the "run.py" script in the docker environment to extract the API usage of each package for the dependencies.  

### Compatibility table
1. API extraction:  
   - Execute the "api_extractor.py" script in the docker environment to extract the provided APIs for each version of each package, the relevant scripts are available in the bin directory.
  
2. Analyzing incompatible changes:  
   - Use "api_compare.py" to detect APIs where incompatible changes occur between different versions of the same edition based on seven rules. 
  
## Online phase  

1. Build the system-level PDG
   - Run "construct_PDG.py" to construct PDG for two repositories, then merge them into system-level PDG and output covered_edge.

2. Detect CC issue  
   - Run "CC_detector.py" script to get data from the compatibility database, check whether there is a CC issue for the packages at both ends of covered_edge and report it.

## Experimental data
This repository also provides all the experimental data for the three RQs in the paper as well as the constructed CC issue dataset and build code. Due to the overall large size of the compatibility database, this repository only uploads the IC API data used in RQ1 (about 900 files).

## Project file structure 

- Hera/
  - README.md
  - code/
    - bin/
      - analyse.sh
      - build_images.sh
      - cleanup_images.sh
      - download_wheels.sh
      - get_releases.sh
      - make_image_dir.sh
      - reboot.sh
    - src/
      - api_compare.py
      - api_extractor.py
      - apt_simulate.py
      - CC_detector.py
      - construct_PDG.py
      - Dockerfile
      - entrypoint.sh
      - extract_members.py
      - fixing_finder.py
      - get_apt_version.py
      - library_traverser.py
      - run.py
      - utils.py
    - wheels/common/
    - data/
      - all_framework.txt
      - package_info_all.txt
      - package_info_new_all.xlsx
  - experimental data/
    - RQ1/
      - resource/
      - database.py
      - import_test.py
      - local_apt_extract.py
      - local_evaluation1.py
      - dependency_parse.py
      - CC issue dataset.xlsx
      - pairs.xlsx
    - RQ2/
      - sample.py
      - sample.json
      - CC issue dataset.xlsx
      - RQ2.xlsx
    - RQ3/
      - issues.xlsx

