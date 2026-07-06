
class AgentSkill:

    name="memory_agent"

    def run(self,input):
        return {
          "agent":self.name,
          "result":"completed",
          "input":input
        }
