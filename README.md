Webcampak 3.0 CLI
==============================================================================

[![Build Status](https://travis-ci.org/Webcampak/cli.svg?branch=develop)](https://travis-ci.org/Webcampak/cli) [![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)

Webcampak CLI is the tool in charge of picture acquisition, video creation, xfer queue management and other backend related tasks.
It is currently being called by CRON jobs or through the API.

Forewords
------------
Many parts of the system refer to a static path to access many different webcampak files. 
To facilitate development (and even deployment), we recommend using cloning the core repo into: /home/webcampak/webcampak/


Installation
------------

```
$ pip install -r requirements.txt
$ python setup.py install
```

Development environment
------------

```
$ cd /home/webcampak/webcampak/bin/cli/
$ virtualenv /home/webcampak/webcampak/bin/cli/env
$ source /home/webcampak/webcampak/bin/cli/env/bin/activate
$ pip install -r requirements.txt
$ python setup.py develop
$ webcampak --help
```
