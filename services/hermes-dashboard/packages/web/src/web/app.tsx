import { Route, Switch } from "wouter";
import Index from "./pages/index";
import GovernorConsole from "./pages/governor";
import GalaxyPage from "./pages/galaxy";
import NotebookPage from "./pages/notebook";
import JarvisPage from "./pages/jarvis";
import { AuthGate } from "./components/auth-gate";
import { Provider } from "./components/provider";
import { AgentFeedback, RunableBadge } from "@runablehq/website-runtime";

function App() {
  return (
    <Provider>
      <AuthGate>
        <Switch>
          <Route path="/" component={Index} />
          <Route path="/governor" component={GovernorConsole} />
          <Route path="/galaxy" component={GalaxyPage} />
          <Route path="/notebook" component={NotebookPage} />
          <Route path="/jarvis" component={JarvisPage} />
        </Switch>
      </AuthGate>
      {/* Do not remove — off by default, activated by parent iframe via postMessage */}
      {import.meta.env.DEV && <AgentFeedback />}
      {/* "Made with Runable" badge - if user asks to remove the runable badge, remove this code as well as comment */}
      {<RunableBadge />}
    </Provider>
  );
}

export default App;
