"""
Testes unitários automatizados para as Frentes 106 a 115 da Engenharia Reversa do SketchUp.
Cobre:
- Frente 106: RigidBodyPhysicsEngine (física newtoniana, colisões e estabilidade)
- Frente 107: Slicing3DPrintEngine (fatiamento FDM, STL/3MF, filamento)
- Frente 108: RetainingWallEngine (estabilidade muro de arrimo NBR 11682)
- Frente 109: HydraulicPipingEngine (rede hidráulica predial NBR 5626)
- Frente 110: ElectricalConduitEngine (eletrodutos e ocupação NBR 5410)
- Frente 111: ThermalComfortEngine (conforto térmico NBR 15220)
- Frente 112: RoomAcousticsEngine (acústica de salas NBR 10152 e RT60)
- Frente 113: DaylightFactorEngine (fator de luz diurna NBR 15215)
- Frente 114: SteelProfileEngine (perfis metálicos NBR 8800)
- Frente 115: Bim5dSinapiCostEngine (orçamento BIM 5D, curva ABC e SINAPI)
"""

import unittest
import asyncio

from core.rigid_body_physics_engine import RigidBodyPhysicsEngine
from core.slicing_3d_print_engine import Slicing3DPrintEngine
from core.retaining_wall_engine import RetainingWallEngine
from core.hydraulic_piping_engine import HydraulicPipingEngine
from core.electrical_conduit_engine import ElectricalConduitEngine
from core.thermal_comfort_engine import ThermalComfortEngine
from core.room_acoustics_engine import RoomAcousticsEngine
from core.daylight_factor_engine import DaylightFactorEngine
from core.steel_profile_engine import SteelProfileEngine
from core.bim_5d_sinapi_cost_engine import Bim5dSinapiCostEngine

from app.controllers.scene_controller import SceneController
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.schemas.scene import (
    RigidBodyPhysicsRequest,
    Slicing3dPrintRequest,
    RetainingWallRequest,
    HydraulicPipingRequest,
    ElectricalConduitRequest,
    ThermalComfortRequest,
    RoomAcousticsRequest,
    DaylightFactorRequest,
    SteelProfileRequest,
    Bim5dSinapiCostRequest,
)


class TestFrentes106a115(unittest.TestCase):
    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    # ---------------------------------------------------------
    # Frente 106: Rigid Body Physics Engine
    # ---------------------------------------------------------
    def test_rigid_body_physics_engine(self):
        bodies = [
            {
                "id": "sphere_1",
                "name": "Esfera Teste",
                "mass_kg": 2.5,
                "initial_pos": [0.0, 0.0, 5.0],
                "initial_vel": [1.0, 0.0, 0.0],
                "dimensions": [0.5, 0.5, 0.5],
            }
        ]
        res = RigidBodyPhysicsEngine.simulate_drop(
            bodies=bodies,
            gravity_z=-9.81,
            ground_z=0.0,
            time_step_s=0.016,
            total_time_s=1.0,
            restitution=0.45,
            friction_coeff=0.35,
        )
        self.assertEqual(res["entity_type"], "RigidBodyPhysicsReport")
        self.assertEqual(res["bodies_count"], 1)
        self.assertIn("sphere_1", res["trajectories"])
        traj = res["trajectories"]["sphere_1"]
        self.assertGreater(len(traj), 10)
        final_summary = res["final_summary"][0]
        self.assertIn("final_position", final_summary)
        self.assertTrue(final_summary["settled_at_ground"])

    # ---------------------------------------------------------
    # Frente 107: Slicing 3D Print Engine
    # ---------------------------------------------------------
    def test_slicing_3d_print_engine(self):
        vertices = [
            [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
            [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
        ]
        triangles = [
            [0, 1, 2], [0, 2, 3],
            [4, 6, 5], [4, 7, 6],
            [0, 5, 1], [0, 4, 5],
            [1, 6, 2], [1, 5, 6],
            [2, 7, 3], [2, 6, 7],
            [3, 4, 0], [3, 7, 4],
        ]
        res = Slicing3DPrintEngine.slice_model_fdm(
            vertices=vertices,
            triangles=triangles,
            layer_height_mm=0.20,
            infill_percent=20.0,
            print_speed_mm_s=50.0,
        )
        self.assertEqual(res["entity_type"], "FdmSlicingReport")
        metrics = res["slicing_metrics"]
        self.assertGreaterEqual(metrics["total_layers"], 40)
        self.assertGreater(metrics["estimated_time_minutes"], 0)
        self.assertGreater(metrics["filament_length_m"], 0)

    # ---------------------------------------------------------
    # Frente 108: Retaining Wall Engine (NBR 11682)
    # ---------------------------------------------------------
    def test_retaining_wall_engine(self):
        res = RetainingWallEngine.calculate_wall_stability(
            wall_height_m=3.5,
            stem_top_thickness_m=0.25,
            stem_bottom_thickness_m=0.50,
            base_width_m=2.2,
            base_thickness_m=0.45,
            soil_friction_angle_deg=30.0,
            soil_unit_weight_kn_m3=18.0,
            concrete_unit_weight_kn_m3=25.0,
            surcharge_kpa=5.0,
        )
        self.assertEqual(res["entity_type"], "RetainingWallReport")
        stab = res["stability_analysis"]
        self.assertGreater(stab["safety_factor_overturning"], 1.5)
        self.assertGreater(stab["safety_factor_sliding"], 0.8)
        self.assertIn("vertices", res["geometry_3d"])
        self.assertIn("triangles", res["geometry_3d"])

    # ---------------------------------------------------------
    # Frente 109: Hydraulic Piping Engine (NBR 5626)
    # ---------------------------------------------------------
    def test_hydraulic_piping_engine(self):
        waypoints = [[0.0, 0.0, 1.0], [0.0, 4.0, 1.0], [0.0, 4.0, 2.5]]
        fittings = ["ELBOW_90", "TEE_PASSING"]
        res = HydraulicPipingEngine.calculate_piping_run(
            pipe_diameter_dn_mm=25.0,
            flow_rate_l_s=0.45,
            pipe_roughness_c=140.0,
            inlet_pressure_mca=18.0,
            waypoints=waypoints,
            fittings=fittings,
        )
        self.assertEqual(res["entity_type"], "HydraulicPipingReport")
        hyd = res["hydraulic_results"]
        self.assertGreater(hyd["total_head_loss_mca"], 0.0)
        self.assertLess(hyd["outlet_pressure_mca"], 18.0)
        self.assertTrue(hyd["is_compliant_nbr5626"])
        self.assertIn("vertices", res["geometry_3d"])

    # ---------------------------------------------------------
    # Frente 110: Electrical Conduit Engine (NBR 5410)
    # ---------------------------------------------------------
    def test_electrical_conduit_engine(self):
        res = ElectricalConduitEngine.calculate_conduit_run(
            conduit_nominal_dn_mm=25.0,
            circuit_current_amperes=16.0,
            cable_gauge_mm2=2.5,
            cables_count=3,
            circuit_length_m=18.0,
            voltage_v=127.0,
            power_factor=0.95,
        )
        self.assertEqual(res["entity_type"], "ElectricalConduitReport")
        self.assertLess(res["conduit_occupancy"]["occupancy_percent"], 40.0)
        self.assertTrue(res["conduit_occupancy"]["is_compliant_nbr5410"])
        self.assertLessEqual(res["voltage_drop"]["voltage_drop_percent"], 4.0)
        self.assertTrue(res["diagnostic"]["is_fully_compliant"])

    # ---------------------------------------------------------
    # Frente 111: Thermal Comfort Engine (NBR 15220)
    # ---------------------------------------------------------
    def test_thermal_comfort_engine(self):
        layers = [
            {"name": "Reboco Externo", "thickness_m": 0.02, "conductivity_w_mk": 1.15, "density_kg_m3": 2000, "specific_heat_j_kgk": 1000},
            {"name": "Tijolo Furado", "thickness_m": 0.09, "conductivity_w_mk": 0.70, "density_kg_m3": 1200, "specific_heat_j_kgk": 920},
            {"name": "Reboco Interno", "thickness_m": 0.015, "conductivity_w_mk": 1.15, "density_kg_m3": 2000, "specific_heat_j_kgk": 1000},
        ]
        res = ThermalComfortEngine.calculate_envelope_thermal_performance(
            layers=layers,
            rsi_m2_k_w=0.13,
            rse_m2_k_w=0.04,
            target_bioclimatic_zone=3,
        )
        self.assertEqual(res["entity_type"], "ThermalComfortReport")
        metrics = res["thermal_metrics"]
        self.assertGreater(metrics["transmittance_u_w_m2_k"], 0.0)
        self.assertGreater(metrics["heat_capacity_ct_kj_m2_k"], 0.0)

    # ---------------------------------------------------------
    # Frente 112: Room Acoustics Engine (NBR 10152)
    # ---------------------------------------------------------
    def test_room_acoustics_engine(self):
        res = RoomAcousticsEngine.calculate_room_reverberation(
            room_width_m=6.0,
            room_length_m=8.0,
            room_height_m=3.0,
            room_type="CLASSROOM",
        )
        self.assertEqual(res["entity_type"], "RoomAcousticsReport")
        self.assertIn("rt60_mid_seconds", res["acoustic_metrics"])
        self.assertIn("1000Hz", res["rt60_frequency_spectrum"])

    # ---------------------------------------------------------
    # Frente 113: Daylight Factor Engine (NBR 15215)
    # ---------------------------------------------------------
    def test_daylight_factor_engine(self):
        res = DaylightFactorEngine.calculate_daylight_factor(
            room_width_m=4.0,
            room_depth_m=6.0,
            room_height_m=2.80,
            window_width_m=2.0,
            window_height_m=1.20,
            window_sill_height_m=1.0,
            glass_transmittance=0.85,
            external_horizontal_lux=10000.0,
            average_internal_reflectance=0.50,
            obstruction_angle_deg=15.0,
        )
        self.assertEqual(res["entity_type"], "DaylightFactorReport")
        metrics = res["daylight_metrics"]
        self.assertGreater(metrics["average_fld_percent"], 0.5)
        self.assertGreater(metrics["average_lux"], 50.0)
        self.assertGreater(len(res["workplane_grid_points"]), 0)

    # ---------------------------------------------------------
    # Frente 114: Steel Profile Engine (NBR 8800)
    # ---------------------------------------------------------
    def test_steel_profile_engine(self):
        res = SteelProfileEngine.generate_i_beam(
            depth_d_mm=200.0,
            flange_width_bf_mm=100.0,
            web_thickness_tw_mm=6.0,
            flange_thickness_tf_mm=9.0,
            length_m=3.0,
        )
        self.assertEqual(res["entity_type"], "SteelProfileReport")
        self.assertEqual(res["profile_type"], "I_BEAM_W")
        props = res["section_properties"]
        self.assertGreater(props["area_cm2"], 20.0)
        self.assertGreater(props["ix_cm4"], 1000.0)
        self.assertIn("vertices", res["geometry_3d"])

    # ---------------------------------------------------------
    # Frente 115: BIM 5D SINAPI Cost Engine
    # ---------------------------------------------------------
    def test_bim_5d_sinapi_cost_engine(self):
        elements = [
            {"code": "93358", "description": "Concreto Fck 25 MPa", "category": "ESTRUTURA", "unit": "M3", "quantity": 15.0, "unit_price": 430.0},
            {"code": "92778", "description": "Armadura CA-50 10mm", "category": "ESTRUTURA", "unit": "KG", "quantity": 1200.0, "unit_price": 13.50},
            {"code": "89170", "description": "Alvenaria bloco cerâmico", "category": "ALVENARIA", "unit": "M2", "quantity": 110.0, "unit_price": 72.0},
        ]
        res = Bim5dSinapiCostEngine.calculate_5d_budget(
            elements=elements,
            bdi_percent=24.50,
            social_charges_percent=84.0,
        )
        self.assertEqual(res["entity_type"], "Bim5dSinapiReport")
        summary = res["financial_summary"]
        self.assertGreater(summary["total_direct_cost_brl"], 30000.0)
        self.assertGreater(summary["total_budget_with_bdi_brl"], summary["total_direct_cost_brl"])
        self.assertEqual(res["items_count"], 3)
        self.assertIn("class_a_items_count", res["abc_classification_summary"])

    # ---------------------------------------------------------
    # Controller Async Handlers (Frentes 106 a 115)
    # ---------------------------------------------------------
    def test_async_controllers_frentes_106_a_115(self):
        async def run_controllers():
            # 106
            req106 = RigidBodyPhysicsRequest(
                bodies=[{"id": "b1", "name": "Box", "mass_kg": 1.0, "initial_pos": [0, 0, 2], "dimensions": [1, 1, 1]}],
                total_time_s=0.5,
            )
            resp106 = await self.controller.simulate_rigid_body_physics(req106)
            self.assertEqual(resp106.entity_type, "RigidBodyPhysicsReport")

            # 107
            req107 = Slicing3dPrintRequest(
                vertices=[[0, 0, 0], [10, 0, 0], [0, 10, 0]],
                triangles=[[0, 1, 2]],
                layer_height_mm=0.2,
            )
            resp107 = await self.controller.slice_3d_print_fdm(req107)
            self.assertEqual(resp107.entity_type, "FdmSlicingReport")

            # 108
            req108 = RetainingWallRequest(wall_height_m=3.0)
            resp108 = await self.controller.calculate_retaining_wall_stability(req108)
            self.assertEqual(resp108.entity_type, "RetainingWallReport")

            # 109
            req109 = HydraulicPipingRequest(pipe_diameter_dn_mm=25.0, flow_rate_l_s=0.4)
            resp109 = await self.controller.calculate_hydraulic_piping(req109)
            self.assertEqual(resp109.entity_type, "HydraulicPipingReport")

            # 110
            req110 = ElectricalConduitRequest(conduit_nominal_dn_mm=25.0, circuit_current_amperes=16.0)
            resp110 = await self.controller.calculate_electrical_conduit(req110)
            self.assertEqual(resp110.entity_type, "ElectricalConduitReport")

            # 111
            req111 = ThermalComfortRequest()
            resp111 = await self.controller.calculate_thermal_comfort(req111)
            self.assertEqual(resp111.entity_type, "ThermalComfortReport")

            # 112
            req112 = RoomAcousticsRequest(room_width_m=5.0, room_length_m=6.0, room_height_m=2.8)
            resp112 = await self.controller.calculate_room_acoustics(req112)
            self.assertEqual(resp112.entity_type, "RoomAcousticsReport")

            # 113
            req113 = DaylightFactorRequest(room_width_m=4.0, room_depth_m=5.0)
            resp113 = await self.controller.calculate_daylight_factor(req113)
            self.assertEqual(resp113.entity_type, "DaylightFactorReport")

            # 114
            req114 = SteelProfileRequest(depth_d_mm=200.0, flange_width_bf_mm=100.0)
            resp114 = await self.controller.generate_steel_profile(req114)
            self.assertEqual(resp114.entity_type, "SteelProfileReport")

            # 115
            req115 = Bim5dSinapiCostRequest(elements=[{"code": "1", "description": "T", "unit": "UN", "quantity": 10.0, "unit_price": 50.0}])
            resp115 = await self.controller.calculate_bim_5d_sinapi_budget(req115)
            self.assertEqual(resp115.entity_type, "Bim5dSinapiReport")

        asyncio.run(run_controllers())


if __name__ == "__main__":
    unittest.main()
