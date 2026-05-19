#################################################################################
# WaterTAP Copyright (c) 2020-2024, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory, Oak Ridge National Laboratory,
# National Renewable Energy Laboratory, and National Energy Technology
# Laboratory (subject to receipt of any required approvals from the U.S. Dept.
# of Energy). All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and license
# information, respectively. These files are also available online at the URL
# "https://github.com/watertap-org/watertap/"
#################################################################################

import pyomo.environ as pyo
from ..util import (
    register_costing_parameter_block,
    make_capital_cost_var,
    make_fixed_operating_cost_var,
)

def build_h2o2_cost_param_block(blk):

    blk.cost = pyo.Param(
        mutable=True,
        initialize=1.55,
        doc="H2O2 cost",  # for Hydrogen peroxide, 70%, as is basis, tankcars, frt. equald. - CatCost v 1.0.4
        units=pyo.units.USD_2020 / pyo.units.kg,
    )
    blk.purity = pyo.Param(
        mutable=True,
        initialize=0.70,
        doc="H2O2 purity",
        units=pyo.units.dimensionless,
    )

    costing = blk.parent_block()
    costing.register_flow_type("h2o2", blk.cost / blk.purity)


def build_uv_cost_param_block(blk):

    blk.factor_lamp_replacement = pyo.Var(
        initialize=0.33278,
        doc="UV replacement factor accounting for lamps, sleeves, ballasts and sensors [fraction of uv replaced/year]",
        units=pyo.units.year**-1,
    )
    blk.reactor_cost = pyo.Var(
        initialize=202.346,
        doc="UV reactor cost",
        units=pyo.units.USD_2018
    )
    blk.lamp_cost = pyo.Var(
        initialize=235.5,
        doc="UV lamps, sleeves, ballasts and sensors cost",
        units=pyo.units.USD_2018,
    )
    blk.dosing_system_cost = pyo.Var(
        initialize=0,
        doc="Cost of H2O2 dosing system, excluding chemical cost",
        units=pyo.units.USD_2018,
    )
    blk.gas_diffusion_cathode = pyo.Var(
        initialize=0,
        doc="Cost of gas diffusion cathode for electrochemical generation of H2O2",
        units=pyo.units.USD_2018,
    )
    blk.graphine_anode = pyo.Var(
        initialize=0,
        doc="Cost of boron-doped reduced-graphene oxide anode for electrochemical generation of H2O2",
        units=pyo.units.USD_2018,
    )
    blk.anode_cathode_replacement = pyo.Var(
        initialize=0.5,
        doc="Replacement factor for anode and cathode [fraction of electrochemical cell replaced/year]",
        units=pyo.units.year**-1,
    )
    blk.cation_exchange_membrane = pyo.Var(
        initialize=0,
        doc="Cost of cation exchange membrane for electrochemical generation of H2O2",
        units=pyo.units.USD_2018,
    )
    blk.steel_electrode = pyo.Var(
        initialize=0,
        doc="Cost of stainless-steel electrode for electrochemical generation of H2O2",
        units=pyo.units.USD_2018,
    )
    blk.electrode_replacement = pyo.Var(
        initialize=2,
        doc="Replacement factor for steel electrode [fraction of electrochemical cell replaced/year]",
        units=pyo.units.year**-1,
    )
    blk.electrochemical_reactor = pyo.Var(
        initialize=0,
        doc="Cost of reactor, reservoir, and metering pump for electrochemical generation of H2O2",
        units=pyo.units.USD_2018,
    )
    blk.remainder_replacement = pyo.Var(
        initialize=0.1,
        doc="Replacement factor for reactor, metering pumps, reservoir, and membrane [fraction of electrochemical cell replaced/year]",
        units=pyo.units.year**-1,
    )                     

@register_costing_parameter_block(
    build_rule=build_h2o2_cost_param_block,
    parameter_block_name="h2o2",
)
@register_costing_parameter_block(
    build_rule=build_uv_cost_param_block,
    parameter_block_name="ultraviolet",
)
def cost_uv_aop(blk, cost_electricity_flow=True):
    """
    UV-AOP costing method
    """
    cost_uv_aop_bundle(
        blk,
        blk.costing_package.ultraviolet.reactor_cost,
        blk.costing_package.ultraviolet.lamp_cost,
        blk.costing_package.ultraviolet.factor_lamp_replacement,
        blk.costing_package.ultraviolet.dosing_system_cost,
        blk.costing_package.ultraviolet.gas_diffusion_cathode,
        blk.costing_package.ultraviolet.graphine_anode,
        blk.costing_package.ultraviolet.cation_exchange_membrane,
        blk.costing_package.ultraviolet.steel_electrode,
        blk.costing_package.ultraviolet.electrochemical_reactor,
        blk.costing_package.ultraviolet.anode_cathode_replacement,
        blk.costing_package.ultraviolet.remainder_replacement,
        blk.costing_package.ultraviolet.electrode_replacement,
    )

    t0 = blk.flowsheet().time.first()
    if cost_electricity_flow:
        blk.costing_package.cost_flow(
            pyo.units.convert(
                blk.unit_model.electricity_demand[t0],
                to_units=pyo.units.kW,
            ),
            "electricity",
        )

    if blk.unit_model.config.has_aop:
        blk.unit_model.mass_flow_hydrogen_peroxide = pyo.Expression(
            expr=(
                pyo.units.convert(
                    blk.unit_model.hydrogen_peroxide_dose
                    * blk.unit_model.control_volume.properties_in[t0].flow_vol_phase[
                        "Liq"
                    ],
                    to_units=pyo.units.kg / pyo.units.s,
                )
            )
        )
        blk.costing_package.cost_flow(
            blk.unit_model.mass_flow_hydrogen_peroxide,
            "h2o2",
        )


def cost_uv_aop_bundle(blk, reactor_cost, lamp_cost, factor_lamp_replacement, dosing_system_cost, gas_diffusion_cathode, graphine_anode, cation_exchange_membrane, steel_electrode, electrochemical_reactor, anode_cathode_replacement, remainder_replacement, electrode_replacement):
    """
    Generic function for costing a UV system.

    Args:
        reactor_cost: The cost of UV reactor in [currency]
        lamp_cost: The costs of the lamps, sleeves, ballasts and sensors in [currency]
        factor_lamp_replacement: Replacement factor for lamps, sleeves, ballasts and sensors [fraction of UV replaced/year]
        dosing_system_cost: The cost of the H2O2 dosing system in [currency]
        gas_diffusion_cathode: The cost of the gas diffusion cathode for electrochemical generation of H2O2 in [currency]
        graphine_anode: The cost of the boron-doped reduced-graphene oxide anode for electrochemical generation of H2O2 in [currency]
        cation_exchange_membrane: The cost of the cation exchange membrane for electrochemical generation of H2O2 in [currency]
        steel_electrode: The cost of the stainless-steel electrode for electrochemical generation of H2O2 in [currency]
        electrochemical_reactor: The cost of the reactor, reservoir, and metering pump for electrochemical generation of H2O2 in [currency]
        anode_cathode_replacement: Replacement factor for anode and cathode [fraction of electrochemical cell replaced/year]
        remainder_replacement: Replacement factor for reactor, metering pumps, reservoir, and membrane [fraction of electrochemical cell replaced/year]
        electrode_replacement: Replacement factor for steel electrode [fraction of electrochemical cell replaced/year]

    """
    make_capital_cost_var(blk)
    make_fixed_operating_cost_var(blk)
    blk.reactor_cost = pyo.Expression(expr=reactor_cost)
    blk.lamp_cost = pyo.Expression(expr=lamp_cost)
    blk.factor_lamp_replacement = pyo.Expression(expr=factor_lamp_replacement)
    blk.dosing_system_cost = pyo.Expression(expr=dosing_system_cost)
    blk.gas_diffusion_cathode = pyo.Expression(expr=gas_diffusion_cathode)
    blk.graphine_anode = pyo.Expression(expr=graphine_anode)
    blk.cation_exchange_membrane = pyo.Expression(expr=cation_exchange_membrane)
    blk.steel_electrode = pyo.Expression(expr=steel_electrode)
    blk.electrochemical_reactor = pyo.Expression(expr=electrochemical_reactor)
    blk.anode_cathode_replacement = pyo.Expression(expr=anode_cathode_replacement)
    blk.remainder_replacement = pyo.Expression(expr=remainder_replacement)
    blk.electrode_replacement = pyo.Expression(expr=electrode_replacement)

    blk.costing_package.add_cost_factor(blk, "TIC")
    blk.capital_cost_constraint = pyo.Constraint(
        expr=blk.capital_cost
        == blk.cost_factor
        * pyo.units.convert(
            blk.reactor_cost + blk.lamp_cost + blk.dosing_system_cost + blk.gas_diffusion_cathode + blk.graphine_anode + blk.cation_exchange_membrane + blk.steel_electrode + blk.electrochemical_reactor,
            to_units=blk.costing_package.base_currency,
        )
    )
    blk.fixed_operating_cost_constraint = pyo.Constraint(
        expr=blk.fixed_operating_cost
        == pyo.units.convert(
            blk.factor_lamp_replacement * blk.lamp_cost + blk.anode_cathode_replacement*(blk.gas_diffusion_cathode + blk.graphine_anode) + blk.remainder_replacement*(blk.cation_exchange_membrane + blk.electrochemical_reactor) + blk.electrode_replacement*(blk.steel_electrode),  
            to_units=blk.costing_package.base_currency
            / blk.costing_package.base_period,
        )
    )
