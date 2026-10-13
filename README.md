# 🏡 SmartHome Energy Optimization
### Intelligent Appliance Scheduling Using a Genetic Algorithm

An interactive Python and Streamlit application that optimizes household appliance schedules to reduce estimated electricity costs and manage peak energy demand.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Framework-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![Algorithm](https://img.shields.io/badge/Algorithm-Genetic%20Algorithm-7B61FF)](#-optimization-methodology)
[![Deployment](https://img.shields.io/badge/Deployment-Render-46E3B7?logo=render)](https://render.com/)

---

## 🌐 Live Demo


Explore the interactive Streamlit dashboard to optimize smart home appliance schedules using a Genetic Algorithm, compare scheduling strategies, and analyze estimated electricity costs and peak energy demand.

👉 https://smarthome-energy-optimization.onrender.com

---

## 📌 1. Project Overview

Electricity tariffs can vary throughout the day, while many household appliances do not need to operate at a fixed time. Running flexible appliances during lower-tariff periods can help reduce electricity costs.

**SmartHome Energy Optimization** is a simulation-based project that uses a Genetic Algorithm (GA) to find promising appliance schedules based on electricity prices, appliance operating constraints, and a preferred maximum hourly load.

The application provides a dashboard where users can configure appliances, adjust hourly tariffs, run optimization experiments, compare schedules, and visualize the results.

> **Note:** This is an educational software simulation. It does not directly connect to smart meters or control physical household appliances.

## 🎯 2. Project Objectives

- Minimize estimated electricity costs through intelligent scheduling.
- Shift flexible appliance usage toward lower-tariff hours.
- Analyze hourly energy demand and peak load.
- Compare optimized schedules against a baseline schedule.
- Demonstrate the practical application of Genetic Algorithms.
- Provide an interactive dashboard for experimentation and visualization.

## ✨ 3. Key Features

| Feature | Description |
|---|---|
| Interactive dashboard | View energy consumption, estimated cost, and peak load. |
| Appliance management | Add, edit, and remove appliances. |
| Flexible scheduling | Configure power, duration, and allowed operating hours. |
| Hourly tariff editor | Customize electricity prices for all 24 hours. |
| Genetic Algorithm | Search for lower-cost appliance schedules. |
| Schedule comparison | Compare the baseline, greedy benchmark, and optimized schedule where supported by the application. |
| Visual analytics | Explore hourly load and electricity cost using charts. |
| CSV reports | Export available optimization results for analysis. |
| Configuration persistence | Save and restore configuration locally where supported. |
| Optimization settings | Adjust population size, generations, crossover, and mutation parameters. |

## 🧠 4. Optimization Methodology

The project uses a **Genetic Algorithm**, an evolutionary optimization technique inspired by natural selection.

Each candidate solution represents the selected starting hour of the configured appliances. The algorithm evaluates candidate schedules and evolves them across multiple generations.

### How the algorithm works

1. **Initialization:** Generate a population of candidate schedules.
2. **Fitness evaluation:** Calculate the estimated electricity cost and any applicable overload penalty.
3. **Selection:** Prefer better-performing candidate schedules.
4. **Crossover:** Combine parts of selected candidate schedules.
5. **Mutation:** Randomly modify some scheduling decisions to explore alternatives.
6. **Elitism:** Preserve strong candidates between generations.
7. **Termination:** Stop after the configured number of generations.
8. **Result analysis:** Display the selected schedule and relevant comparison metrics.

### Fitness function

The general optimization objective is:

**Fitness = Estimated Electricity Cost + Overload Penalty**

A lower fitness value is preferred. The precise behavior depends on the implementation of the optimization engine and its penalty settings.

The Genetic Algorithm is a heuristic search method, so it does not guarantee a globally optimal solution.

## 🔄 5. Genetic Algorithm Workflow

View the complete workflow diagram separately:

[**Open Genetic Algorithm Workflow →**](diagrams/ga-workflow.md)

## 🏗️ 6. System Architecture

The project separates the user interface from the optimization logic.

- **`app.py`** provides the Streamlit dashboard and user interactions.
- **`main.py`** contains the optimization engine and scheduling logic.
- **`requirements.txt`** lists the required Python packages.
- **`smarthome_config.json`** stores local configuration data when created by the application.

[**Open System Architecture Diagram →**](diagrams/system-architecture.md)

## 🧮 7. Energy and Cost Calculations

The dashboard uses appliance power ratings, operating durations, and hourly electricity tariffs to estimate consumption and cost.

- **Hourly load (kW):** Combined power rating of appliances operating during that hour.
- **Energy consumption (kWh):** Power in kW multiplied by operating time in hours.
- **Estimated electricity cost:** Energy consumed during each hour multiplied by that hour's tariff.
- **Peak load (kW):** Highest combined hourly power demand during the day.

For example, an appliance rated at **0.7 kW** running for **2 hours** consumes approximately **1.4 kWh**.

The example tariff values should be treated as illustrative values in ₹/kWh, not as verified rates from a specific electricity provider.

## 🛠️ 8. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web dashboard |
| Pandas | Tabular data processing |
| Plotly | Interactive charts and visualization |
| Genetic Algorithm | Appliance schedule optimization |
| Git and GitHub | Version control and project hosting |
| Render | Cloud deployment |

## 📂 9. Project Structure

```text
SmartHome-Energy-Optimization/
│
├── app.py
│   └── Streamlit dashboard and user interface
│
├── main.py
│   └── Optimization engine and scheduling algorithms
│
├── requirements.txt
│   └── Python dependencies
│
├── README.md
│   └── Project documentation
│
└── smarthome_config.json
    └── Optional runtime-generated configuration
```

The JSON configuration file may be created at runtime and may not exist in a fresh clone of the repository.

## 💻 10. Installation and Local Setup

### Prerequisites

- Python 3.10 or newer
- Git
- Visual Studio Code or another Python editor
- Internet connection for installing dependencies

### Step 1: Clone the repository

Replace `YOUR_GITHUB_USERNAME` with your GitHub username.

```bash

git clone https://github.com/1601devanshi/SmartHome-Energy-Optimization.git
cd SmartHome-Energy-Optimization

```

Alternatively, download the repository as a ZIP file and extract it.

### Step 2: Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 3: Run the application

```bash
python -m streamlit run app.py
```

### Step 4: Open the dashboard

Visit the following address in your browser if it does not open automatically:

```text
http://localhost:8501
```

## ☁️ 11. Deployment on Render

The application can be deployed as a Render Web Service.

### Deployment steps

1. Push the project to GitHub.
2. Sign in at [Render](https://render.com/).
3. Select **New → Web Service**.
4. Connect your GitHub account.
5. Select the `SmartHome-Energy-Optimization` repository.
6. Configure the service using the settings below.
7. Start deployment and monitor the build logs.
8. Open the public URL generated by Render.

### Render configuration

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |

Ensure that `app.py`, `main.py`, and `requirements.txt` are located in the repository root unless you have changed the deployment commands.

**Deployment note:** Render's filesystem may be ephemeral. Locally saved JSON configurations may not survive a restart or redeployment. Persistent configuration storage would require an appropriate persistent disk or external storage solution.

## 📊 12. Suggested Experiments

The application can be used to explore several optimization scenarios.

### Experiment 1: Baseline vs. optimized schedule
Compare estimated electricity costs and peak loads under identical appliance settings and tariffs.

### Experiment 2: Changing electricity tariffs
Increase selected evening tariffs and observe whether flexible appliances move toward less expensive hours.

### Experiment 3: Population size
Compare smaller and larger populations to investigate their effects on the quality of the schedule and execution time.

### Experiment 4: Number of generations
Test different generation counts to observe how the search progresses.

### Experiment 5: Maximum hourly load
Change the preferred load limit and examine how the optimization responds to the resulting constraint or penalty.

For meaningful comparisons, keep the appliance configuration and tariff values unchanged between experiments unless those are the variables being tested.

## ⚠️ 13. Assumptions and Limitations

- This project simulates scheduling and does not control real appliances.
- Electricity tariff values are illustrative and must be replaced with appropriate rates for realistic estimates.
- Appliance power consumption is modeled using configured power ratings and durations.
- Scheduling across midnight may be unsupported by the current implementation.
- A maximum-load target may be infeasible when appliance constraints conflict.
- The Genetic Algorithm may produce different results for different random seeds and settings.
- Optimization results depend on the implementation of the fitness function and scheduling constraints.
- The application does not necessarily reduce total energy consumption; shifting usage to cheaper hours can reduce estimated cost without reducing kWh.

## 🔮 14. Future Enhancements

- Integrate smart-meter and IoT data.
- Add renewable energy and battery storage scheduling.
- Support multi-day optimization.
- Import real time-of-use tariff schedules.
- Store configurations in a persistent database.
- Add user accounts and saved experiment history.
- Compare Genetic Algorithms with Particle Swarm Optimization and other methods.
- Add more detailed convergence analysis and performance benchmarks.

## 🤝 15. Contributing

Contributions and suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Commit your work with a meaningful message.
5. Open a pull request describing the improvement.

## 📄 16. License

No license has been specified yet. Add a `LICENSE` file if you intend to distribute the project for reuse.

---

<div align="center">

**SmartHome Energy Optimization**  
*Smarter Scheduling. Better Energy Insights. Intelligent Optimization.*

Built with Python, Streamlit, and Genetic Algorithms.

</div>
