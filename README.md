# Web-Scraping-Data-Pipeline
In this lab, you'll implement an industry grade data collection pipeline that runs scalably in the cloud.

# Docker Image
The docker image can be obtained from amywinder900/webscraper 

# Rescraping
To prevent rescraping, the scraper takes advantage of the unique product reference provided by the website. Before adding the product data to the dictionaries which will be sent to cloud storage, the scraper compares the product_ref to those already in the table, and skips if neccesary.

# Monitoring
The EC2 instance can be monitored via a Grafana dashboard which measures metrics using Prometheus running inside the instance. Metrics collected include container states, CPU, RAM, total uptime and rate of HTTP requests. 