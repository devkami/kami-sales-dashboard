#!/bin/bash
echo "Extraindo Base BI"
cd /root/pythonmations/kami-sales-dashboard/kami_sales_dashboard/
poetry shell
ipython3 dataframe.py