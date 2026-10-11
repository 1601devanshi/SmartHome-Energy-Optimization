
# System Architecture

The project separates the user interface from the optimization logic.

- **`app.py`** provides the Streamlit dashboard and user interactions.
- **`main.py`** contains the optimization engine and scheduling logic.
- **`requirements.txt`** lists the Python packages needed to run the project.
- **`smarthome_config.json`**, when created by the application, stores local configuration data.

```mermaid
flowchart TD
    U["User"] --> UI["Streamlit Dashboard<br/>app.py"]
    UI --> A["Appliance Configuration"]
    UI --> T["Hourly Electricity Tariffs"]
    A --> E["Optimization Engine<br/>main.py"]
    T --> E
    E --> GA["Genetic Algorithm"]
    E --> B["Baseline Scheduler"]
    E --> G["Greedy Benchmark"]
    GA --> R["Schedule Evaluation"]
    B --> R
    G --> R
    R --> M["Cost, Energy and Peak Load Metrics"]
    M --> C["Interactive Charts"]
    M --> X["CSV Report Export"]
```
