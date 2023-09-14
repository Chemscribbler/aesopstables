import aesops.business_logic.match as m_logic
from aesops.distributed_logic.player_dist import update_score, update_sos_esos
import aesops.business_logic.players as p_logic
from data_models.tournaments import Tournament
import time

def wait_for_tasks(task_list :list):
    done = False
    loopcnt = 0
    while not done:
        pdgCount = 0
        loopcnt += 1
        for task in task_list:
            pdgCount += 0 if task.state == "SUCCESS" else 1
        done = pdgCount == 0
        print(f'----- Pending count {pdgCount} - {loopcnt} -----')
        if not done:
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
