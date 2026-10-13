"""Smart Home Energy Scheduler using a Genetic Algorithm.

Educational simulation. It does not connect to real meters or control hardware.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

HOURS = 24
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
        if self.duration < 1 or self.duration > HOURS or self.earliest < 0 or self.earliest > 23:
            return []
        latest = min(self.latest, HOURS - self.duration)
        if self.earliest > latest:
            return []
        if not self.flexible:
            return [self.earliest]
        return list(range(self.earliest, latest + 1))


def default_appliances() -> list[Appliance]:
    return [
        Appliance("Washing Machine", 0.7, 2, 8, 17),
        Appliance("Dishwasher", 1.2, 2, 10, 21),
        Appliance("Water Heater", 2.0, 1, 5, 9),
        Appliance("Air Conditioner", 1.5, 3, 12, 19),
        Appliance("EV Charger", 3.0, 2, 0, 21),
    ]


def hour_label(hour: int) -> str:
    return "24:00" if hour == 24 else f"{hour:02d}:00"


def build_hourly_load(starts: Sequence[int], appliances: Sequence[Appliance]) -> list[float]:
    if len(starts) != len(appliances):
        raise ValueError("Every appliance must have exactly one scheduled start hour.")
    load = [0.0] * HOURS
    for start, appliance in zip(starts, appliances):
        start = int(start)
        if start not in appliance.valid_starts():
            raise ValueError(f"Invalid start hour {start} for appliance '{appliance.name}'.")
        for hour in range(start, min(HOURS, start + appliance.duration)):
            load[hour] += float(appliance.power_kw)
    return load


def normalize_solar_profile(solar_generation: Sequence[float] | None) -> list[float]:
    if solar_generation is None:
        return [0.0] * HOURS
    if len(solar_generation) != HOURS:
        raise ValueError("Solar generation profile must contain exactly 24 hourly values.")
    profile = [float(v) for v in solar_generation]
    if any(v < 0 for v in profile):
        raise ValueError("Solar generation cannot be negative.")
    return profile


def evaluate(
    starts: Sequence[int],
    appliances: Sequence[Appliance],
    tariffs: Sequence[float],
    max_load: float,
    overload_penalty: float = 25.0,
    solar_generation: Sequence[float] | None = None,
) -> dict:
    """Evaluate a schedule; lower fitness is better.

    The load limit applies to total appliance demand. Solar reduces grid imports,
    but it does not change the physical demand of the appliances.
    """
    if len(tariffs) != HOURS:
        raise ValueError("Exactly 24 hourly tariff rates are required.")
    if len(starts) != len(appliances):
        raise ValueError("Every appliance must have exactly one scheduled start hour.")
    if max_load <= 0:
        raise ValueError("Maximum hourly load must be greater than zero.")
    if any(float(rate) < 0 for rate in tariffs):
        raise ValueError("Tariff rates cannot be negative.")
    load = build_hourly_load(starts, appliances)
    solar = normalize_solar_profile(solar_generation)
    solar_used = [min(load[h], solar[h]) for h in range(HOURS)]
    grid_import = [max(0.0, load[h] - solar[h]) for h in range(HOURS)]
    solar_surplus = [max(0.0, solar[h] - load[h]) for h in range(HOURS)]
    hourly_cost = [grid_import[h] * float(tariffs[h]) for h in range(HOURS)]
    cost = sum(hourly_cost)
    overload = sum(max(0.0, value - max_load) ** 2 for value in load)
    energy = sum(float(a.power_kw) * int(a.duration) for a in appliances)
    solar_generated_kwh = sum(solar)
    solar_used_kwh = sum(solar_used)
    grid_import_kwh = sum(grid_import)
    return {
        "starts": [int(s) for s in starts],
        "load": load,
        "hourly_cost": hourly_cost,
        "cost": cost,
        "energy": energy,
        "peak": max(load, default=0.0),
        "overload": overload,
        "fitness": cost + float(overload_penalty) * overload,
        "overload_hours": sum(value > max_load for value in load),
        "max_load": float(max_load),
        "load_limit_met": all(value <= max_load + 1e-9 for value in load),
        "solar_generation": solar,
        "solar_used": solar_used,
        "solar_surplus": solar_surplus,
        "solar_generated_kwh": solar_generated_kwh,
        "solar_used_kwh": solar_used_kwh,
        "grid_import": grid_import,
        "grid_import_kwh": grid_import_kwh,
        "solar_utilization_pct": (solar_used_kwh / solar_generated_kwh * 100) if solar_generated_kwh else 0.0,
    }


def greedy_schedule(
    appliances: Sequence[Appliance],
    tariffs: Sequence[float],
    max_load: float = 5.0,
    solar_generation: Sequence[float] | None = None,
    overload_penalty: float = 25.0,
) -> dict:
    """Load-aware greedy benchmark using incremental grid cost and overload."""
    if not appliances:
        raise ValueError("Add at least one appliance first.")
    if len(tariffs) != HOURS:
        raise ValueError("Exactly 24 hourly tariff rates are required.")
    solar = normalize_solar_profile(solar_generation)
    current_load = [0.0] * HOURS
    chosen: dict[str, int] = {}
    ordered = sorted(appliances, key=lambda a: a.power_kw * a.duration, reverse=True)
    for appliance in ordered:
        domain = appliance.valid_starts()
        if not domain:
            raise ValueError(f"Invalid operating window for '{appliance.name}'.")
        def candidate_key(start: int):
            incremental_cost = 0.0
            incremental_overload = 0.0
            resulting_peak = 0.0
            for h in range(start, start + appliance.duration):
                before = current_load[h]
                after = before + appliance.power_kw
                before_grid = max(0.0, before - solar[h])
                after_grid = max(0.0, after - solar[h])
                incremental_cost += (after_grid - before_grid) * float(tariffs[h])
                incremental_overload += max(0.0, after - max_load) ** 2 - max(0.0, before - max_load) ** 2
                resulting_peak = max(resulting_peak, after)
            score = incremental_cost + overload_penalty * incremental_overload
            return (score, resulting_peak, start)
        start = min(domain, key=candidate_key)
        chosen[appliance.name] = start
        for h in range(start, start + appliance.duration):
            current_load[h] += appliance.power_kw
    starts = [chosen[a.name] for a in appliances]
    return evaluate(starts, appliances, tariffs, max_load, overload_penalty, solar)


def genetic_algorithm(
    appliances: Sequence[Appliance],
    tariffs: Sequence[float],
    max_load: float = 5.0,
    population_size: int = 80,
    generations: int = 120,
    mutation_rate: float = 0.12,
    crossover_rate: float = 0.85,
    seed: int = 42,
    solar_generation: Sequence[float] | None = None,
    overload_penalty: float = 25.0,
) -> dict:
    """Run a GA with tournament selection, uniform crossover, mutation and elitism."""
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
    domains = [a.valid_starts() for a in appliances]
    if any(not domain for domain in domains):
        raise ValueError("One or more appliances have an invalid operating window.")
    solar = normalize_solar_profile(solar_generation)
    rng = random.Random(seed)

    def random_chromosome() -> list[int]:
        return [rng.choice(domain) for domain in domains]

    def score(chromosome: Sequence[int]) -> float:
        return evaluate(chromosome, appliances, tariffs, max_load, overload_penalty, solar)["fitness"]

    def select(population: list[list[int]], scores: list[float]) -> list[int]:
        contestants = [rng.randrange(len(population)) for _ in range(3)]
        winner = min(contestants, key=lambda i: scores[i])
        return population[winner][:]

    population = [random_chromosome() for _ in range(population_size)]
    global_best = min(population, key=score)[:]
    global_best_score = score(global_best)
    history: list[float] = []
    average_history: list[float] = []
    generation_best_history: list[float] = []
    elite_count = max(1, population_size // 20)

    for _ in range(generations):
        scores = [score(chromosome) for chromosome in population]
        generation_best_score = min(scores)
        if generation_best_score < global_best_score:
            idx = scores.index(generation_best_score)
            global_best = population[idx][:]
            global_best_score = generation_best_score
        history.append(global_best_score)  # best-so-far; should never increase
        average_history.append(sum(scores) / len(scores))
        generation_best_history.append(generation_best_score)

        ranked = sorted(zip(scores, population), key=lambda item: item[0])
        next_population = [chromosome[:] for _, chromosome in ranked[:elite_count]]
        while len(next_population) < population_size:
            parent1 = select(population, scores)
            parent2 = select(population, scores)
            child1, child2 = parent1[:], parent2[:]
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

    result = evaluate(global_best, appliances, tariffs, max_load, overload_penalty, solar)
    result["history"] = history
    result["average_history"] = average_history
    result["generation_best_history"] = generation_best_history
    result["generations_processed"] = len(history)
    result["seed"] = seed
    return result
