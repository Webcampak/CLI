#!/usr/bin/env bash
cd /home/webcampak/webcampak/apps/cli/
virtualenv /home/webcampak/webcampak/apps/cli/env
source /home/webcampak/webcampak/apps/cli/env/bin/activate
pip install -r requirements.txt
python setup.py develop
webcampak --help
