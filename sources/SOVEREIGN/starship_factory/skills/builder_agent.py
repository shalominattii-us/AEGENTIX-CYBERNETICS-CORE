
class AgentSkill:

    name="builder_agent"

    def run(self,input):
        return {
          "agent":self.name,
          "result":"completed",
          "input":input
        }
