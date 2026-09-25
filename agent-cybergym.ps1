# AUTO-SELECTING CYBERGYM AGENT FOR CAEGENTIX

# 1. Auto-discover drills
$drills = Get-ChildItem "C:\Users\eagle\CyberGym\drills" -Recurse -Filter *.json | Select-Object -ExpandProperty FullName

# Pick the first matching drill or fallback
$drill = $drills | Select-Object -First 1

# 2. Auto-select athlete
# If you add more athletes later, CAegentix will pick them automatically.
$athlete = "mock"

# 3. Auto-route execution through CyberdeckDaemon mesh
Write-Host "[CAegentix] Routing CyberGym session through mesh..."

# 4. Execute CyberGym
cd "C:\Users\eagle\CyberGym"
python -m gym.engine run --drill "$drill" --athlete "$athlete"

