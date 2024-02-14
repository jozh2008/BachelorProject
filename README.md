# BachelorProject
Bachelor Project in Bioinformatic

Title: Detection of incompatibilities between installed Galaxy tools

This bachelor project aims to develop a tool within the Galaxy bioinformatics platform that identifies incompatibilities between installed tools. The program focuses on addressing issues arising from different database versions and potential errors following the release of new tool versions. By utilizing a configuration file containing datasets and workflows, the tool dynamically analyzes input requirements, checking for locally cached databases. In the presence of such databases, the program generates all possible combinations of tool inputs and executes them on the Galaxy server. In case of errors, the input configurations are logged with timestamps for further analysis and troubleshooting.
