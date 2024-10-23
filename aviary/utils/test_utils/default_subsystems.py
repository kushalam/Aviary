from aviary.subsystems.propulsion.propulsion_builder import CorePropulsionBuilder
from aviary.subsystems.geometry.geometry_builder import CoreGeometryBuilder
from aviary.subsystems.mass.mass_builder import CoreMassBuilder
from aviary.subsystems.aerodynamics.aerodynamics_builder import CoreAerodynamicsBuilder
from aviary.variable_info.variable_meta_data import _MetaData as BaseMetaData
from aviary.variable_info.enums import LegacyCode


def get_default_premission_subsystems(legacy_code, engines=None):
    """
    Get default premission subsystems propulsion, geometry, aerodynamics, and mass
    in this order.

    Arguments:
    ----------
    legacy_code : str
        either 'FLOPS' or 'GASP'
    engine : <list of EngineDecks>
        List of EngineDecks
    """
    legacy_code = LegacyCode(legacy_code)
    prop = CorePropulsionBuilder('core_propulsion', BaseMetaData, engine_models=engines)
    mass = CoreMassBuilder('core_mass', BaseMetaData, legacy_code)
    aero = CoreAerodynamicsBuilder('core_aerodynamics', BaseMetaData, legacy_code)
    geom = CoreGeometryBuilder('core_geometry', BaseMetaData, legacy_code)

    return [prop, geom, aero, mass]


def get_default_mission_subsystems(legacy_code, engines=None):
    """
    Get default mission subsystems aerodynamics and propulsion
    in this order.

    Arguments:
    ----------
    legacy_code : str
        either 'FLOPS' or 'GASP'
    engine : <list of EngineDecks>
        List of EngineDecks
    """

    legacy_code = LegacyCode(legacy_code)
    prop = CorePropulsionBuilder('core_propulsion', BaseMetaData, engine_models=engines)
    aero = CoreAerodynamicsBuilder('core_aerodynamics', BaseMetaData, legacy_code)

    return [aero, prop]
