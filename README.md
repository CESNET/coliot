![alt text](https://github.com/gre0071/coliot/blob/master/coliot_logo.png)

# Coliot collector
## Web-interface
Coliot collector web-interface serves as a graphical interface to visualize and analyze stored data. This solution is based on Apache Supserset, which is a modern, enterprise-ready business intelligence web application. 

The data comes to the Coliot collector in UniRec format, which uses the NEMEA framework. For visualization, this data are transformed into a SQLite database, which runs automatically and continuously as the data arrives to the collector. Depending on predefined templates, UniRec records are stored in individual tables in a relational database. 

The Coliot collector installation package includes a set of preconfigured views and graphs for visualization, which are accessible via web application.

## Installation instructions
To install the Coliot collector web-interface simply run the installation script, which is part of our solution.

```
git clone https://github.com/gre0071/coliot.git ./coliot-install
cd ./coliot-install

sudo ./install.sh
```




* https://github.com/apache/incubator-superset
* https://github.com/CESNET/Nemea-Framework
* https://github.com/CESNET/Nemea
