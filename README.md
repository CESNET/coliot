![alt text](https://github.com/gre0071/coliot/blob/master/coliot_logo.png)

# Coliot collector
## Installation instructions
To install the Coliot collector web-interface simply run the installation script, which is part of our solution.

```
git clone https://github.com/gre0071/coliot.git ./coliot-install
cd ./coliot-install

sudo ./install.sh
```

## Web-interface
Coliot collector web-interface serves as a graphical interface to visualize and analyze stored data. This solution is based on Apache Supserset, which is a modern, enterprise-ready business intelligence web application. 

The data comes to the Coliot collector in UniRec format, which uses the NEMEA framework. For visualization, this data are transformed into a SQLite database, which runs automatically and continuously as the data arrives to the collector. Depending on predefined templates, UniRec records are stored in individual tables in a relational database. 

The Coliot collector installation package includes a set of preconfigured views and graphs for visualization, which are accessible via web application.

Coliot collector web-interface runs on port ```8088```.

## Coliot module
This module performs automatic aggregation of messages from UniRec format to collector. The message header is used to identify the event type where fields and types are specified.

### Prerequisites
Installation NEMEA System from github
* https://github.com/CESNET/Nemea

Install NEMEA pytrap
```
pip install nemea-pytrap
```

### Template configuration
To create new template, a user first needs to specify a set of fields and their types in the template.

Example of the template definition /template/dispatch.tml
```
[MAIN]
TemplateName = DispatchTemplate
TableName = siot_dispatch
Enable = true

[FIELDS]
ID = uint64
TIME = double
cmd = string
```
### Run instruction
```
sudo ./coliot.py -i u:coliot-socket
# Example test for autogenerate data
sudo ./nemea-generator
```

### Description

### Interfaces
- Input: One UniRec interface, which you must specify in the template file.
  
### Parameters
#### Common TRAP parameters
- `-h [trap,1]`      Print help message for this module / for libtrap specific parameters.
- `-i IFC_SPEC`      Specification of interface types and their parameters.
- `-v`               Be verbose.
- `-vv`              Be more verbose.
- `-vvv`             Be even more verbose.

## Screenshot of the web-interface
![alt text](https://github.com/gre0071/coliot/blob/master/screen.PNG)
