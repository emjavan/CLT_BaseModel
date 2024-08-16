from BaseModel import EpiCompartment, TransitionVariable, OutgoingTransitionVariableGroup, \
    BaseModel, SimulationParams, EpiParams
import PlotTools
import numpy as np
import matplotlib.pyplot as plt
import time

from collections import namedtuple


def compute_new_immunity_rate(immunity_compartment,
                              immunity_increase_factor,
                              total_population_val,
                              saturation_constant):
    return immunity_increase_factor / (total_population_val *
                                        (1 + saturation_constant * immunity_compartment))


def compute_new_waned_immunity_rate(waning_factor):
    return waning_factor


def compute_new_exposed_rate(I,
                             immunity_against_inf,
                             efficacy_against_inf,
                             beta,
                             total_population_val):
    return beta * I / (
            total_population_val * (1 + efficacy_against_inf * immunity_against_inf))


def compute_new_infected_rate(sigma):
    return sigma


def compute_new_recovered_home_rate(mu, gamma):
    return (1 - mu) * gamma


def compute_new_hosp_rate(zeta,
                          mu,
                          immunity_against_hosp,
                          efficacy_against_hosp):
    return zeta * mu / (1 + efficacy_against_hosp * immunity_against_hosp)


def compute_new_recovered_hosp_rate(nu, gamma_hosp):
    return (1 - nu) * gamma_hosp


def compute_new_dead_rate(pi,
                          nu,
                          immunity_against_hosp,
                          efficacy_against_death):
    return pi * nu / (1 + efficacy_against_death * immunity_against_hosp)


def compute_new_susceptible_rate(eta):
    return eta


class ImmunoSEIRModel(BaseModel):

    def update_discretized_rates(self):

        self.new_immunity_hosp.current_rate = compute_new_immunity_rate(
            immunity_compartment=self.population_immunity_hosp.current_val,
            immunity_increase_factor=self.epi_params.immunity_hosp_increase_factor,
            total_population_val=self.epi_params.total_population_val,
            saturation_constant=self.epi_params.immunity_hosp_saturation_constant
        )

        self.new_immunity_inf.current_rate = compute_new_immunity_rate(
            immunity_compartment=self.population_immunity_inf.current_val,
            immunity_increase_factor=self.epi_params.immunity_inf_increase_factor,
            total_population_val=self.epi_params.total_population_val,
            saturation_constant=self.epi_params.immunity_inf_saturation_constant
        )

        self.new_waned_immunity_hosp.current_rate = compute_new_waned_immunity_rate(
            waning_factor=self.epi_params.waning_factor_hosp
        )

        self.new_waned_immunity_inf.current_rate = compute_new_waned_immunity_rate(
            waning_factor=self.epi_params.waning_factor_inf
        )

        self.new_exposed.current_rate = compute_new_exposed_rate(beta=self.epi_params.beta,
                                                                 I=self.I.current_val,
                                                                 immunity_against_inf=self.population_immunity_inf.current_val,
                                                                 efficacy_against_inf=self.epi_params.efficacy_immunity_inf,
                                                                 total_population_val=self.epi_params.total_population_val)

        self.new_infected.current_rate = compute_new_infected_rate(
            sigma=self.epi_params.sigma
        )

        self.new_recovered_home.current_rate = compute_new_recovered_home_rate(
            mu=self.epi_params.mu,
            gamma=self.epi_params.gamma
        )

        self.new_hosp.current_rate = compute_new_hosp_rate(
            zeta=self.epi_params.zeta,
            mu=self.epi_params.mu,
            immunity_against_hosp=self.population_immunity_hosp.current_val,
            efficacy_against_hosp=self.epi_params.efficacy_immunity_hosp
        )

        self.new_recovered_hosp.current_rate = compute_new_recovered_hosp_rate(
            nu=self.epi_params.nu,
            gamma_hosp=self.epi_params.gamma_hosp
        )

        self.new_dead.current_rate = compute_new_dead_rate(
            pi=self.epi_params.pi,
            nu=self.epi_params.nu,
            immunity_against_hosp=self.population_immunity_hosp.current_val,
            efficacy_against_death=self.epi_params.efficacy_immunity_death
        )

        self.new_susceptible.current_rate = compute_new_susceptible_rate(
            eta=self.epi_params.eta
        )

start_time = time.time()

# EpiParams and SimulationParams will eventually be read in from a file
epi_params = EpiParams()
epi_params.beta = 2
epi_params.total_population_val = np.array([int(1e6)])

epi_params.immunity_hosp_increase_factor = 0.0
epi_params.immunity_inf_increase_factor = 0.0
epi_params.immunity_hosp_saturation_constant = 0.0
epi_params.immunity_inf_saturation_constant = 0.0
epi_params.waning_factor_hosp = 0.0
epi_params.waning_factor_inf = 0.0
epi_params.efficacy_immunity_hosp = 0.0
epi_params.efficacy_immunity_inf = 0.0
epi_params.efficacy_immunity_death = 0.0

# R to S rate
epi_params.eta = 0.1

# E to I rate
epi_params.sigma = 0.5

# (Conditional) proportion who go to hospital
epi_params.mu = 0.5

# I to R rate
epi_params.gamma = 0.1

# I to H rate
epi_params.zeta = 0.25

# H to R rate
epi_params.gamma_hosp = 0.17

# H to D rate
epi_params.pi = .17

# (Conditional) proportion who die
epi_params.nu = .03

simulation_params = SimulationParams(timesteps_per_day=7)

print(time.time() - start_time)

start_time = time.time()

simple_model = ImmunoSEIRModel(epi_params,
                               simulation_params)

simple_model.add_epi_compartment("S", np.array([int(1e6) - 2e4]), ["new_susceptible"], ["new_exposed"])
simple_model.add_epi_compartment("E", np.array([1e4]), ["new_exposed"], ["new_infected"])
simple_model.add_epi_compartment("I", np.array([1e4]), ["new_infected"], ["new_recovered_home", "new_hosp"])
simple_model.add_epi_compartment("H", np.array([0.0]), ["new_hosp"], ["new_recovered_hosp", "new_dead"])
simple_model.add_epi_compartment("R", np.array([0.0]), ["new_recovered_home", "new_recovered_hosp"], ["new_susceptible"])
simple_model.add_epi_compartment("D", np.array([0.0]), ["new_dead"], [])

simple_model.add_epi_compartment("population_immunity_hosp",
                                 np.array([0.0]),
                                 ["new_immunity_hosp"],
                                 ["new_waned_immunity_hosp"],
                                 False)

simple_model.add_epi_compartment("population_immunity_inf",
                                 np.array([0.0]),
                                 ["new_immunity_inf"],
                                 ["new_waned_immunity_inf"],
                             False)

simple_model.add_transition_variable("new_susceptible", "binomial", simple_model.R)
simple_model.add_transition_variable("new_exposed", "binomial", simple_model.S)
simple_model.add_transition_variable("new_infected", "binomial", simple_model.E)
simple_model.add_transition_variable("new_recovered_home", "binomial", simple_model.I, True)
simple_model.add_transition_variable("new_hosp", "binomial", simple_model.I, True)
simple_model.add_transition_variable("new_recovered_hosp", "binomial", simple_model.H, True)
simple_model.add_transition_variable("new_dead", "binomial", simple_model.H, True)

simple_model.add_transition_variable("new_immunity_hosp", "binomial", simple_model.population_immunity_hosp)
simple_model.add_transition_variable("new_waned_immunity_hosp", "binomial", simple_model.population_immunity_hosp)

simple_model.add_transition_variable("new_immunity_inf", "binomial", simple_model.population_immunity_inf)
simple_model.add_transition_variable("new_waned_immunity_inf", "binomial", simple_model.population_immunity_inf)

simple_model.add_outgoing_transition_variable_group("I_out", simple_model.I, [simple_model.new_recovered_home, simple_model.new_hosp])
simple_model.add_outgoing_transition_variable_group("H_out", simple_model.H, [simple_model.new_recovered_hosp, simple_model.new_dead])

simple_model.simulate_until_time_period(last_simulation_day=100)

print(time.time() - start_time)

breakpoint()

PlotTools.create_basic_compartment_history_plot(simple_model)