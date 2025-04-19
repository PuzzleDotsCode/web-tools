# Som


## Use disclaimer

The script is 100% passive, ethical, and safe. It does not generate any active interaction with the server beyond simple public HTTP GET requests.
It does not submit forms, perform fuzzing, or attempt brute-force attacks. It works exclusively with publicly exposed resources already available through the application.

### 🧩 What does the script actually do?

* ✔️ It performs a single HTTP GET request to the provided URL (and optionally to the bundle path).
* ✔️ It downloads those JS files exactly as a browser would.
* ✔️ It analyzes the files locally, searching for patterns that indicate potential information leaks.
* ✔️ It extracts references to JavaScript files from the returned HTML `(<script src="...">)`.