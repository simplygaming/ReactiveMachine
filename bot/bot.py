from sc2.bot_ai import BotAI
from sc2.data import Race, Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Unit

class MyBot(BotAI):
    NAME: str = "ReactiveMachine"
    RACE: Race = Race.Zerg

    def __init__(self):
        super().__init__()
        self.build_order_complete = False
        self.zergling_attack_threshold = 20

    async def on_start(self, iteration: int) -> None:
        print("Game started")

    async def on_step(self, iteration: int) -> None:
        # Ensure workers are mining
        await self.distribute_workers()

        # Execute build order
        if not self.build_order_complete:
            await self.execute_build_order()

        # Train units
        await self.train_units()

        # Attack logic
        await self.attack_enemy()

    async def on_end(self, game_result: Result) -> None:
        print(f"Game ended with result: {game_result}")

    async def on_building_construction_complete(self, unit: Unit) -> None:
        print(f"Building construction complete: {unit.name}")

    async def on_unit_created(self, unit: Unit) -> None:
        print(f"Unit created: {unit.name}")

    async def on_unit_destroyed(self, unit_tag: int) -> None:
        print(f"Unit destroyed: {unit_tag}")

    async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float) -> None:
        print(f"{unit.name} took {amount_damage_taken} damage")

    async def execute_build_order(self):
        """Executes the early game build order."""
        if self.townhalls.exists:
            hatchery = self.townhalls.first

            # Build Overlord if supply is low
            if self.supply_left < 2 and self.can_afford(UnitTypeId.OVERLORD):
                await self.train(UnitTypeId.OVERLORD)

            # Build Spawning Pool
            if not self.structures(UnitTypeId.SPAWNINGPOOL) and self.can_afford(UnitTypeId.SPAWNINGPOOL):
                await self.build(UnitTypeId.SPAWNINGPOOL, near=hatchery)

            # Expand to a new base
            if self.townhalls.amount < 2 and self.can_afford(UnitTypeId.HATCHERY):
                target_expansion = await self.get_next_expansion()
                if target_expansion:
                    await self.build(UnitTypeId.HATCHERY, target_expansion)

            # Build Extractor
            if self.gas_buildings.amount < 1 and self.can_afford(UnitTypeId.EXTRACTOR):
                for geyser in self.vespene_geyser.closer_than(15, hatchery):
                    if await self.can_place(UnitTypeId.EXTRACTOR, geyser.position):
                        await self.build(UnitTypeId.EXTRACTOR, geyser)
                        break

            # Check if build order is complete
            if self.structures(UnitTypeId.SPAWNINGPOOL).ready and self.townhalls.amount >= 2:
                self.build_order_complete = True

    async def train_units(self):
        """Handles unit production."""
        for hatchery in self.townhalls.ready.idle:
            # Train Zerglings if Spawning Pool exists
            if self.structures(UnitTypeId.SPAWNINGPOOL).ready and self.can_afford(UnitTypeId.ZERGLING):
                await hatchery.train(UnitTypeId.ZERGLING)

    async def attack_enemy(self):
        """Handles the attack logic."""
        if self.units(UnitTypeId.ZERGLING).amount > self.zergling_attack_threshold:
            for zergling in self.units(UnitTypeId.ZERGLING).idle:
                # Attack closest enemy structure or unit
                if self.enemy_structures:
                    target = self.enemy_structures.closest_to(zergling)
                elif self.enemy_units:
                    target = self.enemy_units.closest_to(zergling)
                else:
                    target = self.enemy_start_locations[0]
                zergling.attack(target)
