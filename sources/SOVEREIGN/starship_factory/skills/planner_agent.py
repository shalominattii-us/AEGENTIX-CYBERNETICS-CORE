
class AgentSkill:

    name="planner_agent"

    def run(self,input):
        return {
          "agent":self.name,
          "result":"completed",
          "input":input
        }
