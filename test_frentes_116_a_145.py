"""
Testes unitários automatizados para as Frentes 116 a 145 da Engenharia Reversa do SketchUp.
Cobre todos os 30 motores especializados (Zero DLL / Pure Python) e camadas assíncronas do controller:
- 116: StormwaterDrainageEngine (drenagem pluvial e calhas NBR 10844)
- 117: PermeablePavementEngine (pavimentação permeável NBR 16416)
- 118: SewerNetworkGravityEngine (rede de esgoto por gravidade NBR 9649)
- 119: DetentionBasinHydrologyEngine (bacia de detenção de cheias)
- 120: EarthworkBrucknerEngine (terraplenagem e curva de massas de Brückner)
- 121: SlopeStabilityBishopEngine (estabilidade de taludes Bishop Simplificado)
- 122: DeepFoundationsPilesEngine (estacas e fundações profundas NBR 6122)
- 123: ShallowFootingsEngine (sapatas rígidas rasas NBR 6118/6122)
- 124: GabionRetainingWallEngine (muros de gabião NBR 10328)
- 125: ConcreteFormworkShoringEngine (fôrmas e escoramento NBR 15696)
- 126: ReinforcedConcreteBeamEngine (vigas de concreto armado ELU NBR 6118)
- 127: WaffleSlabEngine (lajes nervuradas com cubetas NBR 6118)
- 128: PrestressedConcreteEngine (concreto protendido e perdas NBR 6118)
- 129: GlulamCltTimberEngine (madeira laminada colada e CLT NBR 7190)
- 130: SpaceTrussEngine (treliças espaciais tubulares 3D)
- 131: FuelGasPipingEngine (gás canalizado GLP/GN NBR 15526)
- 132: LightningProtectionSpdaEngine (SPDA esfera rolante NBR 5419)
- 133: FireEgressRouteEngine (rotas de fuga NBR 9077)
- 134: HvacThermalLoadEngine (carga térmica HVAC NBR 16401)
- 135: PhotometricLumenDesignEngine (método dos lúmens NBR 8995)
- 136: SolarPhotovoltaicArrayEngine (usinas solares fotovoltaicas)
- 137: NaturalVentilationEngine (ventilação natural e efeito chaminé NBR 15220)
- 138: GlazingFenestrationEngine (esquadrias paramétricas e pele de vidro)
- 139: VentilatedFacadeEngine (fachadas ventiladas convectivas)
- 140: MiniWindCfd2dEngine (túnel de vento numérico CFD 2D)
- 141: Bim4dGanttScheduleEngine (cronograma BIM 4D e curva S)
- 142: Bim7dAssetManagementCobieEngine (gestão de ativos BIM 7D e COBie)
- 143: ConstructionSiteLogisticsEngine (logística de canteiro NR-18)
- 144: UniversalAccessibilityEngine (acessibilidade universal NBR 9050)
- 145: LifeCycleAssessmentEngine (avaliação de ciclo de vida ACV ISO 14040)
"""

import unittest
import asyncio

from core.stormwater_drainage_engine import StormwaterDrainageEngine
from core.permeable_pavement_engine import PermeablePavementEngine
from core.sewer_network_gravity_engine import SewerNetworkGravityEngine
from core.detention_basin_hydrology_engine import DetentionBasinHydrologyEngine
from core.earthwork_bruckner_engine import EarthworkBrucknerEngine
from core.slope_stability_bishop_engine import SlopeStabilityBishopEngine
from core.deep_foundations_piles_engine import DeepFoundationsPilesEngine
from core.shallow_footings_engine import ShallowFootingsEngine
from core.gabion_retaining_wall_engine import GabionRetainingWallEngine
from core.concrete_formwork_shoring_engine import ConcreteFormworkShoringEngine
from core.reinforced_concrete_beam_engine import ReinforcedConcreteBeamEngine
from core.waffle_slab_engine import WaffleSlabEngine
from core.prestressed_concrete_engine import PrestressedConcreteEngine
from core.glulam_clt_timber_engine import GlulamCltTimberEngine
from core.space_truss_engine import SpaceTrussEngine
from core.fuel_gas_piping_engine import FuelGasPipingEngine
from core.lightning_protection_spda_engine import LightningProtectionSpdaEngine
from core.fire_egress_route_engine import FireEgressRouteEngine
from core.hvac_thermal_load_engine import HvacThermalLoadEngine
from core.photometric_lumen_design_engine import PhotometricLumenDesignEngine
from core.solar_photovoltaic_array_engine import SolarPhotovoltaicArrayEngine
from core.natural_ventilation_engine import NaturalVentilationEngine
from core.glazing_fenestration_engine import GlazingFenestrationEngine
from core.ventilated_facade_engine import VentilatedFacadeEngine
from core.mini_wind_cfd_2d_engine import MiniWindCfd2dEngine
from core.bim_4d_gantt_schedule_engine import Bim4dGanttScheduleEngine
from core.bim_7d_asset_management_cobie_engine import Bim7dAssetManagementCobieEngine
from core.construction_site_logistics_engine import ConstructionSiteLogisticsEngine
from core.universal_accessibility_engine import UniversalAccessibilityEngine
from core.life_cycle_assessment_engine import LifeCycleAssessmentEngine

from app.controllers.scene_controller import SceneController
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.schemas.scene import (
    StormwaterDrainageRequest,
    PermeablePavementRequest,
    SewerNetworkGravityRequest,
    DetentionBasinHydrologyRequest,
    EarthworkBrucknerRequest,
    SlopeStabilityBishopRequest,
    DeepFoundationsPilesRequest,
    ShallowFootingsRequest,
    GabionRetainingWallRequest,
    ConcreteFormworkShoringRequest,
    ReinforcedConcreteBeamRequest,
    WaffleSlabRequest,
    PrestressedConcreteRequest,
    GlulamCltTimberRequest,
    SpaceTrussRequest,
    FuelGasPipingRequest,
    LightningProtectionSpdaRequest,
    FireEgressRouteRequest,
    HvacThermalLoadRequest,
    PhotometricLumenDesignRequest,
    SolarPhotovoltaicArrayRequest,
    NaturalVentilationRequest,
    GlazingFenestrationRequest,
    VentilatedFacadeRequest,
    MiniWindCfd2dRequest,
    Bim4dGanttScheduleRequest,
    Bim7dAssetManagementCobieRequest,
    ConstructionSiteLogisticsRequest,
    UniversalAccessibilityRequest,
    LifeCycleAssessmentRequest,
)


class TestFrentes116a145(unittest.TestCase):
    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    # 116
    def test_stormwater_drainage(self):
        res = StormwaterDrainageEngine.calculate_drainage(roof_area_m2=150.0, rainfall_intensity_mm_h=150.0)
        self.assertEqual(res["entity_type"], "StormwaterDrainageReport")
        self.assertGreater(res["hydraulic_results"]["total_design_flow_l_min"], 0.0)
        self.assertTrue(res["hydraulic_results"]["is_compliant_nbr10844"])

    # 117
    def test_permeable_pavement(self):
        res = PermeablePavementEngine.calculate_pavement(pavement_area_m2=300.0, base_thickness_m=0.30)
        self.assertEqual(res["entity_type"], "PermeablePavementReport")
        self.assertGreater(res["drainage_metrics"]["runoff_reduction_percent"], 50.0)
        self.assertTrue(res["drainage_metrics"]["is_storage_adequate"])

    # 118
    def test_sewer_network(self):
        res = SewerNetworkGravityEngine.calculate_sewer_run(pipe_diameter_dn_mm=150.0, flow_rate_l_s=3.0)
        self.assertEqual(res["entity_type"], "SewerNetworkReport")
        self.assertLessEqual(res["hydraulic_metrics"]["water_depth_ratio_y_d"], 0.75)
        self.assertGreaterEqual(res["hydraulic_metrics"]["shear_stress_pa"], 1.0)

    # 119
    def test_detention_basin(self):
        res = DetentionBasinHydrologyEngine.calculate_basin(catchment_area_ha=6.0, allowable_outflow_l_s=300.0)
        self.assertEqual(res["entity_type"], "DetentionBasinReport")
        self.assertGreater(res["hydrologic_results"]["required_storage_volume_m3"], 50.0)
        self.assertGreater(res["hydrologic_results"]["peak_reduction_percent"], 0.0)

    # 120
    def test_earthwork_bruckner(self):
        res = EarthworkBrucknerEngine.calculate_earthwork()
        self.assertEqual(res["entity_type"], "EarthworkBrucknerReport")
        self.assertGreater(res["earthwork_summary"]["total_cut_geometric_m3"], 0.0)
        self.assertGreater(len(res["bruckner_curve"]), 3)

    # 121
    def test_slope_stability_bishop(self):
        res = SlopeStabilityBishopEngine.calculate_stability(slope_height_m=7.0, slope_angle_deg=30.0)
        self.assertEqual(res["entity_type"], "SlopeStabilityReport")
        self.assertGreater(res["stability_analysis"]["factor_of_safety_bishop"], 1.0)
        self.assertGreater(len(res["failure_arc_points"]), 5)

    # 122
    def test_deep_foundations_piles(self):
        res = DeepFoundationsPilesEngine.calculate_pile(column_axial_load_kn=2000.0, pile_diameter_mm=500.0)
        self.assertEqual(res["entity_type"], "DeepFoundationsReport")
        self.assertGreater(res["geotechnical_capacity"]["piles_count_in_cap"], 0)
        self.assertEqual(res["geotechnical_capacity"]["safety_factor"], 2.0)

    # 123
    def test_shallow_footings(self):
        res = ShallowFootingsEngine.calculate_footing(column_load_kn=700.0, soil_allowable_stress_mpa=0.25)
        self.assertEqual(res["entity_type"], "ShallowFootingReport")
        self.assertTrue(res["footing_dimensions"]["is_rigid_footing"])
        self.assertGreater(res["footing_dimensions"]["reinforcement_as_x_cm2"], 0.0)

    # 124
    def test_gabion_wall(self):
        res = GabionRetainingWallEngine.calculate_gabion(wall_height_m=3.5, base_width_m=2.2)
        self.assertEqual(res["entity_type"], "GabionRetainingWallReport")
        self.assertGreater(res["stability_analysis"]["safety_factor_overturning"], 1.2)
        self.assertTrue(res["stability_analysis"]["free_draining"])

    # 125
    def test_concrete_formwork(self):
        res = ConcreteFormworkShoringEngine.calculate_formwork(height_or_span_m=2.8, shore_allowable_load_kn=15.0)
        self.assertEqual(res["entity_type"], "FormworkShoringReport")
        self.assertGreater(res["formwork_metrics"]["max_lateral_pressure_kpa"], 0.0)
        self.assertTrue(res["formwork_metrics"]["is_safe_nbr15696"])

    # 126
    def test_rc_beam_elu(self):
        res = ReinforcedConcreteBeamEngine.calculate_beam_elu(bending_moment_mk_kn_m=100.0, shear_force_vk_kn=70.0)
        self.assertEqual(res["entity_type"], "ReinforcedConcreteBeamReport")
        self.assertTrue(res["design_results"]["is_ductile_section"])
        self.assertGreater(res["design_results"]["longitudinal_steel_as_cm2"], 0.0)

    # 127
    def test_waffle_slab(self):
        res = WaffleSlabEngine.calculate_waffle_slab(span_x_m=8.0, span_y_m=8.0)
        self.assertEqual(res["entity_type"], "WaffleSlabReport")
        self.assertGreater(res["waffle_metrics"]["concrete_savings_percent"], 20.0)
        self.assertGreater(res["waffle_metrics"]["solid_shear_head_capitel_dim_cm"], 50.0)

    # 128
    def test_prestressed_concrete(self):
        res = PrestressedConcreteEngine.calculate_prestressing(beam_span_m=15.0, strands_count=8)
        self.assertEqual(res["entity_type"], "PrestressedConcreteReport")
        self.assertGreater(res["prestress_metrics"]["final_effective_force_p_inf_kn"], 500.0)
        self.assertGreater(len(res["parabolic_tendon_3d"]), 5)

    # 129
    def test_glulam_timber(self):
        res = GlulamCltTimberEngine.calculate_timber(span_m=6.0, distributed_load_kn_m=8.0)
        self.assertEqual(res["entity_type"], "GlulamTimberReport")
        self.assertTrue(res["timber_structural_results"]["is_deflection_compliant"])
        self.assertLessEqual(res["timber_structural_results"]["bending_utilization_ratio"], 1.0)

    # 130
    def test_space_truss(self):
        res = SpaceTrussEngine.generate_space_truss(span_x_m=10.0, span_y_m=10.0)
        self.assertEqual(res["entity_type"], "SpaceTrussReport")
        self.assertGreater(res["truss_statistics"]["nodes_count"], 10)
        self.assertGreater(res["truss_statistics"]["members_count"], 20)

    # 131
    def test_fuel_gas_piping(self):
        res = FuelGasPipingEngine.calculate_gas_network(total_power_kw=60.0, pipe_length_m=20.0)
        self.assertEqual(res["entity_type"], "FuelGasPipingReport")
        self.assertTrue(res["gas_network_results"]["is_compliant_nbr15526"])

    # 132
    def test_lightning_spda(self):
        res = LightningProtectionSpdaEngine.calculate_spda(building_width_m=20.0, building_height_m=15.0)
        self.assertEqual(res["entity_type"], "LightningProtectionSpdaReport")
        self.assertGreater(res["spda_design"]["rolling_sphere_radius_m"], 0.0)
        self.assertGreater(res["spda_design"]["min_down_conductors_count"], 1)

    # 133
    def test_fire_egress(self):
        res = FireEgressRouteEngine.calculate_egress(floor_population_persons=150, longest_travel_distance_m=35.0)
        self.assertEqual(res["entity_type"], "FireEgressReport")
        self.assertGreaterEqual(res["egress_metrics"]["width_per_door_m"], 0.6)

    # 134
    def test_hvac_cooling_load(self):
        res = HvacThermalLoadEngine.calculate_cooling_load(floor_area_m2=90.0, occupants_count=10)
        self.assertEqual(res["entity_type"], "HvacThermalLoadReport")
        self.assertGreater(res["thermal_load_breakdown"]["total_cooling_capacity_tr"], 1.0)

    # 135
    def test_photometric_lumen(self):
        res = PhotometricLumenDesignEngine.calculate_lighting(room_length_m=8.0, room_width_m=6.0, target_lux=500.0)
        self.assertEqual(res["entity_type"], "PhotometricLumenReport")
        self.assertTrue(res["lighting_results"]["is_compliant_nbr8995"])
        self.assertGreater(len(res["luminaire_positions_3d"]), 0)

    # 136
    def test_solar_pv(self):
        res = SolarPhotovoltaicArrayEngine.calculate_pv_system(roof_available_area_m2=120.0)
        self.assertEqual(res["entity_type"], "SolarPhotovoltaicReport")
        self.assertGreater(res["solar_system_metrics"]["installed_capacity_kwp"], 5.0)
        self.assertGreater(res["solar_system_metrics"]["annual_energy_generation_kwh"], 5000.0)

    # 137
    def test_natural_ventilation(self):
        res = NaturalVentilationEngine.calculate_ventilation(room_volume_m3=150.0, wind_speed_m_s=4.0)
        self.assertEqual(res["entity_type"], "NaturalVentilationReport")
        self.assertGreater(res["ventilation_results"]["air_changes_per_hour_ach"], 1.0)

    # 138
    def test_glazing_fenestration(self):
        res = GlazingFenestrationEngine.generate_fenestration(width_m=2.5, height_m=2.2)
        self.assertEqual(res["entity_type"], "GlazingFenestrationReport")
        self.assertGreater(res["fenestration_metrics"]["total_glass_weight_kg"], 10.0)

    # 139
    def test_ventilated_facade(self):
        res = VentilatedFacadeEngine.calculate_facade(facade_height_m=12.0, facade_width_m=18.0)
        self.assertEqual(res["entity_type"], "VentilatedFacadeReport")
        self.assertGreater(res["thermal_and_structural_results"]["solar_heat_dissipation_percent"], 20.0)

    # 140
    def test_mini_wind_cfd_2d(self):
        res = MiniWindCfd2dEngine.simulate_wind_tunnel_2d(building_width_m=10.0, wind_inflow_speed_m_s=12.0)
        self.assertEqual(res["entity_type"], "MiniWindCfd2dReport")
        self.assertGreater(res["aerodynamic_results"]["drag_coefficient_cd"], 1.0)
        self.assertGreater(len(res["streamlines_sample"]), 3)

    # 141
    def test_bim_4d_schedule(self):
        res = Bim4dGanttScheduleEngine.generate_4d_schedule()
        self.assertEqual(res["entity_type"], "Bim4dScheduleReport")
        self.assertGreater(res["schedule_summary"]["total_duration_days"], 50)
        self.assertEqual(len(res["curve_s_points"]), 11)

    # 142
    def test_bim_7d_cobie(self):
        res = Bim7dAssetManagementCobieEngine.generate_cobie_assets()
        self.assertEqual(res["entity_type"], "Bim7dCobieReport")
        self.assertGreater(res["facility_management_summary"]["total_tracked_assets"], 0)
        self.assertEqual(len(res["cobie_components"]), 3)

    # 143
    def test_construction_site_logistics(self):
        res = ConstructionSiteLogisticsEngine.calculate_site_logistics(site_width_m=50.0, site_length_m=70.0)
        self.assertEqual(res["entity_type"], "ConstructionSiteLogisticsReport")
        self.assertGreater(res["logistics_results"]["available_yard_area_m2"], 100.0)

    # 144
    def test_universal_accessibility(self):
        res = UniversalAccessibilityEngine.audit_accessibility(door_clear_width_cm=90.0, corridor_width_cm=130.0)
        self.assertEqual(res["entity_type"], "AccessibilityReport")
        self.assertTrue(res["compliance_checklist"]["is_fully_accessible_nbr9050"])

    # 145
    def test_life_cycle_assessment(self):
        res = LifeCycleAssessmentEngine.calculate_lca(gross_floor_area_m2=600.0)
        self.assertEqual(res["entity_type"], "LifeCycleAssessmentReport")
        self.assertGreater(res["lca_metrics"]["total_embodied_carbon_tons_co2e"], 10.0)
        self.assertIn("environmental_performance_rating", res["lca_metrics"])

    # ---------------------------------------------------------
    # Teste de Integração Assíncrona dos Controllers (Frentes 116 a 145)
    # ---------------------------------------------------------
    def test_async_controllers_frentes_116_a_145(self):
        async def run_controllers():
            r116 = await self.controller.calculate_stormwater_drainage(StormwaterDrainageRequest(roof_area_m2=100.0))
            self.assertEqual(r116.entity_type, "StormwaterDrainageReport")

            r117 = await self.controller.calculate_permeable_pavement(PermeablePavementRequest(pavement_area_m2=200.0))
            self.assertEqual(r117.entity_type, "PermeablePavementReport")

            r118 = await self.controller.calculate_sewer_network(SewerNetworkGravityRequest(pipe_diameter_dn_mm=150.0))
            self.assertEqual(r118.entity_type, "SewerNetworkReport")

            r119 = await self.controller.calculate_detention_basin(DetentionBasinHydrologyRequest(catchment_area_ha=4.0))
            self.assertEqual(r119.entity_type, "DetentionBasinReport")

            r120 = await self.controller.calculate_earthwork_bruckner(EarthworkBrucknerRequest())
            self.assertEqual(r120.entity_type, "EarthworkBrucknerReport")

            r121 = await self.controller.calculate_slope_stability_bishop(SlopeStabilityBishopRequest(slope_height_m=6.0))
            self.assertEqual(r121.entity_type, "SlopeStabilityReport")

            r122 = await self.controller.calculate_deep_foundations_piles(DeepFoundationsPilesRequest())
            self.assertEqual(r122.entity_type, "DeepFoundationsReport")

            r123 = await self.controller.calculate_shallow_footings(ShallowFootingsRequest())
            self.assertEqual(r123.entity_type, "ShallowFootingReport")

            r124 = await self.controller.calculate_gabion_wall(GabionRetainingWallRequest())
            self.assertEqual(r124.entity_type, "GabionRetainingWallReport")

            r125 = await self.controller.calculate_concrete_formwork(ConcreteFormworkShoringRequest())
            self.assertEqual(r125.entity_type, "FormworkShoringReport")

            r126 = await self.controller.calculate_reinforced_concrete_beam(ReinforcedConcreteBeamRequest())
            self.assertEqual(r126.entity_type, "ReinforcedConcreteBeamReport")

            r127 = await self.controller.calculate_waffle_slab(WaffleSlabRequest())
            self.assertEqual(r127.entity_type, "WaffleSlabReport")

            r128 = await self.controller.calculate_prestressed_concrete(PrestressedConcreteRequest())
            self.assertEqual(r128.entity_type, "PrestressedConcreteReport")

            r129 = await self.controller.calculate_glulam_timber(GlulamCltTimberRequest())
            self.assertEqual(r129.entity_type, "GlulamTimberReport")

            r130 = await self.controller.generate_space_truss(SpaceTrussRequest())
            self.assertEqual(r130.entity_type, "SpaceTrussReport")

            r131 = await self.controller.calculate_fuel_gas_piping(FuelGasPipingRequest())
            self.assertEqual(r131.entity_type, "FuelGasPipingReport")

            r132 = await self.controller.calculate_lightning_spda(LightningProtectionSpdaRequest())
            self.assertEqual(r132.entity_type, "LightningProtectionSpdaReport")

            r133 = await self.controller.calculate_fire_egress(FireEgressRouteRequest())
            self.assertEqual(r133.entity_type, "FireEgressReport")

            r134 = await self.controller.calculate_hvac_cooling_load(HvacThermalLoadRequest())
            self.assertEqual(r134.entity_type, "HvacThermalLoadReport")

            r135 = await self.controller.calculate_photometric_lighting(PhotometricLumenDesignRequest())
            self.assertEqual(r135.entity_type, "PhotometricLumenReport")

            r136 = await self.controller.calculate_solar_pv(SolarPhotovoltaicArrayRequest())
            self.assertEqual(r136.entity_type, "SolarPhotovoltaicReport")

            r137 = await self.controller.calculate_natural_ventilation(NaturalVentilationRequest())
            self.assertEqual(r137.entity_type, "NaturalVentilationReport")

            r138 = await self.controller.generate_glazing_fenestration(GlazingFenestrationRequest())
            self.assertEqual(r138.entity_type, "GlazingFenestrationReport")

            r139 = await self.controller.calculate_ventilated_facade(VentilatedFacadeRequest())
            self.assertEqual(r139.entity_type, "VentilatedFacadeReport")

            r140 = await self.controller.simulate_wind_cfd_2d(MiniWindCfd2dRequest())
            self.assertEqual(r140.entity_type, "MiniWindCfd2dReport")

            r141 = await self.controller.generate_bim_4d_schedule(Bim4dGanttScheduleRequest())
            self.assertEqual(r141.entity_type, "Bim4dScheduleReport")

            r142 = await self.controller.generate_bim_7d_cobie(Bim7dAssetManagementCobieRequest())
            self.assertEqual(r142.entity_type, "Bim7dCobieReport")

            r143 = await self.controller.calculate_site_logistics(ConstructionSiteLogisticsRequest())
            self.assertEqual(r143.entity_type, "ConstructionSiteLogisticsReport")

            r144 = await self.controller.audit_universal_accessibility(UniversalAccessibilityRequest())
            self.assertEqual(r144.entity_type, "AccessibilityReport")

            r145 = await self.controller.calculate_lca_emissions(LifeCycleAssessmentRequest())
            self.assertEqual(r145.entity_type, "LifeCycleAssessmentReport")

        asyncio.run(run_controllers())


if __name__ == "__main__":
    unittest.main()
