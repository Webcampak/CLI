cd /home/webcampak/webcampak/bin/webcampak/
virtualenv /home/webcampak/webcampak/bin/webcampak/env
source /home/webcampak/webcampak/bin/webcampak/env/bin/activate
pip install -r requirements.txt
python setup.py develop
webcampak --help
