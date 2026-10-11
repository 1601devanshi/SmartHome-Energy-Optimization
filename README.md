# SmartHome Energy Optimization Using Genetic Algorithm

## 📌 Overview

This project implements a **Genetic Algorithm (GA)** to schedule household appliances during lower-cost electricity hours. It compares a simple baseline schedule with an optimized schedule and reports estimated electricity cost, energy use, and peak load.

The project is designed as a small, understandable college-level algorithm implementation. It runs in the terminal and uses only Python's standard library.

## 🧠 How It Works

The Genetic Algorithm represents a candidate schedule as a chromosome. Each gene stores the start hour for one appliance.

The fitness function is:

`Fitness = Electricity Cost + Overload Penalty`

- **Electricity cost:** hourly power demand multiplied by the tariff for that hour.
- **Overload penalty:** a penalty is added when the total hourly load exceeds the user's preferred maximum load.
- **Lower fitness is better.**

The algorithm repeatedly applies:

1. Population initialization
2. Fitness evaluation
3. Tournament selection
4. Uniform crossover
5. Mutation
6. Elitism (preserving strong solutions)

## ✨ Features

- Includes sample household appliances to try immediately.
- Add, edit, and remove custom appliances.
- Set each appliance's power consumption, operating duration, permitted start window, and flexibility.
- Customize the 24 hourly electricity tariff rates.
- Compare an earliest-start baseline against the Genetic Algorithm schedule.
- View estimated cost difference, energy consumption, peak load, and hourly load/cost report.
- Set Genetic Algorithm population size, number of generations, preferred maximum load, and random seed.
- Uses a fixed random seed by default for repeatable demonstration results.
- No database, web server, or third-party packages required.

## 📐 Example

If a washing machine uses 0.7 kW for 2 hours, its energy requirement is:

`Energy = 0.7 kW × 2 hours = 1.4 kWh`

The scheduler considers allowed start hours and chooses a schedule with a lower fitness score according to the configured tariff and load target.

## 🛠️ Technology

- Python 3.10 or newer
- Genetic Algorithm
- Optimization and fitness evaluation
- Lists, functions, dataclasses, and random number generation

## 📂 Project Structure

```text
SmartHome-Energy-Optimization/
├── main.py
└── README.md
```

## ▶️ Running the Project

1. Install Python 3.10 or newer.
2. Download or clone this repository.
3. Open a terminal in the project folder.
4. Run:

```bash
python main.py
```

No `pip install` command is needed because the project uses only Python's standard library.

## 🚀 How to Use

1. Select **View appliances** to see the sample devices.
2. Select **Add a custom appliance** to configure your own device.
3. Edit or remove devices as required.
4. Customize hourly electricity tariffs if you want to use your own sample rates.
5. Select **Run Genetic Algorithm and compare schedules**.
6. Set the preferred maximum load and algorithm parameters.
7. Review the baseline schedule, optimized schedule, estimated cost difference, and hourly report.

## 🏠 Applications

- Home energy management simulations
- Time-of-use electricity cost optimization
- Peak-load awareness and scheduling
- Demonstration of Genetic Algorithms for optimization problems

## ⚠️ Assumptions and Limitations

- This is a software simulation; it does not connect to a smart meter or control physical appliances.
- The included electricity rates are illustrative. Replace them with appropriate local rates for a realistic demonstration.
- Appliances run continuously for the specified whole-hour duration and cannot cross midnight.
- The baseline schedules each appliance at its earliest permitted start time.
- The optimizer attempts to reduce cost and penalizes excessive simultaneous load; a feasible load target may not always be possible.
- The algorithm shifts when electricity is used; it does not inherently reduce the appliances' required energy consumption.

## 📚 Algorithm Summary

A Genetic Algorithm is a population-based optimization method inspired by natural selection. It evaluates candidate solutions, selects better candidates as parents, recombines their genes through crossover, and introduces random changes through mutation. Elitism carries the best candidate forward. In this project, each candidate is a set of appliance start times, and the objective is to find a low-cost daily schedule while discouraging peak loads.
