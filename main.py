"""Smart Home Energy Scheduler Using Genetic Algorithm.

A small, college-level command-line project. It uses a Genetic Algorithm to
schedule flexible home appliances during lower-tariff hours while discouraging
excessive simultaneous electricity demand. No third-party packages required.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

HOURS = 24

# Illustrative hourly rates in Indian rupees per kWh. Replace with local rates.
DEFAULT_TARIFF = [
    5.0, 4.8, 4.6, 4.5, 4.5, 4.8, 5.5, 6.5,
    7.0, 7.5, 7.2, 6.8, 6.5, 6.2, 6.5, 7.0,
    7.8, 8.5, 9.0, 9.0, 8.2, 7.0, 6.0, 5.5,
]


@dataclass
class Appliance:
    name: str
    power_kw: float
    duration: int
    earliest: int
    latest: int
    flexible: bool = True

    def valid_starts(self) -> list[int]:
        latest = min(self.latest, HOURS - self.duration)
        if self.duration < 1 or self.duration > HOURS or self.earliest < 0:
            return []
        if self.earliest > latest:
            return []
        if not self.flexible:
            return [self.earliest] if self.earliest <= latest else []
        return list(range(self.earliest, latest + 1))


def hour_label(hour: int) -> str:
    return "24:00" if hour == 24 else f"{hour:02d}:00"


def ask_int(prompt: str, minimum: int, maximum: int, default: int | None = None) -> int:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt} ({minimum}-{maximum}){suffix}: ").strip()
        if not raw and default is not None:
            return default
        try:
            value = int(raw)
            if minimum <= value <= maximum:
                return value
        except ValueError:
            pass
        print(f"Please enter a whole number from {minimum} to {maximum}.")


def ask_float(prompt: str, minimum: float, default: float | None = None) -> float:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw and default is not None:
            return default
        try:
            value = float(raw)
            if value >= minimum:
                return value
        except ValueError:
            pass
        print(f"Please enter a number greater than or equal to {minimum}.")


def default_appliances() -> list[Appliance]:
    return [
        Appliance("Washing Machine", 0.7, 2, 8, 17),
        Appliance("Dishwasher", 1.2, 2, 10, 21),
        Appliance("Water Heater", 2.0, 1, 5, 9),
        Appliance("Air Conditioner", 1.5, 3, 12, 19),
        Appliance("EV Charger", 3.0, 2, 0, 21),
    ]


def add_appliance(appliances: list[Appliance]) -> None:
    print("\nAdd a custom appliance")
    name = input("Appliance name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    if any(a.name.lower() == name.lower() for a in appliances):
        print("An appliance with that name already exists.")
        return
    power = ask_float("Power consumption in kW (e.g. 750 W = 0.75 kW)", 0.01)
    duration = ask_int("Operating duration in hours", 1, 24)
    earliest = ask_int("Earliest permitted start hour (24-hour clock)", 0, 23)
    latest = ask_int("Latest permitted start hour (24-hour clock)", earliest, 23)
    flexible_answer = input("Can the algorithm shift its start time? [Y/n]: ").strip().lower()
    appliance = Appliance(name, power, duration, earliest, latest, flexible_answer not in {"n", "no"})
    if not appliance.valid_starts():
        print("Those settings are not feasible. The run duration must fit before midnight.")
        return
    appliances.append(appliance)
    print(f"Added {name}.")


def show_appliances(appliances: Sequence[Appliance]) -> None:
    print("\nAPPLIANCE CONFIGURATION")
    print("-" * 94)
    print(f"{'#':<3} {'Appliance':<22} {'Power (kW)':>11} {'Duration':>10} {'Allowed start window':>22} {'Flexible':>10}")
    print("-" * 94)
    for i, a in enumerate(appliances, 1):
        print(f"{i:<3} {a.name[:21]:<22} {a.power_kw:>11.2f} {a.duration:>8} h {hour_label(a.earliest)}–{hour_label(a.latest):<15} {('Yes' if a.flexible else 'No'):>8}")
    print("-" * 94)


def edit_appliance(appliances: list[Appliance]) -> None:
    if not appliances:
        print("No appliances to edit.")
        return
    show_appliances(appliances)
    index = ask_int("Select appliance number to edit", 1, len(appliances)) - 1
    old = appliances[index]
    print("Press Enter to keep the current value.")
    name = input(f"Name [{old.name}]: ").strip() or old.name
    power = ask_float(f"Power in kW [{old.power_kw}]", 0.01, old.power_kw)
    duration = ask_int("Duration in hours", 1, 24, old.duration)
    earliest = ask_int("Earliest start hour", 0, 23, old.earliest)
    latest = ask_int("Latest start hour", earliest, 23, max(old.latest, earliest))
    flex_text = input(f"Flexible? [Y/n, current {'yes' if old.flexible else 'no'}]: ").strip().lower()
    flexible = old.flexible if not flex_text else flex_text not in {"n", "no"}
    edited = Appliance(name, power, duration, earliest, latest, flexible)
    if not edited.valid_starts():
        print("Edit not saved: these settings do not form a valid schedule window.")
        return
    if any(i != index and a.name.lower() == name.lower() for i, a in enumerate(appliances)):
        print("Edit not saved: appliance names must be unique.")
        return
    appliances[index] = edited
    print("Appliance updated.")


def remove_appliance(appliances: list[Appliance]) -> None:
    if not appliances:
        print("No appliances to remove.")
        return
    show_appliances(appliances)
    index = ask_int("Select appliance number to remove", 1, len(appliances)) - 1
    removed = appliances.pop(index)
    print(f"Removed {removed.name}.")


def set_tariffs(tariffs: list[float]) -> None:
    print("\nHOURLY ELECTRICITY TARIFFS")
    print("Rates are in ₹ per kWh. Enter a new rate, or press Enter to keep the current rate.")
    for hour in range(HOURS):
        while True:
            raw = input(f"{hour_label(hour)}  ₹{tariffs[hour]:.2f} [{tariffs[hour]:.2f}]: ").strip()
            if not raw:
                break
            try:
                value = float(raw)
                if value >= 0:
                    tariffs[hour] = value
                    break
            except ValueError:
                pass
            print("Enter a non-negative number.")


def build_hourly_load(starts: Sequence[int], appliances: Sequence[Appliance]) -> list[float]:
    load = [0.0] * HOURS
    for start, appliance in zip(starts, appliances):
        for hour in range(start, min(HOURS, start + appliance.duration)):
            load[hour] += appliance.power_kw
    return load


def evaluate(starts: Sequence[int], appliances: Sequence[Appliance], tariffs: Sequence[float], max_load: float, overload_penalty: float = 25.0) -> dict:
    """Evaluate a schedule; reject invalid genes rather than silently truncating them."""
    if len(tariffs) != HOURS:
        raise ValueError("Exactly 24 hourly tariff rates are required.")
    if len(starts) != len(appliances):
        raise ValueError("Every appliance must have exactly one scheduled start hour.")
    if max_load <= 0:
        raise ValueError("Maximum hourly load must be greater than zero.")
    if any(float(rate) < 0 for rate in tariffs):
        raise ValueError("Tariff rates cannot be negative.")
    for start, appliance in zip(starts, appliances):
        if int(start) not in appliance.valid_starts():
            raise ValueError(f"Invalid start hour {start} for appliance '{appliance.name}'.")
    load = build_hourly_load(starts, appliances)
    hourly_cost = [load[h] * tariffs[h] for h in range(HOURS)]
    cost = sum(hourly_cost)
    overload = sum(max(0.0, value - max_load) ** 2 for value in load)
    energy = sum(a.power_kw * a.duration for a in appliances)
    return {
        "starts": list(starts), "load": load, "hourly_cost": hourly_cost,
        "cost": cost, "energy": energy, "peak": max(load, default=0.0),
        "overload": overload, "fitness": cost + overload_penalty * overload,
        "overload_hours": sum(value > max_load for value in load),
        "max_load": max_load,
        "load_limit_met": all(value <= max_load for value in load),
    }


def greedy_schedule(appliances: Sequence[Appliance], tariffs: Sequence[float], max_load: float = 5.0) -> dict:
    """Construct a simple tariff-aware comparison schedule, choosing the cheapest valid start per appliance."""
    if len(tariffs) != HOURS:
        raise ValueError("Exactly 24 hourly tariff rates are required.")
    starts: list[int] = []
    for appliance in sorted(appliances, key=lambda item: item.power_kw * item.duration, reverse=True):
        domain = appliance.valid_starts()
        if not domain:
            raise ValueError(f"Invalid operating window for '{appliance.name}'.")
        # Select the start with lowest incremental cost; break ties using lower resulting peak load.
        def candidate_key(start: int):
            trial = starts + [start]
            partial_appliances = list(appliances[:len(starts)])  # only used as a deterministic tie fallback
            cost = sum(appliance.power_kw * tariffs[h] for h in range(start, start + appliance.duration))
            peak = appliance.power_kw
            return (cost, peak, start)
        starts.append(min(domain, key=candidate_key))
    # The sorted construction order differs from the original appliance order, so map by identity/name.
    scheduled_by_name = {a.name: start for a, start in zip(
        sorted(appliances, key=lambda item: item.power_kw * item.duration, reverse=True), starts
    )}
    return evaluate([scheduled_by_name[a.name] for a in appliances], appliances, tariffs, max_load)


def genetic_algorithm(appliances: Sequence[Appliance], tariffs: Sequence[float], max_load: float = 5.0,
                      population_size: int = 80, generations: int = 120, mutation_rate: float = 0.12,
                      crossover_rate: float = 0.85, seed: int = 42) -> dict:
    """Optimize appliance start times with selection, crossover, mutation and elitism."""
    domains = [a.valid_starts() for a in appliances]
    if not appliances:
        raise ValueError("Add at least one appliance first.")
    if len(tariffs) != HOURS:
        raise ValueError("Exactly 24 hourly tariff rates are required.")
    if population_size < 4:
        raise ValueError("Population size must be at least 4.")
    if generations < 1:
        raise ValueError("Generations must be at least 1.")
    if not 0 <= mutation_rate <= 1 or not 0 <= crossover_rate <= 1:
        raise ValueError("Mutation and crossover probabilities must be between 0 and 1.")
    if max_load <= 0:
        raise ValueError("Maximum hourly load must be greater than zero.")
    if any(not domain for domain in domains):
        raise ValueError("One or more appliances have an invalid operating window.")
    rng = random.Random(seed)

    def random_chromosome() -> list[int]:
        return [rng.choice(domain) for domain in domains]

    def score(chromosome: Sequence[int]) -> float:
        return evaluate(chromosome, appliances, tariffs, max_load)["fitness"]

    def select(population: list[list[int]], scores: list[float]) -> list[int]:
        candidates = [rng.randrange(len(population)) for _ in range(3)]
        winner = min(candidates, key=lambda i: scores[i])
        return population[winner][:]

    population = [random_chromosome() for _ in range(population_size)]
    best = min(population, key=score)[:]
    best_score = score(best)
    history: list[float] = []

    for _ in range(generations):
        scores = [score(chromosome) for chromosome in population]
        best_index = min(range(len(population)), key=lambda i: scores[i])
        if scores[best_index] < best_score:
            best, best_score = population[best_index][:], scores[best_index]
        history.append(best_score)
        ranked = sorted(zip(scores, population), key=lambda item: item[0])
        next_population = [chromosome[:] for _, chromosome in ranked[:max(1, population_size // 20)]]
        while len(next_population) < population_size:
            p1, p2 = select(population, scores), select(population, scores)
            child1, child2 = p1[:], p2[:]
            if len(appliances) > 1 and rng.random() < crossover_rate:
                for gene in range(len(appliances)):
                    if rng.random() < 0.5:
                        child1[gene], child2[gene] = child2[gene], child1[gene]
            for child in (child1, child2):
                for gene, domain in enumerate(domains):
                    if rng.random() < mutation_rate:
                        child[gene] = rng.choice(domain)
                next_population.append(child)
                if len(next_population) >= population_size:
                    break
        population = next_population

    result = evaluate(best, appliances, tariffs, max_load)
    result["history"] = history
    return result


def print_schedule(title: str, result: dict, appliances: Sequence[Appliance]) -> None:
    print(f"\n{title}")
    print("-" * 78)
    print(f"{'Appliance':<24} {'Start':>9} {'End':>9} {'Power':>10} {'Energy':>10}")
    print("-" * 78)
    for appliance, start in zip(appliances, result["starts"]):
        print(f"{appliance.name[:23]:<24} {hour_label(start):>9} {hour_label(start + appliance.duration):>9} {appliance.power_kw:>8.2f} kW {appliance.power_kw * appliance.duration:>7.2f} kWh")
    print("-" * 78)
    print(f"Daily energy: {result['energy']:.2f} kWh | Estimated cost: ₹{result['cost']:.2f} | Peak load: {result['peak']:.2f} kW")


def print_hourly_report(result: dict, tariffs: Sequence[float], max_load: float) -> None:
    print("\nHOURLY LOAD AND COST REPORT")
    print("Hour     Tariff (₹/kWh)    Load (kW)    Cost (₹)    Load status")
    print("-" * 69)
    for hour in range(HOURS):
        load = result["load"][hour]
        status = "OVER TARGET" if load > max_load else "OK"
        print(f"{hour_label(hour):<8} {tariffs[hour]:>10.2f} {load:>15.2f} {result['hourly_cost'][hour]:>11.2f}    {status}")


def main() -> None:
    appliances = default_appliances()
    tariffs = DEFAULT_TARIFF[:]
    print("=" * 68)
    print(" SMART HOME ENERGY SCHEDULER USING GENETIC ALGORITHM")
    print(" College Project | Python | Command-line application")
    print("=" * 68)
    print("Goal: schedule flexible appliances in lower-cost hours while limiting peak load.")

    while True:
        print("\nMAIN MENU")
        print("1. View appliances")
        print("2. Add a custom appliance")
        print("3. Edit an appliance")
        print("4. Remove an appliance")
        print("5. Customize hourly electricity tariffs")
        print("6. Run Genetic Algorithm and compare schedules")
        print("7. Exit")
        choice = input("Choose an option (1-7): ").strip()

        if choice == "1":
            show_appliances(appliances)
        elif choice == "2":
            add_appliance(appliances)
        elif choice == "3":
            edit_appliance(appliances)
        elif choice == "4":
            remove_appliance(appliances)
        elif choice == "5":
            set_tariffs(tariffs)
        elif choice == "6":
            if not appliances:
                print("Add at least one appliance before running the algorithm.")
                continue
            invalid = [a.name for a in appliances if not a.valid_starts()]
            if invalid:
                print("Invalid operating windows: " + ", ".join(invalid))
                continue
            max_load = ask_float("Preferred maximum simultaneous load in kW", 0.1, 5.0)
            population_size = ask_int("Genetic Algorithm population size", 10, 500, 80)
            generations = ask_int("Number of generations", 10, 1000, 120)
            seed = ask_int("Random seed (repeatable results)", 0, 1_000_000, 42)
            baseline_starts = [a.valid_starts()[0] for a in appliances]
            baseline = evaluate(baseline_starts, appliances, tariffs, max_load)
            optimized = genetic_algorithm(appliances, tariffs, max_load, population_size, generations, seed=seed)
            print_schedule("BASELINE SCHEDULE (earliest allowed start)", baseline, appliances)
            print_schedule("OPTIMIZED SCHEDULE (Genetic Algorithm)", optimized, appliances)
            savings = baseline["cost"] - optimized["cost"]
            percentage = (savings / baseline["cost"] * 100) if baseline["cost"] else 0.0
            print("\nOPTIMIZATION SUMMARY")
            print(f"Baseline electricity cost : ₹{baseline['cost']:.2f}")
            print(f"Optimized electricity cost: ₹{optimized['cost']:.2f}")
            print(f"Estimated cost difference : ₹{savings:.2f} ({percentage:.2f}%)")
            print(f"Baseline peak load        : {baseline['peak']:.2f} kW")
            print(f"Optimized peak load       : {optimized['peak']:.2f} kW")
            print(f"Generations processed     : {len(optimized['history'])}")
            print(f"Best fitness at start/end : {optimized['history'][0]:.2f} / {optimized['history'][-1]:.2f}")
            print_hourly_report(optimized, tariffs, max_load)
            input("\nPress Enter to return to the main menu...")
        elif choice == "7":
            print("Thank you for using Smart Home Energy Scheduler. Goodbye!")
            break
        else:
            print("Invalid option. Please choose a number from 1 to 7.")


if __name__ == "__main__":
    main()
