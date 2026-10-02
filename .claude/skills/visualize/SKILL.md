---
name: visualize
description: Visualizes the latest data stored in the ".claude/skills/migrate/data/".
---

Usage:

#Step-1: Pick the python environment
Before you start, make sure to pick the python environment in which you want to run the code. You can run/install dependencies using my '.venv' environment which is located at "C:\ClaudeCode\.venv"

#Step-2: Read the Parquet Data
- You need to read the latest Parquet data stored at ".claude/skills/migrate/data/". 

#Step-3: Use pandas to Aggregate the Data and Build KPI's
Use pandas to aggregate the data and build KPI's. You need to Build KPI's like Total Revenue, Total Orders, Total Customers, Average Order Value, etc. 


#Step-4:Use Matplotlib and Seaborn to Visualize the Data
Use Matplotlib and Seaborn to visualize the data.you need to create the visualization in the directory ".claude/skills/visualize/visualizations/" . Use plt.savefig() to save the visualizations in the directory ".claude/skills/visualize/visualizations/" with the same name as source folder (datetime).