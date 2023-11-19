


## Install follow liberies

    pip install sqlite3
    pip install google-api-python-client

or use

    pip install -r requirements.txt

check versions: run `python version.py`

| library                   | Version           | annotation |
| ------------------------- | ----------------- | -----------|
| python                    | 3.11.3            | or newer |
| google-api-python-client  | 2.108.0           | or newer |
| sqlite3                   | 2.6.0             | or newer |



## first run

1. run installation

    python install.py

2. put your youtube api token in `config.ini` as API_SECRET

3. fill the `/data/channels.csv`, it is possible to have multiple `.csv`-files, all will be used
<!-- TODO: is it possible to add some during runtime? -->

4. run application

    python run.py
