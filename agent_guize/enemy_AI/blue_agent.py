from agent_guize.enemy_AI.related_pkgs import *
from agent_guize.enemy_AI.base_agent import BaseAgent
import agent_guize.enemy_AI.constant as const
from agent_guize.enemy_AI.unit_controler import name2controler, PatrolControler
import agent_guize.enemy_AI.utils as utils
from agent_guize.enemy_AI.unit_agent import UnitAgent
init_lla = const.blue_initial_lla
init_controler = const.blue_init_controler
aux_units = const.blue_aux_unit
watch_target_ids = const.blue_watch_target_ids

class BlueAgent(BaseAgent):
  def __init__(self):
    super().__init__()
    self.detected_state={}

  def get_detect_info_gai(self, status):
        # LJD不会探测
        filtered_status = self.__status_filter(status)
        unitIDList = list(filtered_status.keys())

        detectinfo = dict()
        for unit in unitIDList:
            try:
                for i in range(len(status[unit]['DetectorState'])):
                    for j in range(len(status[unit]['DetectorState'][i]['DetectedState'])):
                        detectinfo[status[unit]['DetectorState'][i]['DetectedState'][j]['targetID']] = \
                            status[unit]['DetectorState'][i]['DetectedState'][j]
            except:
                pass
        return detectinfo

  def __status_filter(self, status):
        # 这个用于滤除奇怪的东西.
        status_new = {}
        for attacker_ID in status:
            # 卫星、飞机,和bmc3是不吃这个指令的，还是区分一下以防后面报错在
            # 飞机还是应该吃这个指令
            flag = ("bmc" in attacker_ID) or ("satallite" in attacker_ID) or ("DespoilControlPos" in attacker_ID)  # \
            # or ("ShipboardCombat_plane" in attacker_ID) \
            # or ("missile_truck" in attacker_ID)
            if not flag:
                status_new[attacker_ID] = status[attacker_ID]
        return status_new

  def deploy0(self, ids):
    super().deploy(ids)
    for units in self.units.values():
      for i, unit in enumerate(units):
        if i == 0 and unit.name == 'tank':
          unit.deploy(const.target_lla)
        elif i == 1 and unit.name == 'tank':
          unit.deploy((2.60, 39.7198, 0))
        else:
          unit.deploy(init_lla[unit.id])
    return self.cmd

  def deploy1(self, ids):
    super().deploy(ids)
    for units in self.units.values():
      for i, unit in enumerate(units):
        # if unit.id == 'WheeledCmobatTruck_ZB200_0' or unit.id == 'Infantry2':
        #   unit.deploy((2.60, 39.71969, 0))
        # else:
        unit.deploy(init_lla[unit.id])
        if unit.id in init_controler.keys():
          (controler_name, *args) = init_controler[unit.id]
          aux_unit = aux_units.get(unit.id)
          if aux_unit is not None:
            aux_unit = self.units_id[aux_unit]
          controler = name2controler[controler_name](
            unit, *args, aux_unit=aux_unit
          )
          unit.controler = controler
    return self.cmd

  def deploy(self, ids):  # only deploy units
    for id in ids:
      for name, aux in const.name2aux.items():
        if aux in id:
          unit = UnitAgent(name, id, self.cmd)
          unit.deploy(init_lla[id])
          break
    return self.cmd
  
  def step(self, state: dict):

    self.detected_state = self.get_detect_info_gai(state)

    if self.step_num == 0:  # init controler state
      # super().deploy(list(state.keys()), init_lla, {}, aux_units)  # for test
      super().deploy(list(state.keys()), init_lla, init_controler, aux_units)
          
    self.update_state(state)
    # print("Blue detection:", self.detection)

    ### Control unit by the controler ###
    for unit in self.units_flatten:
      if unit.controler is not None:
        unit.controler.step(self.detection)

    ### Watch target: we need one unit to stay in target ###
    watch_target = False
    for unit in self.units_flatten:
      if unit.controler is None or not unit.alive: continue
      if unit.controler.mode == 'patrol' and unit.controler.name == 'target':
        watch_target = True
    if not watch_target:
      for id in watch_target_ids:
        unit = self.units_id[id]
        if unit.controler is None or not unit.alive: continue
        unit.controler = PatrolControler(
          unit=unit,
          point='target',
          aux_unit=unit.controler.aux_unit,
        )
        break

    # for unit in self.units_flatten:
    #   if unit.controler is not None:
    #     if not unit.alive and unit.name != 'infantry':
    #       print(unit.id, "has been destoried!")
    #     else:
    #       print(unit.id, unit.controler.mode, unit.controler.name if unit.controler.name else unit.controler.target_id)
    #   else:
    #     print(unit.id, unit.controler)
    # for unit in self.units['tank']:
    #   unit._DEBUG()
    
    # self.units['plane'][0]._DEBUG()
    # print("target distance:", utils.get_distance_lla(self.units_id['missile_truck3'].position, const.target_lla))
    # self.units_id['Infantry2']._DEBUG()
    return self.cmd
    