import warnings

import numpy as np
import openmdao.api as om

from aviary.utils.aviary_values import AviaryValues
from aviary.utils.named_values import get_keys
from aviary.variable_info.variable_meta_data import _MetaData
from aviary.variable_info.variables import Aircraft, Mission
from aviary.utils.test_utils.variable_test import get_names_from_hierarchy
from aviary.variable_info.variable_meta_data import _MetaData as BaseMetaData


def preprocess_options(aviary_options: AviaryValues, **kwargs):
    """
    Run all preprocessors on provided AviaryValues object

    Parameters
    ----------
    aviary_options : AviaryValues
        Options to be updated
    """
    try:
        engine_models = kwargs['engine_models']
    except KeyError:
        engine_models = None

    preprocess_crewpayload(aviary_options)
    preprocess_propulsion(aviary_options, engine_models)


def preprocess_crewpayload(aviary_options: AviaryValues):
    """
    Calculates option values that are derived from other options, and are not direct inputs.
    This function modifies the entries in the supplied collection, and for convenience also
    returns the modified collection.
    """

    # Check which values were received from user input
    user_input_num_pax = False
    user_input_design_num_pax = False
    user_input_1TB = False
    user_input_design_1TB = False

    if Aircraft.CrewPayload.NUM_PASSENGERS in aviary_options:
        user_input_num_pax = True
        print('NUM_PASSENGERS', aviary_options.get_val(
            Aircraft.CrewPayload.NUM_PASSENGERS))
    if Aircraft.CrewPayload.Design.NUM_PASSENGERS in aviary_options:
        user_input_design_num_pax = True
        print('Design.NUM_PASSENGERS', aviary_options.get_val(
            Aircraft.CrewPayload.Design.NUM_PASSENGERS))
    if Aircraft.CrewPayload.NUM_FIRST_CLASS in aviary_options or \
        Aircraft.CrewPayload.NUM_BUSINESS_CLASS in aviary_options or \
            Aircraft.CrewPayload.NUM_TOURIST_CLASS in aviary_options:
        user_input_1TB = True
    if Aircraft.CrewPayload.Design.NUM_FIRST_CLASS in aviary_options or \
        Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS in aviary_options or \
            Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS in aviary_options:
        user_input_design_1TB = True

    print('user_input_num_pax', user_input_num_pax)
    print('user_input_design_num_pax', user_input_design_num_pax)
    print('user_input_1TB', user_input_1TB)
    print('user_input_design_1TB', user_input_design_1TB)

    # Grab Default values for 1TB (1st class, Tourist Class, Business Class Passengers) to make
    #   sure they are accessible so we don't have to run checks if they exist again
    if user_input_1TB:
        if Aircraft.CrewPayload.NUM_FIRST_CLASS not in aviary_options:
            aviary_options.set_val(Aircraft.CrewPayload.NUM_FIRST_CLASS,
                                   BaseMetaData[Aircraft.CrewPayload.NUM_FIRST_CLASS]['default_value'])
        if Aircraft.CrewPayload.NUM_BUSINESS_CLASS not in aviary_options:
            aviary_options.set_val(Aircraft.CrewPayload.NUM_BUSINESS_CLASS,
                                   BaseMetaData[Aircraft.CrewPayload.NUM_BUSINESS_CLASS]['default_value'])
        if Aircraft.CrewPayload.NUM_TOURIST_CLASS not in aviary_options:
            aviary_options.set_val(Aircraft.CrewPayload.NUM_TOURIST_CLASS,
                                   BaseMetaData[Aircraft.CrewPayload.NUM_TOURIST_CLASS]['default_value'])
    if user_input_design_1TB:
        if Aircraft.CrewPayload.Design.NUM_FIRST_CLASS not in aviary_options:
            aviary_options.set_val(Aircraft.CrewPayload.Design.NUM_FIRST_CLASS,
                                   BaseMetaData[Aircraft.CrewPayload.Design.NUM_FIRST_CLASS]['default_value'])
        if Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS not in aviary_options:
            aviary_options.set_val(Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS,
                                   BaseMetaData[Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS]['default_value'])
        if Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS not in aviary_options:
            aviary_options.set_val(Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS,
                                   BaseMetaData[Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS]['default_value'])

    # Sum passenger Counts for later checks and assignments
    passenger_count = 0
    for key in (Aircraft.CrewPayload.NUM_FIRST_CLASS,
                Aircraft.CrewPayload.NUM_BUSINESS_CLASS,
                Aircraft.CrewPayload.NUM_TOURIST_CLASS):
        if key in aviary_options:
            passenger_count += aviary_options.get_val(key)
    design_passenger_count = 0
    for key in (Aircraft.CrewPayload.Design.NUM_FIRST_CLASS,
                Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS,
                Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS):
        if key in aviary_options:
            design_passenger_count += aviary_options.get_val(key)

    # Create summary data if it was not assigned by the user originally
    if user_input_num_pax is False and user_input_1TB is True:
        aviary_options.set_val(Aircraft.CrewPayload.NUM_PASSENGERS, passenger_count)
        user_input_num_pax = True
    if user_input_design_1TB and not user_input_design_num_pax:
        print('setting Design.NUM_PASSENGERS')
        aviary_options.set_val(
            Aircraft.CrewPayload.Design.NUM_PASSENGERS, design_passenger_count)
        user_input_design_num_pax = True

    # Fail if incorrect data sets were provided:
    if user_input_num_pax and user_input_design_1TB and not user_input_1TB:
        raise om.AnalysisError(
            f"ERROR: In preprocessor.py: User must specify CrewPayload.FIRST_CLASS, CrewPayload.NUM_BUSINESS_CLASS, Design.NUM_TOURIST_CLASS in aviary_values.")
    if user_input_design_num_pax and user_input_1TB and not user_input_design_1TB:
        raise om.AnalysisError(
            f"ERROR: In preprocessor.py: User must specify Design.FIRST_CLASS, Design.NUM_BUSINESS_CLASS, Design.NUM_TOURIST_CLASS in aviary_values.")

    # Check summary data against individual data if individual data was entered
    if user_input_1TB is True and aviary_options.get_val(Aircraft.CrewPayload.NUM_PASSENGERS) != passenger_count:
        raise om.AnalysisError(
            f"ERROR: In preprocesssors.py: NUM_PASSENGERS ({aviary_options.get_val(Aircraft.CrewPayload.NUM_PASSENGERS)}) does not equal the sum of first class + business class + tourist class passengers (total of {passenger_count}).")
    if user_input_design_1TB is True and aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_PASSENGERS) != design_passenger_count:
        raise om.AnalysisError(
            f"ERROR: In preprocesssors.py: Design.NUM_PASSENGERS ({aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_PASSENGERS)}) does not equal the sum of design first class + business class + tourist class passengers (total of {design_passenger_count}).")

    # Copy data over if only one set of data exists
    if user_input_1TB and not (user_input_design_num_pax and user_input_design_1TB):
        aviary_options.set_val(Aircraft.CrewPayload.Design.NUM_FIRST_CLASS,
                               aviary_options.get_val(Aircraft.CrewPayload.NUM_FIRST_CLASS))
        aviary_options.set_val(Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS,
                               aviary_options.get_val(Aircraft.CrewPayload.NUM_BUSINESS_CLASS))
        aviary_options.set_val(Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS,
                               aviary_options.get_val(Aircraft.CrewPayload.NUM_TOURIST_CLASS))
        user_input_design_1TB = True
    if user_input_num_pax and not user_input_design_num_pax:
        aviary_options.set_val(Aircraft.CrewPayload.Design.NUM_PASSENGERS,
                               aviary_options.get_val(Aircraft.CrewPayload.NUM_PASSENGERS))
        user_input_design_num_pax = True
    if user_input_design_1TB and not (user_input_num_pax and user_input_1TB):
        aviary_options.set_val(Aircraft.CrewPayload.NUM_FIRST_CLASS, aviary_options.get_val(
            Aircraft.CrewPayload.Design.NUM_FIRST_CLASS))
        aviary_options.set_val(Aircraft.CrewPayload.NUM_BUSINESS_CLASS, aviary_options.get_val(
            Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS))
        aviary_options.set_val(Aircraft.CrewPayload.NUM_TOURIST_CLASS, aviary_options.get_val(
            Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS))
        user_input_1TB = True
    if user_input_design_num_pax and not user_input_num_pax:
        aviary_options.set_val(Aircraft.CrewPayload.NUM_PASSENGERS, aviary_options.get_val(
            Aircraft.CrewPayload.Design.NUM_PASSENGERS))
        user_input_num_pax = True

    # Performe checks on the final data tables to ensure data is accurate
    if user_input_design_num_pax and user_input_num_pax:
        if aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_PASSENGERS) < aviary_options.get_val(Aircraft.CrewPayload.NUM_PASSENGERS):
            raise om.AnalysisError(
                f"ERROR: In preprocesssors.py: NUM_PASSENGERS ({aviary_options.get_val(Aircraft.CrewPayload.NUM_PASSENGERS)}) is larger than the number of seats set by Design.NUM_PASSENGERS ({aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_PASSENGERS)}) .")
    if user_input_1TB and user_input_design_1TB:
        if aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_FIRST_CLASS) < aviary_options.get_val(Aircraft.CrewPayload.NUM_FIRST_CLASS):
            raise om.AnalysisError(
                f"ERROR: In preprocesssors.py: NUM_FIRST_CLASS ({aviary_options.get_val(Aircraft.CrewPayload.NUM_FIRST_CLASS)}) is larger than the number of seats set by Design.NUM_FIRST_CLASS ({aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_FIRST_CLASS)}) .")
        if aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS) < aviary_options.get_val(Aircraft.CrewPayload.NUM_BUSINESS_CLASS):
            raise om.AnalysisError(
                f"ERROR: In preprocesssors.py: NUM_BUSINESS_CLASS ({aviary_options.get_val(Aircraft.CrewPayload.NUM_BUSINESS_CLASS)}) is larger than the number of seats set by Design.NUM_BUSINESS_CLASS ({aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS)}) .")
        if aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS) < aviary_options.get_val(Aircraft.CrewPayload.NUM_TOURIST_CLASS):
            raise om.AnalysisError(
                f"ERROR: In preprocesssors.py: NUM_TOURIST_CLASS ({aviary_options.get_val(Aircraft.CrewPayload.NUM_TOURIST_CLASS)}) is larger than the number of seats set by Design.NUM_TOURIST_CLASS ({aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS)}) .")

        # fail

        # # Assign NUM_Passengers if it's not assigned
        # if Aircraft.CrewPayload.NUM_PASSENGERS not in aviary_options:
        #     aviary_options.set_val(
        #         Aircraft.CrewPayload.NUM_PASSENGERS, passenger_count)
        # else:
        #     # we only do this if the values don't match AND at least one of the first/buisness/tourist passenger counts has been set
        #     if passenger_count > 0 and aviary_options.get_val(Aircraft.CrewPayload.NUM_PASSENGERS) != passenger_count:
        #         raise om.AnalysisError(
        #             f"ERROR: In preprocesssors.py: NUM_PASSENGERS ({aviary_options.get_val(Aircraft.CrewPayload.NUM_PASSENGERS)}) does not equal the sum of first class + business class + tourist class passengers (total of {passenger_count}).")

        # # Check if any Design.NUM_ values exist, if non of them exist, assign all values
        # # if any of them do exist, don't over-write anything
        # if Aircraft.CrewPayload.Design.NUM_PASSENGERS not in aviary_options and \
        #     Aircraft.CrewPayload.Design.NUM_FIRST_CLASS not in aviary_options and \
        #         Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS not in aviary_options and \
        # Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS not in aviary_options:
        #     for key in ([Aircraft.CrewPayload.NUM_PASSENGERS, Aircraft.CrewPayload.Design.NUM_PASSENGERS],
        #                 [Aircraft.CrewPayload.NUM_FIRST_CLASS,
        #                     Aircraft.CrewPayload.Design.NUM_FIRST_CLASS],
        #                 [Aircraft.CrewPayload.NUM_BUSINESS_CLASS,
        #                     Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS],
        #                 [Aircraft.CrewPayload.NUM_TOURIST_CLASS, Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS]):
        #         if key[0] in aviary_options:
        #             aviary_options.set_val(
        #                 key[1], aviary_options.get_val(key[0]))

        # # if the user has specified Design.NUM_
        # if Aircraft.CrewPayload.NUM_PASSENGERS not in aviary_options and \
        #     Aircraft.CrewPayload.NUM_FIRST_CLASS not in aviary_options and \
        #         Aircraft.CrewPayload.NUM_BUSINESS_CLASS not in aviary_options and \
        # Aircraft.CrewPayload.NUM_TOURIST_CLASS not in aviary_options:
        #     for key in ([Aircraft.CrewPayload.NUM_PASSENGERS, Aircraft.CrewPayload.Design.NUM_PASSENGERS],
        #                 [Aircraft.CrewPayload.NUM_FIRST_CLASS,
        #                     Aircraft.CrewPayload.Design.NUM_FIRST_CLASS],
        #                 [Aircraft.CrewPayload.NUM_BUSINESS_CLASS,
        #                     Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS],
        #                 [Aircraft.CrewPayload.NUM_TOURIST_CLASS, Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS]):
        #         if key[1] in aviary_options:
        #             aviary_options.set_val(
        #                 key[0], aviary_options.get_val(key[1]))

        # # Assign Design.NUM_Passengers if it hasn't been set yet
        # if Aircraft.CrewPayload.Design.NUM_PASSENGERS not in aviary_options:
        #     aviary_options.set_val(
        #         Aircraft.CrewPayload.NUM_PASSENGERS, design_passenger_count)
        # else:
        #     # we only do this if the values don't match AND at least one of the first/buisness/tourist passenger counts has been set
        #     if design_passenger_count > 0 and aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_PASSENGERS) != design_passenger_count:
        #         raise om.AnalysisError(
        #             f"ERROR: In preprocesssors.py: Design.NUM_PASSENGERS ({aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_PASSENGERS)}) does not equal the sum of design first class + business class + tourist class passengers (total of {design_passenger_count}).")

        # # Check the individual seat assignments if they exist and error if more passengers have been assigned to that group than seats:
        # if aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_PASSENGERS) < aviary_options.get_val(Aircraft.CrewPayload.NUM_PASSENGERS):
        #     raise om.AnalysisError(
        #         f"ERROR: In preprocessor.py: More passengers assigned to aircraft than seats. Design.NUM_PASSENGERS < NUM_PASSENGERS."
        #     )

        # if Aircraft.CrewPayload.Design.NUM_FIRST_CLASS in aviary_options and Aircraft.CrewPayload.NUM_FIRST_CLASS in aviary_options:
        #     if aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_FIRST_CLASS) < aviary_options.get_val(Aircraft.CrewPayload.NUM_FIRST_CLASS):
        #         raise om.AnalysisError(
        #             f"ERROR: In preprocessor.py: More passengers assigned to first class than seats. Design.NUM_FIRST_CLASS < NUM_FIRST_CLASS."
        #         )

        # if Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS in aviary_options and Aircraft.CrewPayload.NUM_BUSINESS_CLASS in aviary_options:
        #     if aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_BUSINESS_CLASS) < aviary_options.get_val(Aircraft.CrewPayload.NUM_BUSINESS_CLASS):
        #         raise om.AnalysisError(
        #             f"ERROR: In preprocessor.py: More passengers assigned to business class than seats. Design.NUM_BUSINESS_CLASS < NUM_BUSINESS_CLASS."
        #         )

        # if Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS in aviary_options and Aircraft.CrewPayload.NUM_TOURIST_CLASS in aviary_options:
        #     if aviary_options.get_val(Aircraft.CrewPayload.Design.NUM_TOURIST_CLASS) < aviary_options.get_val(Aircraft.CrewPayload.NUM_TOURIST_CLASS):
        #         raise om.AnalysisError(
        #             f"ERROR: In preprocessor.py: More passengers assigned to tourist class than seats. Design.NUM_TOURIST_CLASS < NUM_TOURIST_CLASS."
        #         )

    if Aircraft.CrewPayload.NUM_FLIGHT_ATTENDANTS not in aviary_options:
        flight_attendants_count = 0  # assume no passengers

        if 0 < passenger_count:
            if passenger_count < 51:
                flight_attendants_count = 1

            else:
                flight_attendants_count = passenger_count // 40 + 1

        aviary_options.set_val(
            Aircraft.CrewPayload.NUM_FLIGHT_ATTENDANTS, flight_attendants_count)

    if Aircraft.CrewPayload.NUM_GALLEY_CREW not in aviary_options:
        galley_crew_count = 0  # assume no passengers

        if 150 < passenger_count:
            galley_crew_count = passenger_count // 250 + 1

        aviary_options.set_val(Aircraft.CrewPayload.NUM_GALLEY_CREW, galley_crew_count)

    if Aircraft.CrewPayload.NUM_FLIGHT_CREW not in aviary_options:
        flight_crew_count = 3

        if passenger_count < 151:
            flight_crew_count = 2

        aviary_options.set_val(Aircraft.CrewPayload.NUM_FLIGHT_CREW, flight_crew_count)

    if (Aircraft.CrewPayload.BAGGAGE_MASS_PER_PASSENGER not in aviary_options and
            Mission.Design.RANGE in aviary_options):
        design_range = aviary_options.get_val(Mission.Design.RANGE, 'nmi')

        if design_range <= 900.0:
            baggage_mass_per_pax = 35.0
        elif design_range <= 2900.0:
            baggage_mass_per_pax = 40.0
        else:
            baggage_mass_per_pax = 44.0

        aviary_options.set_val(Aircraft.CrewPayload.BAGGAGE_MASS_PER_PASSENGER,
                               val=baggage_mass_per_pax, units='lbm')

    return aviary_options


def preprocess_propulsion(aviary_options: AviaryValues, engine_models: list = None):
    '''
    Updates AviaryValues object with values taken from provided EngineModels.

    If no EngineModels are provided, either in engine_models or included in
    aviary_options, an EngineDeck is created using avaliable inputs and options in
    aviary_options.

    Vectorizes variables in aviary_options in the correct order for vehicles with
    heterogeneous engines.

    Performs basic sanity checks on inputs that are universal to all EngineModels.

    !!! WARNING !!!
    Values in aviary_options can be overwritten with corresponding values from
    engine_models!

    Parameters
    ----------
    aviary_options : AviaryValues
        Options to be updated. EngineModels (provided or generated) are added, and
        Aircraft:Engine:* and Aircraft:Nacelle:* variables are vectorized as numpy arrays

    engine_models : <list of EngineModels> (optional)
        EngineModel objects to be added to aviary_options. Replaced existing EngineModels
        in aviary_options
    '''
    # TODO add verbosity check to warnings
    ##############################
    # Vectorize Engine Variables #
    ##############################
    # Only vectorize variables user has defined in some way or engine model has calculated
    # Combine aviary_options and all engine options into single AviaryValues
    # It is assumed that all EngineModels are up-to-date at this point and will NOT
    # be changed later on (otherwise preprocess_propulsion must be run again)
    num_engine_type = len(engine_models)

    complete_options_list = AviaryValues(aviary_options)
    for engine in engine_models:
        complete_options_list.update(engine.options)

    # update_list has keys of all variables that are already defined, and must
    # be vectorized
    update_list = list(get_keys(complete_options_list))

    # Vectorize engine variables. Only update variables in update_list that are relevant
    # to engines (defined by _get_engine_variables())
    for var in _get_engine_variables():
        if var in update_list:
            dtype = _MetaData[var]['types']
            default_value = _MetaData[var]['default_value']
            # type is optionally specified, fall back to type of default value
            if dtype is None:
                if isinstance(default_value, np.ndarray):
                    dtype = default_value.dtype
                else:
                    dtype = type(default_value)
            # if dtype has multiple options, use type of default value
            if isinstance(dtype, (list, tuple)):
                # if default value is a list/tuple, find type inside that
                if isinstance(default_value, (list, tuple)):
                    dtype = type(default_value[0])
                else:
                    dtype = type(default_value)
            # if var is supposed to be a unique array per engine model, assemble flat
            # vector manually to avoid ragged arrays (such as for wing engine locations)
            if isinstance(default_value, (list, np.ndarray)):
                vec = np.zeros(0, dtype=dtype)
            elif type(default_value) is tuple:
                vec = ()
            else:
                vec = [default_value] * num_engine_type

            units = _MetaData[var]['units']

            # priority order is (checked per engine):
            # 1. EngineModel.options
            # 2. aviary_options
            # 3. default value from metadata
            for i, engine in enumerate(engine_models):
                # test to see if engine has this variable - if so, use it
                try:
                    # variables in engine models are known to be "safe", will only
                    # contain data for that engine
                    engine_val = engine.get_val(var, units)
                    if isinstance(default_value, (list, np.ndarray)):
                        vec = np.append(vec, engine_val)
                    elif isinstance(default_value, tuple):
                        vec = vec + (engine_val,)
                    else:
                        vec[i] = engine_val
                # if the variable is not in the engine model, pull from aviary options
                except KeyError:
                    # check if variable is defined in aviary options (for this engine's
                    # index) - if so, use it
                    try:
                        aviary_val = aviary_options.get_val(var, units)
                        # if aviary_val is an iterable, just grab val for this engine
                        if isinstance(aviary_val, (list, np.ndarray, tuple)):
                            aviary_val = aviary_val[i]
                        if isinstance(default_value, (list, np.ndarray)):
                            vec = np.append(vec, aviary_val)
                        elif isinstance(default_value, tuple):
                            vec = vec + (aviary_val,)
                        else:
                            vec[i] = aviary_val
                    # if not, use default value from _MetaData
                    except (KeyError, IndexError):
                        if isinstance(default_value, (list, np.ndarray)):
                            vec = np.append(vec, default_value)
                        else:
                            # default value is aleady in array
                            continue
                # TODO update each engine's options with "new" values? Allows each engine
                #      to have a copy of all options/inputs, beyond what it was
                #      originally initialized with

            # update aviary options and outputs with new vectors
            # if data is numerical, store in a numpy array
            # keep tuples as tuples, lists get converted to numpy arrays
            if type(vec[0]) in (int, float, np.int64, np.float64)\
               and type(vec) is not tuple:
                vec = np.array(vec, dtype=dtype)
            aviary_options.set_val(var, vec, units)

    ###################################
    # Input/Option Consistency Checks #
    ###################################
    # Make sure number of engines based on mount location match expected total
    try:
        num_engines_all = aviary_options.get_val(Aircraft.Engine.NUM_ENGINES)
    except KeyError:
        num_engines_all = np.zeros(num_engine_type).astype(int)
    try:
        num_fuse_engines_all = aviary_options.get_val(
            Aircraft.Engine.NUM_FUSELAGE_ENGINES)
    except KeyError:
        num_fuse_engines_all = np.zeros(num_engine_type).astype(int)
    try:
        num_wing_engines_all = aviary_options.get_val(Aircraft.Engine.NUM_WING_ENGINES)
    except KeyError:
        num_wing_engines_all = np.zeros(num_engine_type).astype(int)

    for i, engine in enumerate(engine_models):
        num_engines = num_engines_all[i]
        num_fuse_engines = num_fuse_engines_all[i]
        num_wing_engines = num_wing_engines_all[i]
        total_engines_calc = num_fuse_engines + num_wing_engines

        # if engine mount type is not specified at all, default to wing
        if total_engines_calc == 0:
            eng_name = engine.name
            num_wing_engines_all[i] = num_engines
            # TODO is a warning overkill here? It can be documented wing mounted engines
            # are assumed default
            warnings.warn(
                f'Mount location for engines of type <{eng_name}> not specified. '
                'Wing-mounted engines are assumed.')

        # If wing mount type are specified but inconsistent, handle it
        elif total_engines_calc > num_engines:
            # more defined engine locations than number of engines - increase num engines
            eng_name = engine.name
            num_engines_all[i] = total_engines_calc
            warnings.warn(
                'Sum of aircraft:engine:num_fueslage_engines and '
                'aircraft:engine:num_wing_engines do not match '
                f'aircraft:engine:num_engines for EngineModel <{eng_name}>. Overwriting '
                'with the sum of wing and fuselage mounted engines.')
        elif total_engines_calc < num_engines:
            # fewer defined locations than num_engines - assume rest are wing mounted
            eng_name = engine.name
            num_wing_engines_all[i] = num_engines - num_fuse_engines
            warnings.warn(
                'Mount location was not defined for all engines of EngineModel '
                f'<{eng_name}> - unspecified engines are assumed wing-mounted.')

    aviary_options.set_val(Aircraft.Engine.NUM_ENGINES, num_engines_all)
    aviary_options.set_val(Aircraft.Engine.NUM_WING_ENGINES, num_wing_engines_all)
    aviary_options.set_val(Aircraft.Engine.NUM_FUSELAGE_ENGINES, num_fuse_engines_all)

    if Mission.Summary.FUEL_FLOW_SCALER not in aviary_options:
        aviary_options.set_val(Mission.Summary.FUEL_FLOW_SCALER, 1.0)

    num_engines = aviary_options.get_val(Aircraft.Engine.NUM_ENGINES)
    total_num_engines = int(sum(num_engines_all))
    total_num_fuse_engines = int(sum(num_fuse_engines_all))
    total_num_wing_engines = int(sum(num_wing_engines_all))

    # compute propulsion-level engine count totals here
    aviary_options.set_val(
        Aircraft.Propulsion.TOTAL_NUM_ENGINES, total_num_engines)
    aviary_options.set_val(
        Aircraft.Propulsion.TOTAL_NUM_FUSELAGE_ENGINES, total_num_fuse_engines)
    aviary_options.set_val(
        Aircraft.Propulsion.TOTAL_NUM_WING_ENGINES, total_num_wing_engines)


def _get_engine_variables():
    '''
    Yields all propulsion-related variables in Aircraft that need to be vectorized
    '''
    for item in get_names_from_hierarchy(Aircraft.Engine):
        yield item

    for item in get_names_from_hierarchy(Aircraft.Nacelle):
        yield item
