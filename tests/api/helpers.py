import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"


@dataclass(frozen=True)
class RecordedPlayer:
    name: str
    profile_id: int

    def read_fixture(self, filename: str) -> Any:
        return json.loads((FIXTURES / self.name / filename).read_text())


VIPER = RecordedPlayer(name="viper", profile_id=196240)
VIPER_MATCH_IDS = [515058973, 515058199, 515051663, 515046591, 515041058, 514828647]
VIPER_LOST_UNRANKED_MATCH_ID = 515058973
VIPER_WON_RANKED_MATCH_ID = 514828647

TEAM_PLAYER = RecordedPlayer(name="team_player", profile_id=9100001)
RECORDED_PLAYERS = [VIPER, TEAM_PLAYER]
