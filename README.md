# BachelorProject
Bachelor Project in Bioinformatic

Program detects incompatibilites between installed Galaxy tools

Where can we use it?

    1)Solve problems with different versions of databases
    2)Check to see if an error occurs after the release of a new version

Takes datasets and workflow given in the config file.
Runs the workflow with the datasets as input. Check if a tool has as input a locally cached database.

If so, generate all combination of the tool input.

Run every combination of tool input on the Galaxy server.

If an error occurs, store the input with a timestemp in a file. 
