import aesops.business_logic.match as m_logic
from aesops.distributed_logic.player_dist import update_score, update_sos_esos
from data_models.tournaments import Tournament
import time

def wait_for_tasks(task_list :list):
    while len(task_list) != 0:
        task_list = [x for x in task_list if x.state != "SUCCESS"]
        time.sleep(0.25)

def conclude_round_distributed(tournament: Tournament):
    for match in tournament.active_matches:
        m_logic.conclude(match)
    task_list = []
    for player in tournament.players:
        task_list.append(update_score.delay(player.id))

    wait_for_tasks(task_list)

    task_list.clear()
    for player in tournament.players:
        task_list.append(update_sos_esos.delay(player.id))

    wait_for_tasks(task_list)
