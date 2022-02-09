# Usage
To run the scripts under the examples, first create a virtual python environment (assuming linux environment):

```
cd examples
```
```
python3 -m venv .venv
```
Activate it:
``` 
. .venv/bin/activate
```
install requirements
```
pip install -r requirements.txt
```

Fill the `examples/conf.ini` file with your enterprise credentials.

You can now run the scripts under examples, e.g.

```
python3 azure/upload.py --help
```
```
python3 scenario_scheduler.py --help
```
