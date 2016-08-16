## device42-zabbix.py

Maintainer: Mark Mercado <mamercad@umflint.edu>

#### Overview

This script pushes five facts from Device42 (`os`, `custom_fields['Spacewalk Organization, 'Spacewalk Activation Key', 'Spacewalk Base Channel', 'Spacewalk Registration Date']`) into Zabbix's inventory. Naturally, these fields must be created in Device42 as "custom fields". In the order listed, the first three are type `text` and the last is type `date`. Check out [this repo](https://github.com/um-flint/spacewalk-device42.git) to handle pulling these facts from Spacewalk and dumping them into Device42.

#### Usage

Rename `device42-zabbix.ini.sample` to `device42-zabbix.ini` and update accordingly.

#### Python modules

```python
import ConfigParser
import requests
```
