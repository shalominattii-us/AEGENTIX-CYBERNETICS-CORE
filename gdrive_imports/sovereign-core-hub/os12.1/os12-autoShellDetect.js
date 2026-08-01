// os12-autoShellDetect.js
function detectShell() {
  const comspec = process.env.ComSpec || '';
  const isCmd = comspec.toLowerCase().includes('cmd.exe');
  const shellInfo = { comspec, isCmd, argv0: process.argv[0], platform: process.platform };
  console.log('[OS12.1][SHELL]', JSON.stringify(shellInfo));
  return shellInfo;
}
module.exports = { detectShell };
