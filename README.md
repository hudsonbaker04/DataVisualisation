# Running
- First, create a virtual environment inside the top code directory:
  ```Bash
  python3.11 -m venv venv
  ```
- Then, enter it:
  ```Bash
  . venv/bin/activate
  ```
- Now, install the project dependencies:
  ```Bash
  pip install --no-user -r requirements.txt
  ```
- Navigate into the src directory:
  ```Bash
  cd src/
  ```
- Run the Jupyter notebook (be sure to point the Jupyter kernel at the venv) or **(for a better experience)** run the .py file and point a browser at 127.0.0.1:8050
  ```Bash
  python visualisation.py
  ```
**N.B.** Running the code to scrape the data takes a very long time and will overwrite the existing saved CSV files - be careful if running.

## Structure
- src/ \
  The src directory contains all of the project source code.
- data/ \
  The data directory contains the csv data files used in the visualisation.
- assets/ \
  The assets directory contains CSS elements which are picked up by the Dash application.
- visualisation.ipynb \
  This contains all of the project code, from scraping and geocoding through to visualising, in logical order.
- visualisation.py \
  This contains purely the visualisation code for running the Dash application through a browser (this is the best way to experience the visualisation).
