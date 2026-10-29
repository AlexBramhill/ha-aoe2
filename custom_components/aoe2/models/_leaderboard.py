from enum import StrEnum


class Leaderboard(StrEnum):
    RM_1V1 = "rm_1v1"
    RM_TEAM = "rm_team"
    EW_1V1 = "ew_1v1"
    EW_TEAM = "ew_team"
    QP_RM_1V1 = "qp_rm_1v1"
    QP_RM_TEAM = "qp_rm_team"
    DM_1V1 = "dm_1v1"
    DM_TEAM = "dm_team"
    UNRANKED = "unranked"
    RM_1V1_CONSOLE = "rm_1v1_console"
    RM_TEAM_CONSOLE = "rm_team_console"
    EW_1V1_CONSOLE = "ew_1v1_console"
    EW_TEAM_CONSOLE = "ew_team_console"
    OTHER = "other"
