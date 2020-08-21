# Kolibri Studio load testing experiment

# Expected behaviour

- None of the requests will return a 500, 502 or 503 error
- None of the requests will take longer than 20 seconds to return a response

# Steps to run

To run against your local studio instance, simply run:

``` bash
$ make run
```

This pings your localhost:8080 server with 100 clients and a 20 users/sec hatch
rate. You can set each of these parameters for a run.

You can also specify the duration to run the tests for, along with the results
file(s), using the following parameters:

```bash
make run TIME_ARG="-t5m" RESULTS_FILE="--csv=profile_results"
```

To run this script against the Studio staging server, change the `URL`
parameter:

``` bash
$ make run URL=https://develop.studio.learningequality.org
USERNAME=<yourusername> PASSWORD=<yourpassword>
```

To customize the number of clients and the hatch rate, set the `NUM_CLIENTS` and
the `HATCH_RATE` respectively:

``` bash
$ make run NUM_CLIENTS=5 HATCH_RATE=1
```

After stopping it, Locust slaves must be stopped:

```bash
$ make stop_slaves
```

# [WIP] Documentation on generating and running locust based on har files

## Record har file
1. Record a *har* file with the scenario execution:
   1. Open Chrome or Firefox in either Guest or Incognito mode (it’s important to have no cookies prior to starting).
   2. Open the Developer Tools.
   3. Open the Network panel.
   4. Select Disable cache and Preserve log.
   5. Clear the existing log by clicking the Clear 🚫 button.
   6. Ensure recording is enabled: the Record button should be red 🔴 (click it to toggle).
   7. Navigate to Studio server by entering the URL in the address bar, like http://127.0.0.1:8080 and
      perform your scenario by clicking through the pages, filling in forms, clicking buttons, etc. exactly as a normal user would do
   8. **End recording** by clicking the Record 🔴 button.
   9. **Right-click** on any of the file names listed in the bottom pane of the Network panel.
   10. Select **Save as HAR with content**.
   11. Save the file on your machine in the performance/har folder
   12. Repeate the process for each of the Gherking files

##  Convert the *har* file into a Python file to perform the tests:

   In a console, execute inside the performance folder.
``` bash
$ transformer -p plugins.studio har/ >login_locust.py
```

## Run a first test on the created locust file:

``` bash
$ locust -f login_locust.py  --users=1 -r 1 --headless --run-time=30s   --host=http://127.0.0.1:8080
```
