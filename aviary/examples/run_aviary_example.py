"""
This is a slightly more complex Aviary example of running a coupled aircraft design-mission optimization.
It runs the same mission as the `run_basic_aviary_example.py` script, but it uses the AviaryProblem class to set up the problem.
This exposes more options and flexibility to the user and uses the "Level 2" API within Aviary.

We define a `phase_info` object, which tells Aviary how to model the mission.
Here we have climb, cruise, and descent phases.
We then call the correct methods in order to set up and run an Aviary optimization problem.
This performs a coupled design-mission optimization and outputs the results from Aviary into the `reports` folder.
"""
import aviary.api as av
from example_phase_info import phase_info
# phase_info['pre_mission']['include_takeoff'] = True

prob = av.AviaryProblem()

# Load aircraft and options data from user
# Allow for user overrides here
prob.load_inputs('models/test_aircraft/aircraft_for_bench_FwFm.csv', phase_info)

# Preprocess inputs
prob.check_and_preprocess_inputs()

prob.add_pre_mission_systems()

prob.add_phases()

prob.add_post_mission_systems()

# Link phases and variables
prob.link_phases()

prob.add_driver("SLSQP", max_iter=100)

prob.add_design_variables()

# Load optimization problem formulation
# Detail which variables the optimizer can control
prob.add_objective()

prob.setup()

prob.set_initial_guesses()

prob.run_aviary_problem()

print(f'Range = {prob.get_val(av.Mission.Summary.RANGE)}')
print(f"Fuel mass = {prob.get_val(av.Mission.Design.FUEL_MASS, units='lbm')}")
print(f'Total fuel mass = {prob.get_val(av.Mission.Summary.TOTAL_FUEL_MASS)}')
print(f'Empty mass = {prob.get_val(av.Aircraft.Design.OPERATING_MASS)}')
print(f'Payload mass = {prob.get_val(av.Aircraft.CrewPayload.TOTAL_PAYLOAD_MASS)}')
print(f'Design Gross mass = {prob.get_val(av.Mission.Design.GROSS_MASS)}')
print(f'Summary Gross mass = {prob.get_val(av.Mission.Summary.GROSS_MASS)}')
