$log = 'C:\Aegentix\ollama-import.log'
$ollama = 'C:\Users\eagle\AppData\Local\Programs\Ollama\ollama.exe'

"=== IMPORT START $(Get-Date) ===" | Set-Content $log

# Tiny model
Set-Content 'C:\Aegentix\Modelfile-tiny' "FROM C:\Aegentix\models\tinyllama-1.1b.Q4_K_M.gguf`n"
"--- creating cybercore-tiny from tinyllama-1.1b ---" | Add-Content $log
& $ollama create cybercore-tiny -f 'C:\Aegentix\Modelfile-tiny' *>> $log

# Core model
Set-Content 'C:\Aegentix\Modelfile-core' "FROM C:\Aegentix\models\mistral-7b.Q4_K_M.gguf`n"
"--- creating cybercore-core from mistral-7b ---" | Add-Content $log
& $ollama create cybercore-core -f 'C:\Aegentix\Modelfile-core' *>> $log

"--- IMPORT DONE $(Get-Date) ---" | Add-Content $log
& $ollama list *>> $log
